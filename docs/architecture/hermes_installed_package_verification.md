# Hermes Installed Package Verification

## Status

Step 9 of the approved Hermes Runtime Inclusion phase.

## Decision

The clean package verifier now has an explicit Hermes runtime verification
mode:

```text
python scripts/verify_phase1_package.py --with-hermes-runtime
```

The default verifier still installs the Maya wheel with `--no-deps` so normal
offline CI can validate package shape, CLI surfaces, Enterprise BYO
configuration, and secret-safe behavior without network access.

The opt-in Hermes runtime mode installs the built Maya wheel with dependencies
enabled. This allows pip to resolve the pinned Hermes dependency declared in
the wheel metadata:

```text
hermes-agent @ git+https://github.com/Bidzina83/hermes-agent.git@b13e2fd6948a59eeb59fe618914147d97a2ee90a
```

## Runtime Availability Proof

After dependency installation, the verifier runs from the temporary installed
environment with `PYTHONPATH` removed and checks:

- `project_maya` imports from the installed wheel;
- `run_agent:AIAgent` imports and is callable;
- installed `hermes-agent` metadata exists;
- installed direct-url metadata references the inspected Hermes commit;
- `HermesRuntimeAdapter().compatibility()` reports compatible.

This proves Hermes availability without editable installs, repository-relative
imports, `/opt/hermes`, local checkout paths, or `PYTHONPATH` shims.

## Network Boundary

The opt-in mode may require network access because the approved Step 5
dependency is a pinned Git dependency. It is intentionally not the default test
mode until CI has an approved dependency cache, wheelhouse, or network policy.

## Deferred Work

This step does not:

- run live model inference;
- require real provider credentials;
- complete the Windows manual smoke test;
- claim broad platform support;
- package or load Maya skills.

Those remain later approved steps.
