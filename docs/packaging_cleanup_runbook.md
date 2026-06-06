Packaging Cleanup Preparation — Local reproduction runbook

Purpose
- Reproduce CI packaging checks locally using an editable install.
- Validate that `pip install -e .[test]` succeeds and that `pytest` runs cleanly.

Prerequisites
- Python 3.10+ installed (CI uses 3.x); we tested in 3.13 here.
- Git checkout of the repository at commit/branch to test.

Commands (local)

1) Create and activate a venv

   python3 -m venv .venv
   . .venv/bin/activate

2) Upgrade packaging tools

   pip install --upgrade pip build wheel

3) Editable install with test extras

   pip install -e .[test]

   Notes:
   - setup.py includes an extras_require['test'] with minimal test dependencies (pytest, pytest-mock, jsonschema).
   - If your environment needs additional dependencies, install them from requirements-dev.txt.

4) Run pytest

   mkdir -p .pytest_tmp
   PYTEST_ADDOPTS="--basetemp=$(pwd)/.pytest_tmp"
   export PYTEST_ADDOPTS
   pytest -q

5) (Optional) Seed holographic DB for local experiments

   python3 scripts/seed_holographic_db.py --db /tmp/holographic_test.db --confirm

   This script lazy-imports MemoryStore and will exit with a non-zero return code if the holographic plugin is not importable. The script requires --confirm to write on disk.

Notes and troubleshooting
- If pip warns that the project does not provide the extra 'test', ensure setup.py has been updated (this repo's setup.py now defines extras_require['test']).
- If editable install succeeds but pytest still fails due to import paths, check for existing PYTHONPATH shims in your environment (see shims inventory). Prefer unsetting PYTHONPATH to validate the editable install path is working.
- Keep PYTHONPATH support available for now; this runbook is for validation only — do not remove shims until CI confirms stability.
