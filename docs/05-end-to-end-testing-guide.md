# End-to-End Testing Guide
## Agentic SDLC Orchestrator and URL Shortener Service

**Purpose:** Run and validate the three orchestrator scenarios (greenfield, brownfield, ambiguous) and exercise the Spring Boot URL Shortener API backed by PostgreSQL.

> The Python agents currently produce deterministic demonstration artifacts. The orchestrator does not generate or modify the Spring Boot source during a run; the service is built and tested separately. Ready tasks are dispatched in dependency order, but this prototype currently executes them sequentially rather than concurrently.

---

## 1. Prerequisites

- Python 3.10 or later and pip.
- Java 17 or later.
- PostgreSQL, with a database and credentials configured for the service.
- Git Bash or another shell for `mvnw`, or Windows PowerShell/CMD for `mvnw.cmd`.
- Network access on the first Maven Wrapper run so it can download Maven and dependencies.

Check installed tools:

```powershell
python --version
java -version
```

The Python command must resolve to an installed interpreter, not the Microsoft Store execution alias. The Maven Wrapper downloads Maven 3.9.16 automatically.

---

## 2. Install Orchestrator Dependencies

From the repository root:

```powershell
Set-Location .\agentic-orchestrator\orchestrator
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks activation, use the virtual environment interpreter directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

## 3. Run the Greenfield Scenario

From `agentic-orchestrator\orchestrator`:

```powershell
python main.py greenfield
```

### Verify the run

- The run should end with `=== Workflow completed successfully ===`.
- Approval-required tasks are auto-approved by default. The CLI prints an approval message and notes `AUTO_APPROVE=yes`; it does not prompt interactively.
- The final JSON summary should include the workflow ID, artifact names, decisions, and metrics.
- An append-only audit file should exist at `logs\greenfield_audit.jsonl`.

Inspect audit events:

```powershell
Get-Content .\logs\greenfield_audit.jsonl
```

The run should contain `APPROVAL` and `SUCCESS` events. Each of the 21 tasks in `specs\greenfield.yaml` should reach `DONE` in a successful run, with successful task events in the audit log.

The YAML graph expresses independent branches, but the current orchestrator processes ready tasks one at a time. This run validates dependency ordering and synchronization, not simultaneous execution.

---

## 4. Run the Brownfield Scenario

```powershell
python main.py brownfield
```

### Verify the run

- The run should end with `=== Workflow completed successfully ===`.
- The final artifact list should include `codebase_impact`, produced by the Codebase Reasoning Agent.
- The impact artifact should identify `UrlController`, `UrlShortenerService`, `POST /api/v1/urls`, and the controller-to-service-to-repository-to-PostgreSQL flow.
- `logs\brownfield_audit.jsonl` should contain successful events for `REQ-1`, `CODE-1`, `DES-5`, implementation, testing, documentation, risk, and release tasks in dependency order.

```powershell
Get-Content .\logs\brownfield_audit.jsonl
```

This scenario validates the agent's sample impact analysis and workflow sequencing. It does not dynamically inspect or patch the repository.

---

## 5. Run the Ambiguous-Requirement Scenario

### Approved interpretation

```powershell
python main.py ambiguous
```

Verify the workflow completes and the final artifact list includes `requirement`. The Requirement Agent should detect the vague phrase “safer” and create an ambiguity artifact. The approval gate is auto-approved by default, after which downstream tasks run.

### Rejected approval / safe-stop

In PowerShell:

```powershell
$env:AUTO_APPROVE = "no"
python main.py ambiguous
$env:AUTO_APPROVE = "yes"
```

Verify:

- The `REQ-1` gate is rejected.
- The workflow reports that it halted due to the rejected approval.
- The audit log at `logs\ambiguous_audit.jsonl` includes a `FAILURE` event for `REQ-1`.
- Downstream stages do not run after the rejection.

`AUTO_APPROVE=no` rejects every approval gate in a run; to test a later gate specifically, change the demo callback or provide a gate-specific approval implementation.

---

## 6. Run the Spring Boot Service Tests

From the repository root:

```powershell
Set-Location .\agentic-orchestrator\service
.\mvnw.cmd test
```

The test profile uses an in-memory H2 database, so PostgreSQL is not required for this step. Expected result: 8 tests pass across `UrlControllerTest` and `UrlShortenerServiceTest`.

---

## 7. Run the Service Against PostgreSQL

### Configure the database

Create a PostgreSQL database named `urlshortener` if it does not already exist. For example, in `psql`:

```sql
CREATE DATABASE urlshortener;
```

Set credentials using environment variables rather than committing local credentials. Update `application.yml` to read those values, or configure equivalent Spring datasource environment properties for your shell. The current default datasource configuration uses `localhost:5432`, database `urlshortener`, username `postgres`, and password `postgres`.

### Start the service

```powershell
.\mvnw.cmd spring-boot:run
```

Keep this terminal running. In a second terminal, from the repository root:

```powershell
$created = Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8080/api/v1/urls `
  -ContentType "application/json" `
  -Body '{"longUrl":"https://example.com/test-end-to-end"}'

$created | ConvertTo-Json
$code = $created.shortCode
```

Verify the response contains a non-empty `shortCode`, the submitted `longUrl`, a `shortUrl`, and a `createdAt` timestamp. A new URL should return HTTP `201 Created`.

Retrieve the saved URL:

```powershell
$resolved = Invoke-RestMethod -Method Get -Uri "http://localhost:8080/api/v1/urls/$code"
$resolved | ConvertTo-Json
```

Verify `longUrl` matches `https://example.com/test-end-to-end`. This endpoint returns the mapping as JSON; it does not issue an HTTP redirect.

### Check duplicate and error behavior

Submit the same URL again:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri http://localhost:8080/api/v1/urls `
  -ContentType "application/json" `
  -Body '{"longUrl":"https://example.com/test-end-to-end"}'
```

Verify it returns the existing mapping with HTTP `200 OK`.

Invalid URL (expected `400 Bad Request`):

```powershell
try {
    Invoke-RestMethod `
      -Method Post `
      -Uri http://localhost:8080/api/v1/urls `
      -ContentType "application/json" `
      -Body '{"longUrl":"not-a-url"}'
} catch {
    $_.Exception.Response.StatusCode.value__
}
```

Unknown code (expected `404 Not Found`):

```powershell
try {
    Invoke-RestMethod -Method Get -Uri http://localhost:8080/api/v1/urls/not-a-code
} catch {
    $_.Exception.Response.StatusCode.value__
}
```

Stop the service with `Ctrl+C`.

---

## 8. Cross-Scenario Checklist

| Validation | Greenfield | Brownfield | Ambiguous |
|---|---:|---:|---:|
| Workflow completes when approvals are accepted | [ ] | [ ] | [ ] |
| Expected specialized artifact is produced | [ ] | [ ] | [ ] |
| Audit JSONL file is created with stage events | [ ] | [ ] | [ ] |
| Approval rejection halts work at the gate | [ ] | [ ] | [ ] |
| Final metrics summary is printed | [ ] | [ ] | [ ] |

| Service validation | Result |
|---|---:|
| Maven Wrapper test suite passes (8 tests) | [ ] |
| PostgreSQL-backed POST creates a short code | [ ] |
| GET retrieves the original long URL | [ ] |
| Duplicate submission returns the existing mapping | [ ] |
| Invalid URL returns 400 | [ ] |
| Unknown short code returns 404 | [ ] |

---

## 9. Known Prototype Limitations

- Workflow agents are deterministic stubs; they do not call an LLM or apply generated code patches.
- Ready tasks are currently executed sequentially, despite parallelizable branches in the YAML DAG.
- Approval is simulated by the `AUTO_APPROVE` environment variable, not an interactive human approval UI.
- Audit and metric output is a prototype; validate reported counts against the audit log before treating them as operational reliability measurements.
- The service provides create and lookup APIs only. Analytics, rate limiting, expiry, Redis caching, and HTTP redirect behavior are not implemented in this service version.

---

## 10. Troubleshooting

| Symptom | Likely cause | Action |
|---|---|---|
| `ModuleNotFoundError` for `networkx` or `yaml` | Orchestrator dependencies not installed in the active Python environment | Activate `.venv` and run `python -m pip install -r requirements.txt` |
| YAML dependency error or workflow load failure | Invalid task ID in `dependsOn`, malformed YAML, or dependency cycle | Check the named scenario under `orchestrator\specs\` |
| Workflow reports safe-stop after approval | `AUTO_APPROVE` is set to `no` | Set `$env:AUTO_APPROVE = "yes"` and rerun |
| `mvnw.cmd` cannot download Maven | Network/proxy restrictions on first wrapper run | Check network/proxy access to Maven Central |
| Service fails to connect to PostgreSQL | Database is stopped, missing, or credentials differ | Check PostgreSQL status, database name, and datasource configuration |
| Port 8080 is already in use | Another process is listening on the service port | Stop that process or configure a different `server.port` |
