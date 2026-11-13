"""Build the offline Windows demo from verified runtime bytes."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / ".codex-build/maya-offline-model-final-20261104-3"
OUT = ROOT / ".codex-build/Maya-Reset-Offline-Windows-3.zip"
INDEX_SHA = "17cbc9ae19fe42dd4c96ca9f963c4b08152874e7676e28485eaff603d3e328a3"
PAYLOAD_SHA = "eb41614596be929c3ba1ed71622d8b983c308056a9cce26701f5668aaf13913f"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(ok, message):
    if not ok:
        raise ValueError(message)


def main():
    raw = (BASE / "model-payload-index.json").read_bytes()
    payload = BASE / "model-payload.zip"
    require(sha(raw) == INDEX_SHA and sha(payload.read_bytes()) == PAYLOAD_SHA, "runtime pin mismatch")
    index = json.loads(raw)
    paths = {row["path"]: row for row in index["files"]}
    members = {}
    with zipfile.ZipFile(payload) as source:
        require(len(source.namelist()) == len(paths) == 6788 and
                set(source.namelist()) == paths.keys(), "runtime inventory mismatch")
        for name, row in paths.items():
            if not name.startswith(("python/", "hermes/", "dependencies/", "notices/")):
                continue
            path = PurePosixPath(name)
            require(not path.is_absolute() and path.as_posix() == name and ".." not in path.parts
                    and "\\" not in name and ":" not in name, "invalid member path")
            data = source.read(name)
            require(len(data) == row["size"] and sha(data) == row["sha256"], name)
            members[name] = data
    members["maya_reset_demo.py"] = (ROOT / "scripts/maya_reset_demo.py").read_bytes()
    members["README.txt"] = (
        "Maya Reset offline Windows demo\n\n"
        "Extract the ZIP. From the extracted folder in PowerShell, run:\n"
        ".\\python\\python.exe -I -B .\\maya_reset_demo.py\n\n"
        "Run once with y and once with n. Expected endpoint receipt counts: 1 and 0.\n"
        "Synthetic data and endpoint only. No real provider or credentials.\n"
        "This package does not configure or verify OS network isolation.\n"
    ).encode("ascii")
    require(len(members) == len({name.casefold() for name in members}), "case collision")
    with zipfile.ZipFile(OUT, "x", compression=zipfile.ZIP_DEFLATED) as target:
        for name, data in sorted(members.items()):
            target.writestr(name, data)
    with zipfile.ZipFile(OUT) as target:
        require(target.namelist() == sorted(members) and
                all(target.read(name) == data for name, data in members.items()), "archive readback failed")
    print(len(members), sha(OUT.read_bytes()))


if __name__ == "__main__":
    main()
