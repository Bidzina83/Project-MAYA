"""Fixed, open-only child entry for the separate delete-child diagnostic."""
import sys


def serve(argv, entry, cwd, pid, source, destination, backend_factory=None):
    from pathlib import PureWindowsPath
    from journal_access_role import PrivateChannel, ProbeSession, WindowsCalls, _attempt_path, _hex

    try:
        path = PureWindowsPath(entry)
        if (len(argv) != 2 or not _hex(argv[1], 32) or str(path) != entry
                or PureWindowsPath(argv[0]) != path
                or path.name != "journal_delete_child_entry.py" or path.parent.name != "runtime"):
            return 2
        attempt = argv[1]
        directory = _attempt_path(str(path.parent.parent), attempt)
        if PureWindowsPath(cwd) != directory / "state":
            return 2
        channel = PrivateChannel(source, destination)
        command = channel.receive()
        if (type(command) is not dict or set(command) != {"v", "type", "attempt", "request_id"}
                or type(command["v"]) is not int or command["v"] != 1
                or command["type"] != "delete_child_probe" or command["attempt"] != attempt
                or not _hex(command["request_id"], 32) or source.read(1) != b""):
            return 2
        request = command["request_id"]
        session = ProbeSession(str(directory), attempt, "child", pid, request,
                               (backend_factory or WindowsCalls)())
        control = session._probe(directory / "state" / "delete-child-control", 64, True)
        target = session._probe(directory, 64, True)
        channel.send(dict(v=1, type="delete_child_result", attempt=attempt, request_id=request,
                          pid=pid, control=control, target=target))
        return 0
    except Exception:
        return 2


def _main():
    if (sys.platform != "win32" or sys.version_info[:3] != (3, 13, 14)
            or not all((sys.flags.isolated, sys.flags.no_site, sys.flags.dont_write_bytecode))):
        return 2
    import os
    from pathlib import Path

    runtime = Path(__file__).parent
    if not runtime.is_absolute() or runtime.name != "runtime":
        return 2
    sys.path.insert(0, str(runtime))
    return serve(sys.argv, __file__, os.getcwd(), os.getpid(), sys.stdin.buffer, sys.stdout.buffer)


if __name__ == "__main__":
    raise SystemExit(_main())
