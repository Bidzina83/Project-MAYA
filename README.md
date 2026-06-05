Project MAYA — Embedding provider integration

This repository contains a minimal embedding wrapper and tests for Project MAYA.

Setup (recommended):
- Create a virtualenv and activate it
- pip install -r requirements-dev.txt
- Set OPENAI_API_KEY if you want to run live OpenAI integration tests

Environment variables
- MAYA_EMBEDDING_PROVIDER: 'local' (default) or 'openai' or 'azure'
- OPENAI_API_KEY: API key for OpenAI/Azure
- OPENAI_MODEL: model name (OpenAI) or deployment id (Azure)
- For Azure: OPENAI_API_BASE, OPENAI_API_VERSION, OPENAI_DEPLOYMENT

Files of interest:
- src/maya/embeddings.py — public entrypoint
- src/maya/adapters/openai_provider.py — OpenAI/Azure adapter
- tests/test_embeddings.py — placeholder unit test (local fallback)
- tests/test_openai_provider.py — live OpenAI integration test (skipped without OPENAI_API_KEY)

## Developer notes: runtime scripts, testing, and deployment

- Runtime scripts used by the scheduler live under `/opt/data/.hermes/scripts` on the host. Use the helper script `tools/maya-dev/deploy/ensure_runtime_scripts.sh` to copy the helper scripts into that directory:

  ./tools/maya-dev/deploy/ensure_runtime_scripts.sh --source /opt/data/maya-dev/tools/maya-dev --dest /opt/data/.hermes/scripts --mode 755

- To run the ingest test suite locally:

  PYTHONPATH=/opt/data/.hermes_shim /opt/hermes/.venv/bin/pytest -c /dev/null -q plugins/memory/ingest/tests -p no:xdist

  If pytest reports issues due to temporary directory ownership, set TMPDIR to a writable path (e.g. `TMPDIR=/opt/data/pytest_tmp`).

- CI now installs the package in editable mode when possible and runs tests across Python versions. Optional provider smoke tests are gated by repository secrets (`OPENAI_API_KEY`, `HF_API_KEY`).

## Running integration tests locally

Integration tests that exercise live provider APIs (OpenAI/Azure) are marked `openai_integration` and are skipped by default when the `OPENAI_API_KEY` is not set.

To run only the OpenAI integration tests locally:

1. Export your API key in the environment (do not commit it):

   export OPENAI_API_KEY="sk-..."

2. Run pytest with the integration marker (example):

   PYTHONPATH=/opt/hermes /opt/hermes/.venv/bin/pytest -q --basetemp=/opt/data/pytest-basetemp /opt/hermes/plugins/memory/ingest/tests -k "openai_integration"

To run the full test suite including integration tests:

   export OPENAI_API_KEY="sk-..."
   PYTHONPATH=/opt/hermes /opt/hermes/.venv/bin/pytest -q --basetemp=/opt/data/pytest-basetemp /opt/hermes/plugins/memory/ingest/tests

Notes:
- Never paste your API key into commits or public places. Use repository secrets in GitHub Actions for CI runs.
- If using Azure OpenAI, set OPENAI_API_BASE, OPENAI_API_VERSION, and OPENAI_DEPLOYMENT accordingly in your environment before running tests.

