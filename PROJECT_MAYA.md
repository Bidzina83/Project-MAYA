# Project MAYA — Product and Architecture Context

## Purpose

Project MAYA is the foundation of **IM AI Employee**, a commercially deployable Information Manager AI Employee for small and medium-sized businesses.

Maya is intended to act as an accountable digital employee: assisting operations, managing organizational information, preserving institutional knowledge, coordinating governed workflows, and keeping humans able to inspect and control what the system does.

Project MAYA is not a chatbot project. Its defining properties are persistence, governance, transparency, auditability, recoverability, portability, and long-term organizational memory.

## Product architecture

The product consists of replaceable providers and adapters around a governed, persistent AI-employee core:

```text
Users and Messaging Channels
             |
             v
+-----------------------------------------+
| Hermes Agent Middleware                 |
|                                         |
| - Maya identity and role                |
| - skills and agent behavior             |
| - context assembly                      |
| - tool and workflow orchestration       |
| - LLM-provider adapter                  |
| - messaging and application adapters    |
| - productivity-system connectors        |
+-------------------+---------------------+
                    |
          governed reads/actions/writes
                    |
          +---------+---------+
          |                   |
          v                   v
  Governance Layer     Persistent Memory
          |                   |
          +---------+---------+
                    |
                    v
       Authoritative Business State
 Files | Databases | Registries | Audit Logs
                    |
                    v
 Google | Office | Metabase | Other Workflows
```

This diagram represents logical responsibilities, not a mandatory deployment topology. Governance is a control boundary around consequential operations, not simply a downstream box in a linear pipeline.

## Hermes Agent middleware role

Hermes Agent is the current middleware and agent functionality core of IM AI Employee.

Hermes connects:

- LLM providers
- messaging gateways and applications
- persistent memory
- governance services
- productivity platforms
- business intelligence systems
- business workflows and operational tools

Hermes currently hosts the executable agent definition of Maya, including:

- Maya's identity as an Information Manager
- role boundaries and behavioral instructions
- skills and operating procedures
- context assembly
- tool selection and orchestration
- workflow execution
- provider and integration adapters

Hermes is therefore more than a message router or generic runtime. It is the current execution host for Maya as an AI Employee.

However, Hermes must not become the authoritative owner of Maya. Maya's identity, skills, policies, procedures, integration definitions, and durable knowledge should be represented as portable, versioned product artifacts wherever possible. Hermes may load and execute these artifacts, but their authoritative definitions must remain outside Hermes-specific runtime state.

This separation must allow Hermes to be replaced without losing:

- Maya's identity and role
- Maya's skills and procedures
- organizational memory
- governance policies
- integration and workflow definitions
- workflow history and audit records

The intended principle is:

> Hermes executes Maya; Hermes does not permanently define or own Maya.

Hermes is architecturally replaceable, but it is not incidental. It is a central component of the current product implementation whose contracts must prevent permanent runtime lock-in.

## Authority model

Important state must exist outside the LLM. Authoritative state should reside in:

- files and repositories
- registries and databases
- audit logs
- governance records
- authoritative records in connected operational systems

Never treat conversation history, model memory, embeddings, indexes, or Hermes runtime state as authoritative.

Filesystem-backed state is the preferred human-inspectable source of truth for product knowledge and configuration. Where a database or external operational system is the appropriate system of record, its authority must be explicit and its changes governed and auditable.

## Governance

Governance is mandatory and is intended to become the final authority over consequential system behavior.

Governance must be able to validate, approve, reject, constrain, and record:

- tool calls
- workflow execution
- external-system mutations
- authoritative memory writes
- changes to policies, skills, or identity artifacts
- privileged or policy-sensitive operations

The preferred interaction is:

> Hermes proposes. Governance approves, rejects, constrains, or records.

Every significant action should be explainable, traceable, auditable, and recoverable. Governance records must survive runtime replacement, deployment changes, and product upgrades.

## Persistent memory

Persistent memory preserves organizational knowledge independently of the LLM provider, model version, Hermes version, session history, container lifecycle, operating system, and hosting platform.

Memory must survive restarts, rebuilds, migrations, vendor replacement, and product upgrades.

### Memory hierarchy

1. **Operational memory** — active tasks, current objectives, pending actions, and operational status.
2. **Project knowledge** — specifications, architecture, procedures, integrations, and governance policies.
3. **Institutional memory** — lessons learned, decision records, design rationale, historical outcomes, and postmortems.

The retrieval hierarchy is:

```text
Authoritative filesystem or database state
                    |
                    v
                Registries
                    |
                    v
                  Indexes
                    |
                    v
                Embeddings
                    |
                    v
                 Retrieval
```

Indexes and embeddings are derived artifacts. They must be reproducible from authoritative records and safe to discard and rebuild.

## Storage and portability

Prefer human-readable, inspectable formats:

- Markdown
- YAML
- JSON
- SQLite where structured transactional storage is appropriate

Avoid opaque proprietary storage and hidden runtime-only state.

All storage roots must be configurable. Do not hardcode Linux-specific paths such as `/opt/data` or `/root/.hermes`. Use configuration and environment variables such as `MAYA_HOME` and `MAYA_DATA_DIR`, resolving them through cross-platform path libraries.

The final product must support:

- Windows, macOS, and Linux
- local and self-hosted deployment
- single-machine and small-business deployment
- single-user and multi-user operation

It must not require Hostinger, Docker, Linux, Hermes Agent, any specific cloud provider, or any specific LLM provider.

## Integrations and operational systems

Hermes provides the current orchestration and adapter boundary for messaging gateways, LLM providers, Google Workspace, Microsoft Office, Metabase, and other productivity or operational systems.

Integration adapters should expose explicit contracts and keep credentials, provider-specific behavior, and transport details separated from Maya's portable identity, skills, policies, and memory.

External systems may be authoritative for their own business records. Reads and changes must respect governance policy, authorization boundaries, audit requirements, idempotency, and recoverability.

## Metabase

Metabase is the IM AI Employee Intelligence and Accountability Portal. It provides visibility into operational activity, governance decisions, organizational knowledge, business workflows, system health, and AI-employee performance.

Metabase is an observability layer, not a source of truth. Dashboards must derive from authoritative persistent records.

## Current development environment

The current development and validation environment uses a Hostinger VPS, Linux, Docker, Hermes Agent, and a self-hosted GitHub Actions runner.

These are implementation details of the development environment, not mandatory components of the final product architecture. Product decisions must not create unnecessary dependencies on Hostinger, VPS infrastructure, Docker-only execution, Linux-only features, `systemd`, or platform-specific filesystem assumptions.

## Engineering principles

Prefer:

- deterministic behavior
- explicit configuration and contracts
- audit logging
- versioned artifacts
- testability and reproducibility
- backward compatibility
- provider independence
- cross-platform libraries
- recoverable and idempotent operations

Avoid:

- hidden or implicit state
- vendor lock-in
- runtime-only persistence
- autonomous self-modification
- untracked side effects
- hardcoded storage locations
- operating-system-specific logic unless isolated behind an abstraction

## Current priorities

1. Persistent memory subsystem
2. Governance framework
3. Filesystem-based state management
4. Google Workspace integration
5. Knowledge persistence
6. GitHub automation
7. Operational reliability

## Decision rule

When architectural uncertainty remains, choose the solution that maximizes, in order:

1. Persistence
2. Auditability
3. Governance
4. Recoverability
5. Transparency
6. Cross-platform compatibility
7. Provider independence

The AI runtime, hosting platform, and LLM provider are replaceable. Durable identity, governed behavior, authoritative state, and organizational memory must survive their replacement.
