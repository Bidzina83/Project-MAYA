# Phase 3 Dependency Contracts

## Status

Initial dependency/readiness contracts for Phase 3.

## Decision

Project MAYA now exposes static dependency contracts through
`project_maya.dependencies`. The contracts are safe to evaluate during
`maya doctor`: they inspect local Python packages, local commands, local
customer-managed application placeholders, connector configuration summaries,
and local-model configuration without installing software or performing live
network validation.

## Initial Contracts

| Profile | Dependencies |
| --- | --- |
| `maya-documents` | `reportlab`, `pypdf`, `Markdown`, `Pillow`, optional `pymupdf`, optional `pdftoppm`, optional `soffice`, customer-managed Microsoft Office |
| `maya-metabase` | Java runtime, customer-managed Metabase service, customer-managed Metabase application database |
| `maya-browser` | optional supported browser executable |
| `maya-messaging` | Google, Slack, and Telegram external-service readiness through connector validation |
| `maya-local-models` | customer-managed OpenAI-compatible local endpoint configuration |

`maya-core` intentionally has no heavy dependency requirements in this phase.

## Doctor Behavior

`maya doctor` adds stable checks such as:

- `dependencies.profile.maya-documents`
- `dependencies.python.reportlab`
- `dependencies.command.pdftoppm`
- `dependencies.application.ms-office`
- `dependencies.service.google`

Dependency messages are redacted summaries. They report install hints and
configuration status without printing secret values.

## Install Hints

Install hints are informational and OS-specific. Maya does not execute them in
Phase 3.

Examples:

- Documents Python extra: `python -m pip install project-maya[documents]`
- Documents preview Python extra: `python -m pip install project-maya[documents-preview]`
- Windows Poppler: `winget install oschwartz10612.Poppler`
- macOS Poppler: `brew install poppler`
- Debian/Ubuntu Poppler: `sudo apt-get install -y poppler-utils`
- Windows LibreOffice: `winget install TheDocumentFoundation.LibreOffice`
- macOS LibreOffice: `brew install --cask libreoffice`
- Debian/Ubuntu LibreOffice: `sudo apt-get install -y libreoffice`

Google, Slack, Telegram, Microsoft Office, Metabase databases, and local model
endpoints are customer-managed readiness surfaces, not packages Maya silently
installs.
