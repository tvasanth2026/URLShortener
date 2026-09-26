"""Base agent interface. Every stage agent implements `execute`, receiving and
returning a shared TaskContext so cross-stage context and lineage is preserved.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from core.models import TaskContext, TaskSpec


class Agent(ABC):
    name: str = "BaseAgent"

    @abstractmethod
    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        """Run this agent's work for the given task spec.

        Must return a JSON-serializable dict result, which the orchestrator
        stores under `context.artifacts[spec.id]`.
        Raise an exception to signal failure (the orchestrator handles
        retry/rollback/safe-stop policy).
        """
        raise NotImplementedError
