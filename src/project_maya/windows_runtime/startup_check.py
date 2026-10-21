"""Managed Python startup health check, run only by the protected native launcher."""

import sys


def main():
    if sys.version_info[:3] != (3, 13, 14):
        return 2
    if not sys.flags.isolated or not sys.flags.no_site or not sys.flags.dont_write_bytecode:
        return 2
    if len(sys.argv) != 2 or len(sys.argv[1]) != 32:
        return 2
    nonce = sys.argv[1]
    if any(char not in "0123456789abcdef" for char in nonce):
        return 2
    beacon = 'MAYA_PROTECTED_PYTHON_STARTED_V1:' + nonce + '\n'
    try:
        with open("python-startup.txt", "x", encoding="ascii", newline="\n") as stream:
            if stream.write(beacon) != len(beacon):
                return 3
        encoded = beacon.encode("ascii")
        if sys.stdout.buffer.write(encoded) != len(encoded):
            return 3
        sys.stdout.buffer.flush()
    except OSError:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
