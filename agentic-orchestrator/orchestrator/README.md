# Agentic SDLC Orchestrator (Python)

A governed, dependency-graph-driven orchestrator that coordinates specialized
agents across the full SDLC lifecycle (Requirements → Design →
Implementation → Testing/Documentation → Release) to produce the Spring Boot
URL Shortener microservice in `../service/`.

## Why this is not a linear chain

- The workflow is defined as data (`specs/*.yaml`), not hardwired control flow.
- `core/graph.py` builds a true DAG (`networkx`) from that spec; independent
  tasks (e.g. Testing + Documentation, both depending only on Implementation)
  are exposed as parallel-ready sets, not forced into a sequence.
- `core/orchestrator.py` is a stateful controller: it tracks per-task status
  (`PENDING → RUNNING → AWAITING_APPROVAL → DONE/FAILED/ROLLED_BACK`), gates
  high-impact tasks on human approval, retries transient failures (bounded),
  rolls back and invalidates downstream tasks on unrecoverable failure, and
  safe-stops the whole run on rejected approvals or release-stage failures.
- `core/policy.py` is the governance layer: approvals, guardrails (simple
  secret/credential pattern scan), retry/rollback/safe-stop rules.
- `core/audit.py` writes an append-only JSONL audit log per run and computes
  reliability metrics (success rate, retry/rollback counts, MTTR, end-to-end
  latency).

## Structure

```
orchestrator/
  core/
    models.py        # TaskSpec, TaskState, TaskContext, Decision, AuditEvent
    graph.py          # DAG engine (networkx) + re-planning support
    policy.py          # Approval, guardrails, retry/rollback/safe-stop
    audit.py            # Audit log + reliability metrics
    orchestrator.py      # Main control loop
  agents/
    base.py              # Agent interface
    requirement_agent.py # Requirement Understanding (Core Req. #1)
    planner_agent.py     # Task Decomposition (Core Req. #2)
    design_agent.py       # Design + Codebase Reasoning (Core Req. #3)
    dev_agent.py            # Implementation
    test_doc_release_agents.py # Testing, Docs, Risk & Validation, Release
    registry.py               # Maps YAML `owningAgent` names to agent instances
  specs/
    greenfield.yaml   # Full URL shortener build (21 tasks)
    brownfield.yaml    # Add rate limiting to existing service
    ambiguous.yaml       # "Make links safer" — ambiguity resolution demo
  main.py                # CLI entry point
```

## Running

```bash
cd agentic-orchestrator/orchestrator
pip install -r requirements.txt

# Run any of the three demo scenarios
python main.py greenfield
python main.py brownfield
python main.py ambiguous
```

Each run:
1. Loads the workflow DAG from the chosen YAML spec.
2. Executes tasks in dependency order, running independent tasks as
   parallel-ready groups.
3. Prompts for human approval at each `requiresApproval: true` gate
   (auto-approved by default for unattended demo runs; set
   `AUTO_APPROVE=no` to see the rejection/safe-stop path).
4. Writes an audit log to `logs/<scenario>_audit.jsonl`.
5. Prints a Final Engineering Summary (artifacts produced, decisions made,
   reliability metrics) to stdout.

### Example: forcing a rejection to see safe-stop behavior

```bash
AUTO_APPROVE=no python main.py greenfield
```

## Extending with a real LLM

Agents in `agents/` currently use deterministic, rule-based logic so the
whole pipeline runs end-to-end without any API key. To wire in a real LLM
(Copilot/Claude/OpenAI), replace the body of an agent's `execute()` method
with a call to your model client, keeping the same input (`TaskSpec`,
`TaskContext`) and output (`dict` artifact) contract — no orchestrator
changes are required.
