"""Test Agent, Documentation Agent, Risk & Validation Agent, Release Agent."""
from __future__ import annotations

from core.models import TaskContext, TaskSpec
from agents.base import Agent


class TestAgent(Agent):
    name = "TestAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        result = {
            "taskId": spec.id,
            "testsRun": self._tests_for(spec.id),
            "passed": True,
        }
        context.set_artifact(spec.id.lower().replace("-", "_"), result)
        return result

    def _tests_for(self, task_id: str) -> list:
        mapping = {
            "TEST-1": ["dedup", "expiry check", "Base62 generation"],
            "TEST-2": ["POST /urls happy path", "GET /urls/{code} happy path", "4xx error paths"],
            "TEST-3": ["concurrent code generation collision test"],
            "TEST-4": ["rate-limit enforcement", "cache hit/miss behavior"],
        }
        return mapping.get(task_id, [f"tests for {task_id}"])


class DocumentationAgent(Agent):
    name = "DocumentationAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        result = {
            "taskId": spec.id,
            "artifact": "OpenAPI spec + README.md" if spec.id == "DOC-1" else "README.md setup instructions",
        }
        context.set_artifact(spec.id.lower().replace("-", "_"), result)
        return result


class RiskValidationAgent(Agent):
    name = "RiskValidationAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        result = {
            "risks": [
                "Short-code collision under concurrency",
                "Cache/DB inconsistency on redirect path",
                "Rate-limit misconfiguration blocking legitimate traffic",
            ],
            "tradeoffs": [
                "Relational DB chosen over NoSQL for consistency",
                "No auth/ownership in v1",
            ],
            "validationPlan": [
                "Load test at 2x expected traffic",
                "Collision test on Base62 generation",
                "Security scan for injection/auth bypass",
            ],
        }
        context.set_artifact("risk_validation", result)
        return result


class ReleaseAgent(Agent):
    name = "ReleaseAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        result = {
            "releaseNotes": "URL Shortener v1.0.0: shorten, redirect, analytics endpoints.",
            "rollbackPlan": "Revert to previous container image; DB migrations are additive-only.",
            "goNoGo": "GO",
        }
        context.set_artifact("release", result)
        return result
