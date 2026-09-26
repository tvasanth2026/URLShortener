"""Developer Agents (Controller / Service / Repository) — Implementation stage.

These agents represent code-generation work. In this prototype they record a
structured summary of the generated artifact (the actual Spring Boot source
lives under agentic-orchestrator/service/) rather than re-emitting source
code, since the artifact is the production code tree itself.
"""
from __future__ import annotations

from core.models import TaskContext, TaskSpec
from agents.base import Agent


class DevAgent(Agent):
    name = "DevAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        result = {
            "taskId": spec.id,
            "generatedArtifact": self._artifact_for(spec.id),
            "status": "IMPLEMENTED",
        }
        context.set_artifact(spec.id.lower().replace("-", "_"), result)
        return result

    def _artifact_for(self, task_id: str) -> str:
        mapping = {
            "IMPL-1": "service/.../entity/UrlMapping.java, repository/UrlMappingRepository.java",
            "IMPL-2": "service/.../service/UrlShortenerService.java (create/dedup/resolve)",
            "IMPL-3": "service/.../service/UrlShortenerService.java (analytics hooks)",
            "IMPL-4": "service/.../controller/UrlController.java",
            "IMPL-5": "service/.../config/CacheConfig.java (Redis, optional)",
            "IMPL-6": "service/.../config/RateLimitFilter.java",
            "IMPL-7": "service/.../exception/GlobalExceptionHandler.java",
        }
        return mapping.get(task_id, f"Generated code for {task_id}")
