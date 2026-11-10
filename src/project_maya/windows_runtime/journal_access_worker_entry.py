"""Fixed worker bootstrap for the synthetic journal access profile."""
import sys


def _main():
    if (sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14)
            or not all((sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode))):
        return 2
    try:
        import importlib.util
        import os
        from pathlib import Path

        runtime = Path(__file__).parent
        if not runtime.is_absolute() or runtime.name != "runtime":
            return 2
        sys.path.insert(0, str(runtime))
        spec = importlib.util.spec_from_file_location("maya_journal_access_role", runtime / "journal_access_role.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.serve_entry("worker", platform=sys.platform, version=sys.version_info, flags=sys.flags,
                                 argv=sys.argv, entry_path=__file__, cwd=os.getcwd(), pid=os.getpid(),
                                 source=sys.stdin.buffer, destination=sys.stdout.buffer)
    except Exception:
        return 2


if __name__ == "__main__":
    raise SystemExit(_main())
