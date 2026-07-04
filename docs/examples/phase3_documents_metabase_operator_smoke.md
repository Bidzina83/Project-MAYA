# Phase 3 Metabase and Documents Operator Smoke

This guide exercises the Product Spec V2 Phase 3 capability surfaces from an installed
Maya package.

## Documents

Enable `maya-documents` and allow the specific document capability in local
governance policy:

```json
{
  "allow": [
    {"capability": "documents.inspect", "operation": "inspect"},
    {"capability": "documents.extract-text", "operation": "extract-text"},
    {"capability": "documents.create-pdf", "operation": "create-pdf"},
    {"capability": "documents.convert", "operation": "convert"},
    {"capability": "metabase.apply-provision", "operation": "apply-provision"}
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
maya documents extract-text --config maya-config.json --source maya-data/documents/sample.pdf --to extracted.txt
maya documents create-pdf --config maya-config.json --output out.pdf --text "Hello from Maya"
maya documents convert --config maya-config.json --source maya-data/documents/sample.docx --to sample.pdf --format pdf
maya skills status --config maya-config.json
```

The default output and audit records are redacted. Document contents are not
written to audit records. Bare output filenames are written under:

```text
maya-data/documents/outputs/
```

## Metabase

Enable `maya-metabase` and configure:

- deployment mode: `customer_managed` or `managed_local`;
- endpoint;
- application database credential reference;
- approved analytics sources.

Run:

```text
maya metabase health --config maya-config.json
maya metabase health --config maya-config.json --live
maya metabase lifecycle --config maya-config.json
maya metabase plan-provision --config maya-config.json --write
```

`apply-provision` requires explicit governance authorization and `--apply`:

```text
maya metabase apply-provision --config maya-config.json --apply
```

V2 Phase 3 provisioning plans include governed views, cards, and dashboard
specifications for approved analytics sources. Plans exclude Maya memory,
prompts, secrets, and raw files. Redacted plan files are written under:

```text
maya-data/metabase/provisioning/
```
