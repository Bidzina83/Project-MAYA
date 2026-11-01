"""Fixed M05a bootstrap with existing startup diagnostic support."""
import sys
if sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14) or not all(
        (sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode)):
    raise SystemExit(2)
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("maya_model_worker_support", Path(__file__).with_name("model_validation_worker_entry.py"))
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
raise SystemExit(entry.launch(same_client_budget=True))
