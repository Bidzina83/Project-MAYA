import os
# Point maya_dev.plugins package to the repository's plugins/ directory
__path__ = [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'plugins'))]
