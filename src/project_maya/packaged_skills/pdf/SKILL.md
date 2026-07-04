---
name: documents/pdf
origin: maya_trained
source_repository: Bidzina83/Hermes-Agent-Maya-Skills
source_skill: skills/pdf
source_declared_name: pdf
version: 0.1.0
capabilities:
  - documents.inspect
  - documents.extract-text
  - documents.create-pdf
  - documents.convert
---

# PDF and Document Operations

Use this skill when Maya needs to inspect local document metadata, extract PDF
text, create simple PDFs, or convert supported office documents through the
governed Project MAYA document capability.

This packaged artifact is the Product MAYA wrapper for the trained
`skills/pdf` source from `Bidzina83/Hermes-Agent-Maya-Skills`. The upstream
skill creates and validates PDFs from Markdown through portable helper scripts;
Maya exposes that capability through product document operations and the
Maya/Hermes adapter boundary, not by direct CLI imports from the trained-skills
repository.

All file reads and writes must go through Project MAYA document operations.
Do not read arbitrary filesystem paths directly. Do not expose document
contents, prompts, raw local paths, credentials, tokens, or customer records in
logs, audit records, diagnostics, or status output.

Supported actions are:

- inspect document metadata under the configured Maya documents directory;
- extract PDF text only through the governed extraction operation;
- create PDFs from approved text inputs through the governed PDF creation
  operation;
- convert supported documents through the governed LibreOffice conversion
  operation when LibreOffice is available.

Every consequential action requires local authorization and audit.
