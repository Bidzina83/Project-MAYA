# Hermes Package Inclusion

## Status

Step 5 of the approved Hermes Runtime Inclusion phase.

## Decision

Project MAYA now declares the selected Hermes runtime as a required package
dependency instead of relying on a local checkout, editable install,
`PYTHONPATH`, `/opt/hermes`, or repository-relative import path.

The runtime dependency is pinned to the exact source inspected during the
contract inventory:

```text
hermes-agent @ git+https://github.com/Bidzina83/hermes-agent.git@b13e2fd6948a59eeb59fe618914147d97a2ee90a
```

This keeps the Maya package tied to the adapter contract that was actually
reviewed for `run_agent:AIAgent`, Hermes `MemoryManager`, and the memory
provider lifecycle.

## Python Compatibility

The selected Hermes source declares Python support as `>=3.11,<3.14`.
Project MAYA now matches that range for this runtime-completion phase:

```text
Requires-Python: >=3.11,<3.14
```

This is intentional. A Python 3.14 environment should not be treated as a
supported packaged Hermes runtime while the selected Hermes dependency
declares it unsupported.

## Verification Boundary

The current package verifier still installs the built Maya wheel with
`--no-deps` so CI and offline tests do not need network access to GitHub.
However, it now inspects the wheel metadata and fails if the built artifact
does not declare:

- the pinned Hermes Git dependency;
- the compatible Python range.

Full dependency resolution and installed Hermes availability belong to the
later Installed Package Verification step, where the verifier can run in an
environment allowed to install runtime dependencies.

## Non-Goals

This step does not:

- copy Hermes runtime folders into `project_maya`;
- vendor a Hermes source snapshot;
- include default or trained Maya skills;
- prove real model inference;
- complete the Windows manual smoke test;
- claim Python 3.14 support for the packaged Hermes runtime.

Those remain later approved steps.
