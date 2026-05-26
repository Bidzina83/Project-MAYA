# hermes.plugins proxy package — exposes plugins/ directory as hermes.plugins namespace
import os
__path__ = [os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'plugins'))]
