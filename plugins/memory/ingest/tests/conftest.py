import sys, os
# Ensure repo root is on sys.path for tests run in CI (low-risk shim).
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if root not in sys.path:
    sys.path.insert(0, root)
