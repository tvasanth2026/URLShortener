"""Core data models shared across the orchestrator and all agents.

These models are intentionally framework-agnostic (plain dataclasses) so they
can be serialized to/from JSON for audit logging, re-planning, and
cross-stage context sharing.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    READY = "READY"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    DONE = "DONE"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TaskSpec:
    """Declarative definition of a single node in the SDLC dependency graph."""

    id: str
    stage: str
    description: str
    owning_agent: str
    depends_on: List[str] = field(default_factory=list)
    requires_approval: bool = False
    traces_to: List[str] = field(default_factory=list)
    max_retries: int = 3


@dataclass
class TaskState:
    """Mutable runtime state for a task, tracked by the orchestrator."""

    spec: TaskSpec
    status: TaskStatus = TaskStatus.PENDING
    attempts: int = 0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    finished_at: Optional[str] = None


@dataclass
class Decision:
    """A recorded decision (human or automated) that affects workflow lineage."""

    task_id: str
    decision: str  # e.g. "approved", "rejected", "auto-resolved"
    rationale: str
    made_by: str  # "human" or agent name
    timestamp: str = field(default_factory=utcnow)


@dataclass
class AuditEvent:
    event_type: str  # SUCCESS | RETRY | ROLLBACK | APPROVAL | FAILURE | REPLAN
    task_id: str
    detail: str
    timestamp: str = field(default_factory=utcnow)


@dataclass
class TaskContext:
    """Shared, evolving context passed between agents across the whole workflow.

    Acts as the single source of truth for cross-stage artifacts (requirement
    artifact, design artifact, code artifacts, test results, etc.) and
    decision lineage.
    """

    workflow_id: str
    intent: str
    artifacts: Dict[str, Any] = field(default_factory=dict)
    decisions: List[Decision] = field(default_factory=list)

    def set_artifact(self, key: str, value: Any) -> None:
        self.artifacts[key] = value

    def get_artifact(self, key: str, default: Any = None) -> Any:
        return self.artifacts.get(key, default)

    def record_decision(self, decision: Decision) -> None:
        self.decisions.append(decision)
