"""Governance layer: approvals, retry/rollback/safe-stop policy, and guardrails.

This module enforces controlled autonomy: agents may execute multi-step work,
but high-impact actions require an explicit human decision, and failures are
bounded (retry limits) with safe-stop as the last resort.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .models import Decision, TaskSpec, utcnow


@dataclass
class ApprovalRequest:
    task_id: str
    description: str
    context_summary: str
    status: str = "PENDING"  # PENDING | APPROVED | REJECTED


class PolicyEngine:
    """Central policy authority consulted by the orchestrator before/after each stage."""

    def __init__(self, approval_callback: Optional[Callable[[ApprovalRequest], bool]] = None):
        # approval_callback: given a request, return True to approve, False to reject.
        # Defaults to auto-approve (useful for unattended demo runs); production
        # usage should inject a real human-in-the-loop callback (CLI prompt, UI, ticket system).
        self._approval_callback = approval_callback or self._default_auto_approve
        self.pending_approvals: Dict[str, ApprovalRequest] = {}
        self.decisions: List[Decision] = []

    @staticmethod
    def _default_auto_approve(request: ApprovalRequest) -> bool:
        return True

    def request_approval(self, spec: TaskSpec, context_summary: str) -> Decision:
        request = ApprovalRequest(
            task_id=spec.id,
            description=spec.description,
            context_summary=context_summary,
        )
        self.pending_approvals[spec.id] = request

        approved = self._approval_callback(request)
        request.status = "APPROVED" if approved else "REJECTED"

        decision = Decision(
            task_id=spec.id,
            decision="approved" if approved else "rejected",
            rationale=context_summary,
            made_by="human",
            timestamp=utcnow(),
        )
        self.decisions.append(decision)
        return decision

    # --- Guardrails -------------------------------------------------
    def check_security_guardrails(self, task_id: str, artifact: dict) -> Optional[str]:
        """Return a violation message, or None if the artifact passes guardrails."""
        text_blob = str(artifact)
        forbidden_markers = ["BEGIN RSA PRIVATE KEY", "password=hardcoded", "AKIA"]
        for marker in forbidden_markers:
            if marker in text_blob:
                return f"Guardrail violation in {task_id}: forbidden pattern '{marker}' detected"
        return None

    # --- Retry / rollback / safe-stop --------------------------------
    def can_retry(self, attempts: int, max_retries: int) -> bool:
        return attempts < max_retries

    def should_rollback(self, task_id: str, error: Exception) -> bool:
        # Any error that survives all retries triggers rollback by default.
        return True

    def should_safe_stop(self, task_id: str, error: Exception) -> bool:
        # High-impact stages (release) trigger a full safe-stop rather than
        # silently rolling back and continuing.
        return "REL-" in task_id
