"""Python-entry beacon only; not an isolation or Hermes qualification test."""

import sys
import time


def main():
    if sys.version_info[:3] != (3, 13, 14):
        return 2
    if not sys.flags.isolated or not sys.flags.no_site:
        return 2
    beacon = '{"schema":"maya.python_entry.v1","status":"python_entered","production_qualified":false}\n'
    try:
        # Exclusive creation prevents an old marker from becoming fresh evidence.
        with open("python-startup.json", "x", encoding="ascii") as stream:
            if stream.write(beacon) != len(beacon):
                return 3
    except OSError:
        return 3
    sys.stdout.write(beacon)
    sys.stdout.flush()
    # A bounded observation window permits external token read-back before exit.
    time.sleep(5)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
