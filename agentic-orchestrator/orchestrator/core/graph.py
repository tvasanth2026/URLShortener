"""Dependency-graph engine built on networkx.

Loads a workflow spec (list of TaskSpec) and exposes graph queries needed by
the orchestrator: ready tasks, parallel groups, downstream invalidation for
re-planning, etc. This keeps the SDLC workflow expressed as *data*, not
hardwired control flow.
"""
from __future__ import annotations

from typing import Dict, Iterable, List, Set

import networkx as nx
import yaml

from .models import TaskSpec, TaskState, TaskStatus


class WorkflowGraph:
    def __init__(self, task_specs: List[TaskSpec]):
        self.graph = nx.DiGraph()
        self.states: Dict[str, TaskState] = {}

        for spec in task_specs:
            self.graph.add_node(spec.id)
            self.states[spec.id] = TaskState(spec=spec)

        for spec in task_specs:
            for dep in spec.depends_on:
                if dep not in self.graph:
                    raise ValueError(f"Task '{spec.id}' depends on unknown task '{dep}'")
                self.graph.add_edge(dep, spec.id)

        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            raise ValueError(f"Workflow graph contains cycles: {cycles}")

    @classmethod
    def from_yaml(cls, path: str) -> "WorkflowGraph":
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        specs = [
            TaskSpec(
                id=t["id"],
                stage=t["stage"],
                description=t["description"],
                owning_agent=t["owningAgent"],
                depends_on=t.get("dependsOn", []) or [],
                requires_approval=t.get("requiresApproval", False),
                traces_to=t.get("tracesTo", []) or [],
                max_retries=t.get("maxRetries", 3),
            )
            for t in data["tasks"]
        ]
        return cls(specs)

    def ready_tasks(self) -> List[str]:
        """Tasks whose dependencies are all DONE and which are themselves PENDING."""
        ready = []
        for node in self.graph.nodes:
            state = self.states[node]
            if state.status != TaskStatus.PENDING:
                continue
            deps = list(self.graph.predecessors(node))
            if all(self.states[d].status == TaskStatus.DONE for d in deps):
                ready.append(node)
        return ready

    def parallel_groups(self) -> List[List[str]]:
        """Groups tasks that share the exact same dependency set (safe to run concurrently)."""
        groups: Dict[frozenset, List[str]] = {}
        for node in self.graph.nodes:
            deps = frozenset(self.graph.predecessors(node))
            groups.setdefault(deps, []).append(node)
        return [nodes for nodes in groups.values() if len(nodes) > 1]

    def downstream_of(self, task_id: str) -> Set[str]:
        return set(nx.descendants(self.graph, task_id))

    def invalidate_downstream(self, task_id: str) -> List[str]:
        """Re-planning support: reset a task and everything depending on it back to PENDING."""
        affected = [task_id] + list(self.downstream_of(task_id))
        for node in affected:
            state = self.states[node]
            state.status = TaskStatus.PENDING
            state.attempts = 0
            state.result = None
            state.error = None
        return affected

    def is_complete(self) -> bool:
        return all(s.status in (TaskStatus.DONE,) for s in self.states.values())

    def has_unresolved_failures(self) -> bool:
        return any(s.status in (TaskStatus.FAILED, TaskStatus.ROLLED_BACK) for s in self.states.values())
