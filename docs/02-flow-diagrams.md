# Flow Diagrams — Agentic SDLC Orchestrator (URL Shortener)

## 1. Requirement Understanding — Process Flow

```mermaid
flowchart TD
    A[Raw Intent / Stakeholder Request] --> B[Requirement Analyst Agent]
    B --> C{Parse Intent}
    C --> D[Interpret into Clusters:\nCore APIs / Analytics / Reliability]
    D --> E{Detect Ambiguities?}
    E -- Yes --> F[List Ambiguities A1..A8\n+ Working Assumptions]
    F --> G{Assumption is\nHigh-Impact?}
    G -- Yes --> H[Flag as requiresApproval]
    G -- No --> I[Auto-resolve with default assumption]
    H --> J[Human Approval Checkpoint]
    I --> K[Merge into Normalized Problem]
    J -- Approved --> K
    J -- Rejected / Modified --> B
    E -- No --> K[Merge into Normalized Problem]
    K --> L[Normalize into Engineering Problem Statement]
    L --> M[Derive Functional Requirements]
    L --> N[Derive Non-Functional Requirements]
    M --> O[Define Acceptance Criteria]
    N --> O
    O --> P[Emit Structured Requirement Artifact\nJSON: REQ-URL-SHORTENER-001]
    P --> Q[Audit Log: Decision Lineage Recorded]
    P --> R[Handoff to Planner Agent\nTask Decomposition Stage]
```

---

## 2. Overall SDLC Orchestration — Dependency Graph

```mermaid
flowchart LR
    subgraph REQ["REQUIREMENTS"]
        R1[Requirement Analyst Agent]
    end
    subgraph PLAN["TASK DECOMPOSITION"]
        P1[Planner Agent]
    end
    subgraph DES["DESIGN"]
        D1[Architect / Design Agent]
        D2[Codebase Reasoning Agent\n(Brownfield only)]
    end
    subgraph IMPL["IMPLEMENTATION"]
        I1[Dev Agent: Controller]
        I2[Dev Agent: Service]
        I3[Dev Agent: Repository]
    end
    subgraph VAL["TESTING & DOCS (parallel)"]
        T1[Test Agent]
        T2[Documentation Agent]
        T3[Risk & Validation Agent]
    end
    subgraph REL["RELEASE READINESS"]
        REL1[Release Agent]
    end

    R1 -->|"Approval Gate"| P1
    P1 --> D2
    D2 --> D1
    P1 --> D1
    D1 -->|"Approval Gate"| I1
    D1 --> I2
    D1 --> I3
    I1 --> T1
    I2 --> T1
    I3 --> T1
    I1 --> T2
    I2 --> T2
    I3 --> T2
    T1 --> T3
    T2 --> T3
    T3 -->|"Approval Gate"| REL1
    REL1 --> DONE[Final Engineering Summary]

    classDef gate fill:#f96,stroke:#333,stroke-width:1px;
```

**Legend:**
- Solid arrows = dependency (`dependsOn`)
- Nodes within the same subgraph row execute **in parallel** once their shared dependency is satisfied (e.g., Controller/Service/Repository dev agents; Test/Docs agents)
- "Approval Gate" = human checkpoint required before proceeding (`requiresApproval: true`)

---

## 3. Orchestrator State Machine (per task node)

```mermaid
stateDiagram-v2
    [*] --> PENDING
    PENDING --> READY: dependencies satisfied
    READY --> RUNNING: orchestrator dispatches agent
    RUNNING --> AWAITING_APPROVAL: requiresApproval = true
    RUNNING --> DONE: success, no approval needed
    AWAITING_APPROVAL --> DONE: human approves
    AWAITING_APPROVAL --> FAILED: human rejects
    RUNNING --> FAILED: transient error, retries exhausted
    FAILED --> RUNNING: bounded retry (attempt < max)
    FAILED --> ROLLED_BACK: high-impact error / safe-stop triggered
    ROLLED_BACK --> READY: re-plan triggered (upstream artifact changed)
    DONE --> [*]
    ROLLED_BACK --> [*]: safe-stop (manual intervention required)
```

---

## 4. Requirement Understanding — Sequence Diagram (Ambiguous Scenario Example)

```mermaid
sequenceDiagram
    participant U as Human Stakeholder
    participant O as Orchestrator
    participant RA as Requirement Analyst Agent
    participant PL as Policy Engine
    participant AU as Audit Log

    U->>O: Submit raw intent ("make links safer")
    O->>RA: dispatch REQ stage
    RA->>RA: Parse intent, detect vague/ambiguous terms
    RA->>AU: log("ambiguity_detected", intent)
    RA-->>O: return normalized draft + ambiguities + proposed interpretation
    O->>PL: is_approved(REQ-1)?
    PL-->>O: requiresApproval = true (pending)
    O->>U: present interpretation + ambiguities for review
    U-->>O: approve / modify interpretation
    alt Approved
        O->>AU: log("approval_granted", REQ-1)
        O->>O: mark REQ-1 = DONE
        O->>O: unlock PLAN stage (Planner Agent)
    else Rejected / Modified
        O->>RA: re-run with human feedback
        RA-->>O: revised requirement artifact
    end
```

---

*Diagrams rendered with Mermaid — viewable directly in GitHub, VS Code (Markdown Preview Mermaid Support), or any Mermaid-compatible renderer.*
