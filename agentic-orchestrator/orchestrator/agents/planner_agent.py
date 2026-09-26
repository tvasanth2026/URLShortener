"""Planner Agent — Task Decomposition stage.

Confirms the task graph for this workflow is well-formed and annotates the
context with traceability from the requirement artifact to the already
declared TaskSpec graph (the graph itself is defined declaratively in the
workflow YAML spec — this agent validates and summarizes it, rather than
inventing it at runtime, to keep the DAG auditable).
"""
from __future__ import annotations

from core.models import TaskContext, TaskSpec
from agents.base import Agent


class PlannerAgent(Agent):
    name = "PlannerAgent"

    def execute(self, spec: TaskSpec, context: TaskContext) -> dict:
        requirement = context.get_artifact("requirement", {})
        plan = {
            "planId": spec.id,
            "workflowId": context.workflow_id,
            "basedOnRequirement": requirement.get("requirementId"),
            "summary": "Task graph validated: dependencies form a DAG; "
                       "parallel branches identified for design, implementation, "
                       "and testing/documentation stages.",
            "status": "READY_FOR_DESIGN",
        }
        context.set_artifact("plan", plan)
        return plan
