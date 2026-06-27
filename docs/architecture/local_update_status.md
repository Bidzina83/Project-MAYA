# Local Update Status CLI

## Decision

Phase 1 introduces an honest local update status command:

```text
maya update --config <maya-config.json> --check
maya update --config <maya-config.json> --rollback
```

The command inspects local metadata only. It does not contact update servers,
download artifacts, execute installers, replace files, or perform rollback.

`--check` looks for:

```text
<deployment.data_dir>/updates/update-manifest.json
```

`--rollback` looks for:

```text
<deployment.data_dir>/updates/rollback.json
```

Unsigned metadata is reported as rejected. Missing metadata is reported as
unavailable. Network access is always reported as unused.

## Scope

This is not the production updater. Signed manifests, artifact provenance,
rollback execution, SBOM validation, installer integration, offline Enterprise
update bundles, and automatic update policy are later distribution work. Phase
1 only exposes a safe status surface so the required command exists without
claiming unsupported update behavior.
