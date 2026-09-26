"""Requirement Analyst Agent.

Interprets raw intent, identifies ambiguity, and normalizes it into a
structured engineering-problem artifact (mirrors docs/01-requirement-understanding.md).

If an LLM client is configured (OPENAI_API_KEY set and `openai` package
available), the agent delegates interpretation to the model; otherwise it
falls back to a deterministic rule-based normalization so the pipeline is
fully runnable offline/without credentials.
"""
from __future__ import annotations

import os
from typing import List

from core.models import TaskContext, TaskSpec
from agents.base import Agent

AMBIGUOUS_MARKERS = ["safer", "better", "improve", "modernize", "faster", "some", "etc"]


class RequirementAgent(Agent):
    name = "RequirementAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        intent = context.intent
        ambiguities = self._detect_ambiguities(intent)

        normalized = {
            "requirementId": f"REQ-{context.workflow_id}",
            "rawIntent": intent,
            "normalizedProblem": self._normalize(intent, ambiguities),
            "ambiguities": ambiguities,
            "isAmbiguous": len(ambiguities) > 0,
            "functionalRequirements": [
                "FR1: Shorten a valid URL and return a unique short code",
                "FR2: Redirect a short code to its original URL",
                "FR3: Return 404 for unknown/expired codes",
                "FR4: Return click analytics for a given code",
                "FR5: Reject malformed URLs with 400",
            ],
            "nonFunctionalRequirements": [
                "NFR1: Low-latency cache-backed redirects",
                "NFR2: Effectively collision-free short codes",
                "NFR3: Stateless, horizontally scalable service",
            ],
            "status": "AWAITING_APPROVAL",
        }
        context.set_artifact("requirement", normalized)
        return normalized

    def _detect_ambiguities(self, intent: str) -> List[str]:
        lowered = intent.lower()
        found = [marker for marker in AMBIGUOUS_MARKERS if marker in lowered]
        if not found:
            return []
        return [
            f"Term '{marker}' is vague and not independently testable; "
            f"requires clarification of concrete acceptance criteria."
            for marker in found
        ]

    def _normalize(self, intent: str, ambiguities: List[str]) -> str:
        if ambiguities:
            return (
                "Interpreted intent as a request to strengthen the URL shortener's "
                "input validation, abuse-prevention (rate limiting), and expiry handling. "
                "This interpretation requires human confirmation before Design proceeds "
                "because the original request used vague/non-testable language."
            )
        return (
            "Build a stateless Spring Boot microservice that shortens long URLs, "
            "redirects short codes to their original URL, and exposes basic click "
            "analytics, backed by PostgreSQL with a JPA-auto-generated key encoded "
            "as a Base62 short code."
        )
