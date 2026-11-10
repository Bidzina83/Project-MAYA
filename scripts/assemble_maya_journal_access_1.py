"""Assemble the reviewed offline diagnostic. Never execute the product."""

import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import struct
import subprocess
import sys
import zipfile
import os


ROOT = Path(__file__).resolve().parents[1]
BUILDS = ROOT / ".codex-build"
BASE = BUILDS / "maya-offline-model-final-20261104-3"
BUILD = BUILDS / "maya-journal-access-20261110-1"
PREDECESSOR = "Maya-Offline-Model-Final-3"
NAME = "Maya-Journal-Access-1"
REVIEW = ROOT / "docs/architecture/maya_final_output_actual_token_package_review.md"
SOURCE = ROOT / "src/project_maya/windows_runtime"
CHECK = ROOT / "scripts/maya_journal_access_offline_check.cs"
FLAGS = "HERMES_JOURNAL_ACCESS,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT"
INDEX_HASH = "17cbc9ae19fe42dd4c96ca9f963c4b08152874e7676e28485eaff603d3e328a3"
PAYLOAD_HASH = "eb41614596be929c3ba1ed71622d8b983c308056a9cce26701f5668aaf13913f"
ZIP_HASH = "e59b7061d619f7084f7725c9873266a72d59d84ec4c0708995a4fab5ea5c8a7f"
EXE_HASH = "0766f67d2eae76f353f7c03e1caa9ed9532447e320c45b45c320e7c028a71389"
MANIFEST_HASH = "afc0f2a1c854812ccfbb9dccfe4c5b89d112746573ae2df149fbdc482c5e8d22"
REVIEW_HASH = "1462c9375f7acc6286c0ac3371197521e3ad00778ef2d66c77b6ce6141596ab9"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def pinned(path, expected, size=None):
    raw = path.read_bytes()
    require(digest(raw) == expected and (size is None or len(raw) == size), str(path))
    return raw


def write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def json_bytes(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2).encode("ascii") + b"\n"


def predecessor():
    archive_path = BASE / (PREDECESSOR + ".zip")
    pinned(archive_path, ZIP_HASH)
    pinned(BASE / "MayaProtectedPython.exe", EXE_HASH)
    with zipfile.ZipFile(archive_path) as archive:
        raw = archive.read(PREDECESSOR + "/package-manifest.json")
        require(digest(raw) == MANIFEST_HASH, "predecessor manifest")
        require(raw == (BASE / PREDECESSOR / "package-manifest.json").read_bytes(), "manifest parity")
        require(digest(archive.read(PREDECESSOR + "/MayaProtectedPython.exe")) == EXE_HASH, "packaged predecessor")
    manifest = json.loads(raw)
    require(len(manifest["source_files"]) == 401, "predecessor freeze inventory")
    for entry in manifest["source_files"]:
        pinned(BASE / "source-freeze" / entry["path"], entry["sha256"], entry["size"])
    return manifest


def inputs(manifest, review):
    replacements = dict(re.findall(r"\| `([\w.]+\.cs)` \| `([a-f0-9]{64})`", review))
    original = {Path(row["path"]).name: row["sha256"] for row in manifest["source_files"]
                if row["path"].startswith(SOURCE.relative_to(ROOT).as_posix() + "/") and row["path"].endswith(".cs")}
    require(len(original) == 38 and len(replacements) == 10 and len(original.keys() & replacements.keys()) == 4,
            "exact launcher delta")
    result = {SOURCE / name: pinned(SOURCE / name, sha) for name, sha in (original | replacements).items()}
    require(len(result) == 44, "exact launcher inventory")
    return result


def check_imports(data):
    modules = {n[:-3].removesuffix("/__init__").replace("/", "."): n
               for n in data if n.startswith("project_maya/") and n.endswith(".py")}
    seen = set()
    external = set()
    todo = ["project_maya", "project_maya.bridge", "project_maya.bridge.protocol", "project_maya.bridge.transport"]

    def imports(node, scope):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            return
        if isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = scope.split(".")
                base = ".".join(parts[:len(parts) + 1 - node.level] + ([base] if base else []))
            yield base
            yield from (base + "." + a.name for a in node.names if base + "." + a.name in modules)
        for child in ast.iter_child_nodes(node):
            yield from imports(child, scope)

    while todo:
        module = todo.pop()
        if module in seen:
            continue
        seen.add(module)
        name = modules[module]
        scope = module if name.endswith("/__init__.py") else module.rsplit(".", 1)[0]
        for dependency in imports(ast.parse(data[name], filename=name), scope):
            if dependency.startswith("project_maya"):
                require(dependency in modules, "missing module: " + dependency)
                parts = dependency.split(".")
                todo.extend(".".join(parts[:i]) for i in range(1, len(parts) + 1) if ".".join(parts[:i]) in modules)
            elif dependency.split(".")[0] not in sys.stdlib_module_names:
                external.add(dependency)
    require(len(seen) == 43 and external == {
        "cryptography.exceptions", "cryptography.hazmat.primitives.asymmetric.ed25519",
        "cryptography.hazmat.primitives.serialization"}, "reviewed eager import closure")
    for name in ("python/python.exe", "python/python313.dll", "python/DLLs/_ctypes.pyd",
                 "python/DLLs/libffi-8.dll", "python/Lib/ctypes/__init__.py", "python/Lib/ctypes/wintypes.py"):
        require(name in data, "bundled interpreter dependency: " + name)


def payload(manifest, review):
    source_zip = BASE / "model-payload.zip"
    pinned(source_zip, PAYLOAD_HASH)
    index = json.loads(pinned(BASE / "model-payload-index.json", INDEX_HASH))
    require(manifest["payload_zip_sha256"] == index["zip_sha256"] == PAYLOAD_HASH and
            manifest["payload_index_sha256"] == INDEX_HASH and index["python_version"] == "3.13.14", "predecessor payload pins")
    indexed = {item["path"]: item for item in index["files"]}
    data, omitted = {}, []
    with zipfile.ZipFile(source_zip) as archive:
        require(len(archive.namelist()) == len(indexed) == len(index["files"]) == 6788 and
                set(archive.namelist()) == indexed.keys(), "baseline membership")
        for name, row in indexed.items():
            raw = archive.read(name)
            require(len(raw) == row["size"] and digest(raw) == row["sha256"], name)
            if name == "startup_check.py" or name.startswith(("python/", "notices/", "project_maya/")):
                data[name] = raw
            else:
                omitted.append(name)
    old_roots = re.search(r"```text\n(.*?)\n```", review, re.S).group(1).splitlines()
    require(len(data) == 889 and len(omitted) == 5899 and
            sorted(n for n in omitted if "/" not in n) == sorted(old_roots) and
            sum(n.startswith("hermes/") for n in omitted) == 827 and
            sum(n.startswith("dependencies/") for n in omitted) == 5049, "approved omissions")
    roles = {}
    for name, size, sha in re.findall(r"\| `(journal_access_\w+\.py)` \| (\d+) \| `([a-f0-9]{64})`", review):
        path = SOURCE / name
        roles[path] = pinned(path, sha, int(size))
        require(name not in indexed, "no role replacement")
        ast.parse(roles[path], filename=name)
        data[name] = roles[path]
    require(len(roles) == 3 and len(data) == len({n.casefold() for n in data}) == 892 and
            sum(map(len, data.values())) == 37359018, "exact reviewed payload")
    for name, raw in data.items():
        require(PurePosixPath(name).as_posix() == name and not name.startswith("/") and
                not {"..", "."}.intersection(name.split("/")) and not set("\\:").intersection(name) and
                len(raw) <= 33554432, "unsafe payload member")
    check_imports(data)
    return data, roles, sorted(omitted)


def run(command):
    return subprocess.run([str(arg) for arg in command], check=True, cwd=ROOT)


def main():
    manifest = predecessor()
    review_bytes = pinned(REVIEW, REVIEW_HASH)
    review = review_bytes.decode("utf-8")
    launcher = inputs(manifest, review)
    data, roles, omitted = payload(manifest, review)
    BUILD.mkdir()
    frozen = launcher | roles | {REVIEW: review_bytes}
    for name in ("scripts/assemble_maya_journal_access_1.py", "scripts/maya_journal_access_offline_check.cs",
                 "tests/check_windows_journal_access_profile.ps1", "tests/windows_journal_access_profile_fixtures.cs"):
        path = ROOT / name
        frozen[path] = path.read_bytes()
    source_records = []
    freeze = BUILD / "source-freeze"
    for path, raw in sorted(frozen.items()):
        relative = path.relative_to(ROOT).as_posix()
        write(freeze / relative, raw)
        source_records.append(dict(path=relative, size=len(raw), sha256=digest(raw)))

    archive_path = BUILD / "journal-access-payload.zip"
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(data.items()):
            archive.writestr(name, raw)
    payload_sha = digest(archive_path.read_bytes())
    index_path = BUILD / "journal-access-payload-index.json"
    index = dict(python_version="3.13.14", zip_sha256=payload_sha,
                 files=[dict(path=n, size=len(b), sha256=digest(b)) for n, b in sorted(data.items())])
    write(index_path, json_bytes(index))
    with zipfile.ZipFile(archive_path) as archive:
        require(archive.namelist() == sorted(data), "archive inventory")
        for row in index["files"]:
            raw = archive.read(row["path"])
            require(len(raw) == row["size"] and digest(raw) == row["sha256"], row["path"])

    csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    refs = "/reference:System.Windows.Forms.dll,System.Drawing.dll,System.Web.Extensions.dll,System.IO.Compression.dll,System.IO.Compression.FileSystem.dll"
    common = [csc, "/nologo", "/warnaserror+", "/optimize+", "/platform:x64", "/define:" + FLAGS, refs]
    sources = [freeze / path.relative_to(ROOT) for path in sorted(launcher)]
    exe = BUILD / "MayaProtectedPython.exe"
    run(common + ["/target:winexe", "/main:ProjectMaya.WindowsRuntime.ProtectedPython", "/out:" + str(exe),
                  f"/resource:{archive_path},MayaPython.payload.zip", f"/resource:{index_path},MayaPython.payload-index.json"] + sources)
    raw = exe.read_bytes()
    pe = struct.unpack_from("<I", raw, 60)[0]
    require(raw[:2] == b"MZ" and raw[pe:pe+6] == b"PE\0\0\x64\x86" and
            struct.unpack_from("<H", raw, pe+24)[0] == 0x20B and struct.unpack_from("<H", raw, pe+92)[0] == 2, "x64 GUI PE")
    for role in ("worker", "child"):
        require(f"journal_access_{role}_entry.py".encode("utf-16le") in raw, "fixed selector")
    checker = BUILD / "JournalAccessOfflineCheck.exe"
    run(common + ["/target:exe", "/main:JournalAccessOfflineCheck", "/out:" + str(checker),
                  freeze / CHECK.relative_to(ROOT)] + sources)
    run([checker, exe, index_path, archive_path])
    require(predecessor() == manifest, "predecessor preserved")
    for row in source_records:
        pinned(freeze / row["path"], row["sha256"], row["size"])
        pinned(ROOT / row["path"], row["sha256"], row["size"])
    print("Offline verification passed. Staged; not sealed.", flush=True)
    record = dict(schema="maya.journal_access.offline_package.v1", artifact=NAME, version="0.2.2-journal-access.1",
                  scope="offline-journal-access-matrix-v1", file_version="0.2.2.1", defines=FLAGS.split(","),
                  assembly_approved=True, native_run_approved=False, native_execution_performed=False,
                  containment_qualified=False, production_qualified=False, independent_cleanup_verified=False,
                  real_inference=False, exe_sha256=digest(raw), exe_size=len(raw),
                  predecessor_zip_sha256=ZIP_HASH, predecessor_exe_sha256=EXE_HASH,
                  payload_zip_sha256=payload_sha, payload_index_sha256=digest(index_path.read_bytes()),
                  payload_files=index["files"], expanded_bytes=37359018, omitted=omitted,
                  source_files=source_records, exact_embedded_resources_verified=True)
    write(BUILD / "staging-receipt.json", json_bytes(record))


if __name__ == "__main__":
    main()
