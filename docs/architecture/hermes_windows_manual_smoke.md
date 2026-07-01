# Hermes Windows Manual Smoke Test

## Status

Step 10 of the approved Hermes Runtime Inclusion phase.

## Decision

The Windows installed-package smoke path is accepted only when the test runs
from a clean installed wheel, outside the repository root, without
`PYTHONPATH`, and with the pinned Hermes runtime resolved from the declared
package dependency.

The automated equivalent is:

```text
python scripts/verify_phase1_package.py --with-hermes-runtime
```

This command builds the Maya wheel, installs it into a temporary virtual
environment, resolves the pinned `hermes-agent` Git dependency, imports
`run_agent:AIAgent`, verifies installed Hermes metadata, and checks
`HermesRuntimeAdapter().compatibility()`.

## Manual Windows Commands

Run from the Project MAYA repository root on Windows with Python 3.13:

```text
py -3.13 scripts\verify_phase1_package.py --with-hermes-runtime
```

For a longer manual smoke test, use a neutral working directory after
installation so repository files cannot shadow installed packages:

```text
$repo = "C:\Users\tsere\OneDrive\Desktop\MyHermes\Project-MAYA"
$venv = "$repo\.maya-win-smoke"
$smoke = "$env:TEMP\maya-win-smoke-run"
New-Item -ItemType Directory -Force -Path $smoke | Out-Null
cd $smoke
& "$venv\Scripts\python.exe" -c "import project_maya; from run_agent import AIAgent; print(project_maya.__name__, callable(AIAgent))"
```

The expected final import output is:

```text
project_maya True
```

Hermes may emit non-fatal local-state warnings when the operator's Hermes home
is not readable in the current shell. Those warnings do not fail the smoke
test unless `AIAgent` import, metadata validation, or adapter compatibility
fails.

## Windows Findings

The first Windows manual run exposed two important conditions:

- Running from the repository root can shadow installed packages when local
  package directories share names with installed Hermes modules.
- A stale local `hermes-agent` wheel cache can install an incompatible
  artifact for the pinned Git dependency because the package version remained
  `0.17.0` across commits.

The verifier now passes `--no-cache-dir` in Hermes runtime mode and explicitly
checks the installed `hermes_cli.config` surface required by Hermes imports:
`load_config`, `load_env`, `get_hermes_home`, and `_expand_env_vars`.

## Acceptance Evidence

On local Windows, after PR #179 was merged into `main`, the hardened command
completed successfully:

```text
python scripts\verify_phase1_package.py --with-hermes-runtime
```

The command is intentionally quiet on success. A zero exit code is the
acceptance signal.

## Boundaries

This step proves installed Hermes runtime availability and import-level
adapter compatibility on Windows. It does not claim full Windows product
support, signed installer readiness, live model inference, connector OAuth,
backup and restore support for production data, or Metabase lifecycle support.
