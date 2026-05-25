# hermes shim to map hermes.plugins -> ./plugins
import os
__path__ = [os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))]
