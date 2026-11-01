"""Fixed M02 product entry, not a general fault selector."""
import importlib.util
from pathlib import Path
import sys

if (sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14) or not all(
        (sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode))):
    raise SystemExit(2)
spec = importlib.util.spec_from_file_location("maya_model_entry", Path(__file__).with_name("model_child_entry.py"))
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
raise SystemExit(entry.main(deny_egress=True))
