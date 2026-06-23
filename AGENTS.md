# Project MAYA Agent Guidance

Read `PROJECT_MAYA.md` before making architectural, implementation, refactoring, memory, governance, workflow, infrastructure, or integration decisions.

## Product identity

Project MAYA is an AI Employee platform, not a chatbot project. Maya is an Information Manager AI Employee for small and medium-sized businesses. The product must remain transparent, governed, auditable, recoverable, portable, and capable of preserving long-term organizational memory.

## Hermes Agent

Hermes Agent is the current middleware and agent functionality core. It connects Maya to:

- LLM providers
- messaging gateways and applications
- persistent memory
- governance services
- productivity platforms and operational tools
- business intelligence systems such as Metabase
- business workflows

Hermes currently executes Maya's identity, role, skills, context assembly, tool selection, and workflow orchestration. Hermes is central to the current implementation but is not an authoritative system of record and must remain architecturally replaceable.

Treat Maya's identity, skills, policies, procedures, integration definitions, and durable knowledge as portable, versioned product artifacts wherever possible. Hermes may load and execute these artifacts; Hermes-specific runtime state must not permanently own them.

The governing principle is:

> Hermes executes Maya; Hermes does not permanently define or own Maya.

## Authority and state

- Authoritative state lives outside the LLM in files, repositories, registries, databases, audit logs, and governance records.
- Conversation history and model memory are never authoritative.
- Filesystem-backed knowledge is the preferred human-inspectable source of truth.
- Governance is the final authority for significant actions and authoritative state changes.
- Embeddings and indexes are derived, disposable artifacts; they are never authoritative.
- Operational context must be reconstructable from persistent records.

## Governance boundary

Do not model governance as merely a downstream processing step. Governance must mediate significant reads, actions, and writes across the Hermes boundary, including:

- tool calls and workflow execution
- external-system changes
- persistent-memory writes
- changes to authoritative business state
- privileged or policy-sensitive operations

Hermes proposes. Governance approves, rejects, constrains, or records. Significant actions must be explainable, traceable, and auditable.

## Engineering priorities

Prefer deterministic behavior, explicit configuration, audit logging, versioned artifacts, testability, reproducibility, backward compatibility, provider independence, and cross-platform compatibility.

Avoid hidden state, implicit behavior, vendor lock-in, runtime-only persistence, autonomous self-modification, untracked side effects, hardcoded paths, and platform-specific assumptions.

The final product must support Windows, macOS, and Linux and must not require Hostinger, Docker, Linux, Hermes, or any specific cloud or LLM provider.

Use configurable application-data roots such as `MAYA_HOME` or `MAYA_DATA_DIR`. Prefer portable formats and technologies such as Markdown, YAML, JSON, SQLite, Python, and open standards.

## Decision rule

When uncertain, choose the option that best maximizes, in order:

1. Persistence
2. Auditability
3. Governance
4. Recoverability
5. Transparency
6. Cross-platform compatibility
7. Provider independence
