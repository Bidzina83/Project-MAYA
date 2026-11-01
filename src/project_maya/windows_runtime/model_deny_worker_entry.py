"""Fixed M02 trusted worker entry; no caller-selectable policy mode."""
import os
from pathlib import Path
import sys

if (sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14) or not all(
        (sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode))):
    raise SystemExit(2)
runtime = Path(__file__).resolve().parent
if Path.cwd().resolve() != runtime.parent/"host" or os.environ.get("HERMES_DISABLE_LAZY_INSTALLS") != "1":
    raise SystemExit(2)
sys.path[:0] = [str(runtime), str(runtime/"dependencies")]
from project_maya.bridge.model_worker import main
raise SystemExit(main(deny_egress=True))
