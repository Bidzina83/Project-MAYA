"""Assemble a compile-only reset launcher review artifact."""
import json
import argparse
import os
from pathlib import Path
import subprocess
import zipfile

from package_maya_reset_demo import BASE, INDEX_SHA, PAYLOAD_SHA, ROOT, require, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pipe-only", action="store_true", required=True)
    parser.parse_args()
    raw = (BASE / "model-payload-index.json").read_bytes()
    source_path = BASE / "model-payload.zip"
    require(sha(raw) == INDEX_SHA and sha(source_path.read_bytes()) == PAYLOAD_SHA,
            "base pin mismatch")
    index = json.loads(raw)
    rows = {row["path"]: row for row in index["files"]}
    out = ROOT / ".codex-build" / "Maya-Reset-Pipe-Review-2"
    out.mkdir()
    payload = out / "payload.zip"
    files = []
    with zipfile.ZipFile(source_path) as source, zipfile.ZipFile(
        payload, "x", compression=zipfile.ZIP_DEFLATED
    ) as target:
        require(len(source.namelist()) == len(rows) == 6788 and
                set(source.namelist()) == rows.keys(), "base inventory mismatch")
        for name, row in sorted(rows.items()):
            if name != "startup_check.py" and not name.startswith(
                ("python/", "hermes/", "dependencies/", "notices/")
            ):
                continue
            data = source.read(name)
            require(len(data) == row["size"] and sha(data) == row["sha256"], name)
            target.writestr(name, data)
            files.append(row)
        name = "maya_reset_demo.py"
        data = (ROOT / "scripts" / name).read_bytes()
        target.writestr(name, data)
        files.append(dict(path=name, size=len(data), sha256=sha(data)))
    with zipfile.ZipFile(payload) as archive:
        require(archive.namelist() == [row["path"] for row in files], "archive inventory")
        require(all(sha(archive.read(row["path"])) == row["sha256"] for row in files),
                "archive readback")
    manifest = out / "payload-index.json"
    manifest.write_text(json.dumps(dict(python_version=index["python_version"],
                                       zip_sha256=sha(payload.read_bytes()), files=files)),
                        encoding="ascii")
    exe = out / "MayaResetPipeReview.exe"
    compiler = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    runtime = ROOT / "src/project_maya/windows_runtime"
    subprocess.run([
        str(compiler), "/nologo", "/target:winexe", "/platform:x64",
        "/define:MAYA_RESET_PRIVATE", f"/out:{exe}",
        f"/resource:{manifest},MayaPython.payload-index.json",
        f"/resource:{payload},MayaPython.payload.zip",
        *[f"/r:{name}.dll" for name in ("System.Web.Extensions", "System.Windows.Forms",
           "System.Drawing", "System.IO.Compression", "System.IO.Compression.FileSystem")],
        *map(str, sorted(runtime.glob("*.cs"))),
    ], check=True)
    print(f"{len(files)} members; executable SHA256 {sha(exe.read_bytes()).upper()}")


if __name__ == "__main__":
    main()
