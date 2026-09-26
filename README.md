# URL Shortener — Agentic SDLC Prototype

A working prototype demonstrating agentic Software Development Life Cycle
(SDLC) orchestration — from raw intent to a running Spring Boot microservice
— for a URL shortener service.

## Repository Layout

```
URLShortener/
├── docs/                              # Engineering documentation (SDLC artifacts)
│   ├── 01-requirement-understanding.md   # Intent → ambiguity → normalized problem
│   ├── 02-flow-diagrams.md               # Mermaid flow/sequence/state diagrams
│   ├── 03-task-decomposition.md          # Task graph, dependencies, sequencing
│   └── 04-final-engineering-summary.md   # Plan, artifacts, risks, assumptions, limitations
│
└── agentic-orchestrator/
    ├── orchestrator/                  # Python: the agentic SDLC orchestration engine
    │   ├── core/                        # Graph engine, policy/governance, audit/metrics, control loop
    │   ├── agents/                      # Requirement, Planner, Design, Dev, Test, Docs, Risk, Release agents
    │   ├── specs/                       # Workflow DAGs (greenfield / brownfield / ambiguous scenarios)
    │   └── main.py                      # CLI entry point
    │
    └── service/                       # Java/Spring Boot: the URL Shortener microservice
        └── src/main/java/.../urlshortener/
            ├── entity/                   # UrlMapping (JPA auto-generated id -> Base62 shortCode)
            ├── repository/, service/, controller/, dto/, exception/, util/
```

## How the Pieces Fit Together

1. **`docs/`** captures the human-readable engineering narrative: what was asked, what was ambiguous, how it was decomposed into tasks, and the final summary of what was built, its risks, and its limitations.
2. **`agentic-orchestrator/orchestrator/`** is the executable version of that same process: `specs/*.yaml` encodes the task graph from `03-task-decomposition.md` as data, `agents/*.py` implements each stage agent (Requirement, Planner, Design, Dev, Test, Docs, Risk, Release), and `core/orchestrator.py` runs the graph with governance (approvals, retries, rollback, safe-stop, audit, metrics).
3. **`agentic-orchestrator/service/`** is the production code artifact the orchestrator's Implementation-stage tasks (`IMPL-*`) are responsible for: a Spring Boot microservice with `POST /api/v1/urls` (save a long URL, get back a Base62 short code derived from its JPA auto-generated id) and `GET /api/v1/urls/{shortCode}` (resolve it back to the original URL).

See `docs/03-task-decomposition.md` for the explicit cross-reference table mapping each task ID to its owning agent and generated source file.

## Quick Start

### Run the orchestrator (Python)
```bash
cd agentic-orchestrator/orchestrator
pip install -r requirements.txt
python main.py greenfield   # or: brownfield | ambiguous
```

### Run the microservice (Spring Boot)
```bash
cd agentic-orchestrator/service
# requires a local PostgreSQL database named "urlshortener" (see application.yml)
mvnw.cmd spring-boot:run
```

```bash
curl -X POST http://localhost:8080/api/v1/urls \
  -H "Content-Type: application/json" \
  -d '{"longUrl":"https://example.com/some/very/long/path"}'

curl http://localhost:8080/api/v1/urls/<shortCode>
```

### Run the microservice tests (H2, no PostgreSQL required)
```bash
cd agentic-orchestrator/service
mvnw.cmd test
```

## Documentation Index

| Doc | Purpose |
|---|---|
| `docs/01-requirement-understanding.md` | Requirement Understanding (Core Req. #1) |
| `docs/02-flow-diagrams.md` | Orchestration flow, dependency graph, state machine, sequence diagrams |
| `docs/03-task-decomposition.md` | Task Decomposition (Core Req. #2), with implementation cross-references |
| `docs/04-final-engineering-summary.md` | Final Engineering Summary (Core Req. #8) |
| `agentic-orchestrator/orchestrator/README.md` | Orchestrator architecture and how to run each scenario |
| `agentic-orchestrator/service/README.md` | Microservice API reference, data model, setup, and testing instructions |
