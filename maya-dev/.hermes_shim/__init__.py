"""PYTHONPATH shim used by CI workflows.
When the workflow sets PYTHONPATH to maya-dev/.hermes_shim, this package runs
and ensures the repository root and the plugins/ directory are on sys.path so
imports like ``plugins.memory.adapters.holographic_adapter`` resolve correctly.
"""
import sys
import os

# Add the repository root (two levels up) to sys.path
_here = os.path.abspath(os.path.dirname(__file__))
_repo_root = os.path.abspath(os.path.join(_here, os.pardir))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Also ensure the hermes proxy package (if repo provides it) is discoverable
_plugins_path = os.path.join(_repo_root, "plugins")
if os.path.isdir(_plugins_path) and _plugins_path not in sys.path:
    sys.path.insert(0, _plugins_path)
