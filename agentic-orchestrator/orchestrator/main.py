"""CLI entry point for running the agentic SDLC orchestrator against one of
the three demo scenarios (greenfield / brownfield / ambiguous).

Usage:
    python main.py greenfield
    python main.py brownfield
    python main.py ambiguous
"""
from __future__ import annotations

import argparse
import json
import os
import sys

try:
    import yaml
except ModuleNotFoundError as exc:
    if exc.name != "yaml":
        raise
    print(
        "Missing Python dependency: PyYAML. From this directory, run "
        "'python -m pip install -r requirements.txt', then retry.",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc

from agents.registry import build_default_registry
from core.audit import AuditLog, MetricsRecorder
from core.graph import WorkflowGraph
from core.models import TaskContext
from core.orchestrator import Orchestrator, SafeStopException
from core.policy import ApprovalRequest, PolicyEngine

SPEC_DIR = os.path.join(os.path.dirname(__file__), "specs")


def cli_approval_callback(request: ApprovalRequest) -> bool:
    print(f"\n[APPROVAL REQUIRED] Task {request.task_id}: {request.description}")
    print(f"  Context: {request.context_summary}")
    answer = os.environ.get("AUTO_APPROVE", "yes").strip().lower()
    if answer in ("yes", "y", "true", "1"):
        print("  -> auto-approved (AUTO_APPROVE=yes)")
        return True
    print("  -> auto-rejected (AUTO_APPROVE=no)")
    return False


def run_scenario(scenario: str) -> None:
    spec_path = os.path.join(SPEC_DIR, f"{scenario}.yaml")
    if not os.path.exists(spec_path):
        print(f"Unknown scenario '{scenario}'. Available: greenfield, brownfield, ambiguous")
        sys.exit(1)

    with open(spec_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    graph = WorkflowGraph.from_yaml(spec_path)
    agents = build_default_registry()
    policy = PolicyEngine(approval_callback=cli_approval_callback)
    audit = AuditLog(path=os.path.join(os.path.dirname(__file__), "logs", f"{scenario}_audit.jsonl"))
    metrics = MetricsRecorder()

    context = TaskContext(workflow_id=raw["workflowId"], intent=raw["intent"])

    orchestrator = Orchestrator(graph=graph, agents=agents, policy=policy, audit=audit, metrics=metrics)

    print(f"=== Running scenario: {scenario} ===")
    print(f"Intent: {raw['intent']}\n")

    try:
        orchestrator.run(context)
        print("\n=== Workflow completed successfully ===")
    except SafeStopException as e:
        print(f"\n=== Workflow halted (safe-stop): {e} ===")

    print("\n--- Final Engineering Summary ---")
    summary = {
        "workflowId": context.workflow_id,
        "scope": raw.get("scope"),
        "artifacts": list(context.artifacts.keys()),
        "decisions": [d.__dict__ for d in context.decisions],
        "metrics": metrics.snapshot(),
    }
    print(json.dumps(summary, indent=2, default=str))


def main() -> None:
    parser = argparse.ArgumentParser(description="Agentic SDLC Orchestrator")
    parser.add_argument("scenario", choices=["greenfield", "brownfield", "ambiguous"])
    args = parser.parse_args()
    run_scenario(args.scenario)


if __name__ == "__main__":
    main()
