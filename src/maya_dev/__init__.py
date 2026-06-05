# shim to allow imports using maya_dev.* for compatibility with tests
# This proxies the top-level maya package into maya_dev namespace.
from maya import *

try:
    __all__ = maya.__all__
except Exception:
    __all__ = [k for k in globals().keys() if not k.startswith('_')]
