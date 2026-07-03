# Phase 4 Documents and Metabase Operator Smoke

This guide exercises the first Phase 4 capability surfaces from an installed
Maya package.

## Documents

Enable `maya-documents` and allow the specific document capability in local
governance policy:

```json
{
  "allow": [
    {"capability": "documents.inspect", "operation": "inspect"},
    {"capability": "documents.extract-text", "operation": "extract-text"},
    {"capability": "documents.create-pdf", "operation": "create-pdf"}
  ]
}
```

Place test files under:

```text
maya-data/documents/
```

Run:

```text
maya documents inspect --config maya-config.json --source maya-data/documents/sample.txt
maya documents extract-text --config maya-config.json --source maya-data/documents/sample.pdf
maya documents create-pdf --config maya-config.json --output maya-data/documents/out.pdf --text "Hello from Maya"
```

The default output and audit records are redacted. Document contents are not
written to audit records.

## Metabase

Enable `maya-metabase` and configure:

- deployment mode: `customer_managed` or `managed_local`;
- endpoint;
- application database credential reference;
- approved analytics sources.

Run:

```text
maya metabase health --config maya-config.json
maya metabase plan-provision --config maya-config.json
```

`apply-provision` requires explicit governance authorization and `--apply`:

```text
maya metabase apply-provision --config maya-config.json --apply
```

Phase 4 does not perform live dashboard creation by default. Provisioning plans
exclude Maya memory, prompts, secrets, and raw files.
