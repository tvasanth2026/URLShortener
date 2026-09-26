"""Architect / Design Agent and Codebase Reasoning Agent (brownfield)."""
from __future__ import annotations

from core.models import TaskContext, TaskSpec
from agents.base import Agent


class DesignAgent(Agent):
    name = "DesignAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        design_key = spec.id.lower().replace("-", "_")
        design: dict

        if "data" in spec.description.lower() or spec.id == "DES-1":
            design = {
                "entity": "UrlMapping",
                "fields": ["id (auto-generated PK)", "shortCode (Base62 of id, unique)",
                           "longUrl (TEXT)", "createdAt (timestamp)"],
                "keyStrategy": "JPA IDENTITY id -> Base62 encode -> shortCode",
            }
        elif "api contract" in spec.description.lower() or spec.id == "DES-2":
            design = {
                "endpoints": [
                    "POST /api/v1/urls -> create short URL",
                    "GET /api/v1/urls/{shortCode} -> resolve original URL",
                ],
            }
        elif "code gen" in spec.description.lower() or spec.id == "DES-3":
            design = {"strategy": "Base62 encode auto-generated numeric id; unique DB constraint on shortCode"}
        elif "caching" in spec.description.lower() or spec.id == "DES-4":
            design = {"cache": "Optional Redis cache-aside on redirect lookup path"}
        elif "rate" in spec.description.lower() or spec.id == "DES-5":
            design = {"rateLimiting": "Fixed-window limiter on POST /api/v1/urls"}
        else:
            design = {"note": f"Design decision recorded for {spec.id}: {spec.description}"}

        context.set_artifact(design_key, design)
        return design


class CodebaseReasoningAgent(Agent):
    """Used for brownfield scenarios: identifies impacted modules/APIs/data flows."""

    name = "CodebaseReasoningAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        impact = {
            "impactedModules": ["UrlController", "UrlShortenerService"],
            "impactedApis": ["POST /api/v1/urls"],
            "dataFlows": ["Controller -> Service -> Repository -> PostgreSQL"],
            "notes": "Enhancement scoped to the shorten endpoint; redirect/analytics "
                     "endpoints unaffected.",
        }
        context.set_artifact("codebase_impact", impact)
        return impact
