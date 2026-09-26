"""Orchestrator Agent — the controller loop.

Coordinates the full SDLC lifecycle across the dependency graph:
non-linear, stateful execution with governance (approvals, retries,
rollback, safe-stop, guardrails, audit, metrics, re-planning).
"""
from __future__ import annotations

from typing import Dict

from .audit import AuditLog, MetricsRecorder
from .graph import WorkflowGraph
from .models import TaskContext, TaskStatus
from .policy import PolicyEngine
from agents.base import Agent


class SafeStopException(Exception):
    """Raised to halt the entire workflow when a high-impact failure occurs."""


class Orchestrator:
    def __init__(
        self,
        graph: WorkflowGraph,
        agents: Dict[str, Agent],
        policy: PolicyEngine,
        audit: AuditLog,
        metrics: MetricsRecorder,
    ):
        self.graph = graph
        self.agents = agents
        self.policy = policy
        self.audit = audit
        self.metrics = metrics

    def run(self, context: TaskContext) -> TaskContext:
        while not self.graph.is_complete():
            ready = self.graph.ready_tasks()
            if not ready:
                if self.graph.has_unresolved_failures():
                    raise SafeStopException(
                        "Workflow halted: unresolved failures and no ready tasks remain."
                    )
                raise SafeStopException("Workflow stalled: no ready tasks and not complete.")

            # Tasks in `ready` share no interdependency (else they wouldn't
            # both be ready), so this loop represents genuine parallel
            # execution opportunities. A real implementation could dispatch
            # these concurrently (threads/async); executed sequentially here
            # for deterministic, auditable demo output.
            for task_id in ready:
                self._run_task(task_id, context)

        return context

    def _run_task(self, task_id: str, context: TaskContext) -> None:
        state = self.graph.states[task_id]
        spec = state.spec
        state.status = TaskStatus.RUNNING
        self.metrics.task_started(task_id)

        if spec.requires_approval:
            summary = f"{spec.stage}: {spec.description}"
            decision = self.policy.request_approval(spec, summary)
            context.record_decision(decision)
            if decision.decision != "approved":
                state.status = TaskStatus.FAILED
                self.audit.log("FAILURE", task_id, f"Approval rejected: {summary}")
                self.metrics.task_failed(task_id)
                raise SafeStopException(f"Task {task_id} rejected by human approver; halting.")
            self.audit.log("APPROVAL", task_id, summary)

        agent = self.agents.get(spec.owning_agent)
        if agent is None:
            raise ValueError(f"No agent registered for '{spec.owning_agent}' (task {task_id})")

        while True:
            state.attempts += 1
            try:
                result = agent.execute(spec, context)

                violation = self.policy.check_security_guardrails(task_id, result)
                if violation:
                    raise RuntimeError(violation)

                state.result = result
                state.status = TaskStatus.DONE
                self.audit.log("SUCCESS", task_id, f"{spec.owning_agent} completed {spec.id}")
                self.metrics.task_succeeded(task_id)
                if state.attempts > 1:
                    self.metrics.task_recovered(task_id)
                return

            except Exception as exc:  # noqa: BLE001 - orchestrator must catch all agent errors
                self.audit.log("FAILURE", task_id, str(exc))
                self.metrics.task_failed(task_id)

                if self.policy.can_retry(state.attempts, spec.max_retries):
                    self.metrics.task_retried(task_id)
                    self.audit.log("RETRY", task_id, f"attempt {state.attempts}/{spec.max_retries}")
                    continue

                if self.policy.should_safe_stop(task_id, exc):
                    state.status = TaskStatus.FAILED
                    self.audit.log("FAILURE", task_id, "Safe-stop triggered; halting workflow.")
                    raise SafeStopException(f"Safe-stop on {task_id}: {exc}") from exc

                if self.policy.should_rollback(task_id, exc):
                    affected = self.graph.invalidate_downstream(task_id)
                    state.status = TaskStatus.ROLLED_BACK
                    self.metrics.task_rolled_back(task_id)
                    self.audit.log("ROLLBACK", task_id, f"Rolled back; invalidated {affected}")
                    return

                state.status = TaskStatus.FAILED
                raise
