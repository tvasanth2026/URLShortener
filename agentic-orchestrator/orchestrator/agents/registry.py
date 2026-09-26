"""Agent registry: maps `owningAgent` names used in workflow YAML specs to
concrete Agent implementations.
"""
from __future__ import annotations

from typing import Dict

from .base import Agent
from .design_agent import CodebaseReasoningAgent, DesignAgent
from .dev_agent import DevAgent
from .planner_agent import PlannerAgent
from .requirement_agent import RequirementAgent
from .test_doc_release_agents import (
    DocumentationAgent,
    ReleaseAgent,
    RiskValidationAgent,
    TestAgent,
)


def build_default_registry() -> Dict[str, Agent]:
    return {
        "RequirementAgent": RequirementAgent(),
        "PlannerAgent": PlannerAgent(),
        "ArchitectAgent": DesignAgent(),
        "CodebaseReasoningAgent": CodebaseReasoningAgent(),
        "DevAgent-Repository": DevAgent(),
        "DevAgent-Service": DevAgent(),
        "DevAgent-Controller": DevAgent(),
        "TestAgent": TestAgent(),
        "DocumentationAgent": DocumentationAgent(),
        "RiskValidationAgent": RiskValidationAgent(),
        "ReleaseAgent": ReleaseAgent(),
    }
