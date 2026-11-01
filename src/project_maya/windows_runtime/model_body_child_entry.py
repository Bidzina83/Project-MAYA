"""Fixed M03d child entry; no caller-selected mutation."""
import sys
if sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14) or not all(
        (sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode)):
    raise SystemExit(2)
import importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("maya_model_child", Path(__file__).with_name("model_child_entry.py"))
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
raise SystemExit(entry.main(wrong_body=True))
