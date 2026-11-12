"""Compile and seal the approved diagnostics successor without launching it."""
import json
import os
from pathlib import Path
import re
import struct
import sys
import zipfile

from assemble_maya_journal_access_1 import ROOT, digest, json_bytes, pinned, require, run, write
from assemble_maya_journal_access_2 import update_literals


def main():
    base = ROOT / ".codex-build/maya-journal-delete-child-1"
    build = base.with_name("maya-journal-delete-child-2")
    old_name, name = "Maya-Journal-Delete-Child-1", "Maya-Journal-Delete-Child-2"
    require(not build.exists(), "refuse overwrite")
    old_raw = pinned(base / old_name / "package-manifest.json",
                     "96dc4862ea883bec019bb10e5f6158f596bf7b75e69261c7b9c9527acdc1daa1")
    old = json.loads(old_raw)
    old_zip = "c2f37587476d6e886486bda5346cc2652dfe3c80d537cec0a20587d32d30e8dc"
    old_exe = "4442c7a6b7f161155bd6bcb5c5352ff7913176e6aefdb32bdd347cc3515db28d"
    payload_name, index_name = "journal-delete-child-payload.zip", "journal-delete-child-payload-index.json"
    payload_sha = "f57cea986ca3b0814e73ccc7bcb8f912a05ed0fb225ac53f0af5c8a52f73326f"
    index_sha = "d8f8ea595da9907aef21727eb7078181044a2fc2cbafb13ac7ac8fc4baabe036"

    def verify_old():
        executable = pinned(base / "MayaProtectedPython.exe", old_exe)
        pinned(base / (old_name + ".zip"), old_zip)
        pinned(base / payload_name, payload_sha)
        pinned(base / index_name, index_sha)
        with zipfile.ZipFile(base / (old_name + ".zip")) as z:
            require(z.read(old_name + "/package-manifest.json") == old_raw and
                    z.read(old_name + "/MayaProtectedPython.exe") == executable, "predecessor archive parity")
        require(len(old["source_files"]) == 62, "predecessor source inventory")
        for r in old["source_files"]:
            pinned(base / "source-freeze" / r["path"], r["sha256"], r["size"])

    verify_old()
    payload = pinned(base / payload_name, payload_sha)
    index_bytes = pinned(base / index_name, index_sha)
    index = json.loads(index_bytes)
    require(index["files"] == old["payload_files"] and index["zip_sha256"] == payload_sha and
            len(index["files"]) == 891 and sum(r["size"] for r in index["files"]) == 37359038, "payload inventory")
    with zipfile.ZipFile(base / payload_name) as z:
        paths = z.namelist()
        require(len(paths) == len({p.casefold() for p in paths}) == 891 and
                set(paths) == {r["path"] for r in index["files"]}, "payload paths")
        for r in index["files"]:
            raw = z.read(r["path"])
            require(len(raw) == r["size"] and digest(raw) == r["sha256"], r["path"])

    review = "docs/architecture/maya_journal_delete_child_2_package_review.md"
    review_bytes = (ROOT / review).read_bytes()
    changes = dict(re.findall(r"\| `([\w.]+\.cs)` \| `([a-f0-9]{64})`", review_bytes.decode()))
    require(set(changes) == {"DeleteChildControlDescriptor.cs", "DeleteChildControlLease.cs",
                             "DeleteChildControlOwner.cs", "DeleteChildControlProvision.cs", "ProtectedPython.cs"},
            "reviewed launcher paths")
    fixture = "tests/windows_delete_child_control_descriptor_fixtures.cs"
    fixture_sha = "8495b4f5993d540f523614b037219ea8ab8d05ff4c3e4de8407fd36942964e1f"
    checker = "scripts/maya_journal_access_offline_check.cs"
    legacy = "tests/check_windows_journal_access_profile.ps1"
    py_tests = ["tests/test_journal_delete_child_entry_inert.py", "tests/test_journal_access_role_inert.py"]
    prefix = "src/project_maya/windows_runtime/"
    files, compile_names, working = {}, [], {}
    versions = [(b'"0.2.3.1"', b'"0.2.3.2"', 1),
                (b'"0.2.3-journal-delete-child.1"', b'"0.2.3-journal-delete-child.2"', 2)]
    for r in old["source_files"]:
        path = r["path"]
        leaf = Path(path).name
        if path.startswith(prefix) and path.endswith(".cs"):
            sha = changes.get(leaf, r["sha256"])
            raw = pinned(ROOT / path, sha)
            working[path] = sha
            compile_names.append(path)
            files[path] = update_literals(raw, versions) if leaf == "ProtectedPython.cs" else raw
        elif path == checker:
            raw = pinned(base / "source-freeze" / path, r["sha256"])
            files[path] = update_literals(raw, [versions[0], (*versions[1][:2], 1)])
        elif path == fixture or path in [legacy, *py_tests]:
            sha = fixture_sha if path == fixture else r["sha256"]
            files[path] = pinned(ROOT / path, sha)
            working[path] = sha
        elif path.startswith(prefix) and path.endswith(".py"):
            files[path] = pinned(base / "source-freeze" / path, r["sha256"])
    require(len(compile_names) == 53 and all((prefix + n) in compile_names for n in changes), "compile paths")
    for path in ("scripts/assemble_maya_journal_access_1.py", "scripts/assemble_maya_journal_access_2.py",
                 Path(__file__).relative_to(ROOT).as_posix()):
        files[path] = (ROOT / path).read_bytes()
    files[review] = review_bytes
    build.mkdir()
    freeze = build / "source-freeze"
    for path, raw in files.items():
        write(freeze / path, raw)
    write(build / payload_name, payload)
    write(build / index_name, index_bytes)
    flags = "HERMES_JOURNAL_DELETE_CHILD_SOURCE,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT"
    csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    refs = "/reference:System.Windows.Forms.dll,System.Drawing.dll,System.Web.Extensions.dll,System.IO.Compression.dll,System.IO.Compression.FileSystem.dll"
    common = [csc, "/nologo", "/warnaserror+", "/optimize+", "/platform:x64", "/define:" + flags, refs]
    sources = [freeze / n for n in sorted(compile_names)]
    exe = build / "MayaProtectedPython.exe"
    run(common + ["/target:winexe", "/main:ProjectMaya.WindowsRuntime.ProtectedPython", "/out:" + str(exe),
                  f"/resource:{build / payload_name},MayaPython.payload.zip",
                  f"/resource:{build / index_name},MayaPython.payload-index.json"] + sources)
    raw = exe.read_bytes()
    pe = struct.unpack_from("<I", raw, 60)[0]
    require(raw[:2] == b"MZ" and raw[pe:pe+6] == b"PE\0\0\x64\x86" and
            struct.unpack_from("<H", raw, pe+24)[0] == 0x20b and struct.unpack_from("<H", raw, pe+92)[0] == 2 and
            "journal_delete_child_entry.py".encode("utf-16le") in raw and
            "journal_access_child_entry.py".encode("utf-16le") not in raw, "x64 GUI and fixed selector")
    for cls, path, args in [
        ("JournalAccessOfflineCheck", checker, [exe, build / index_name, build / payload_name]),
        ("DeleteChildControlDescriptorFixtures", fixture, []),
    ]:
        tool = build / (cls + ".exe")
        run(common + ["/target:exe", "/main:" + cls, "/out:" + str(tool), freeze / path] + sources)
        run([tool, *args])
    run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ROOT / legacy])
    run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *py_tests])
    verify_old()
    for path, sha in working.items():
        pinned(ROOT / path, sha)
    for path, contents in files.items():
        pinned(freeze / path, digest(contents), len(contents))
    pinned(exe, digest(raw), len(raw))
    pinned(build / index_name, index_sha)
    pinned(build / payload_name, payload_sha)
    manifest = dict(artifact=name, version="0.2.3-journal-delete-child.2", file_version="0.2.3.2",
                    scope=old["scope"], defines=flags.split(","), sealed=True, assembly_approved=True,
                    native_run_approved=False, native_execution_performed=False, production_qualified=False,
                    containment_qualified=False, independent_cleanup_verified=False, real_inference=False,
                    predecessor=old_name, predecessor_zip_sha256=old_zip, predecessor_exe_sha256=old_exe,
                    exe_sha256=digest(raw), exe_size=len(raw), payload_zip_sha256=payload_sha,
                    payload_index_sha256=index_sha, payload_files=index["files"], expanded_bytes=37359038,
                    payload_added=[], payload_replaced=[], payload_omitted=[], exact_embedded_resources_verified=True,
                    inert_regressions_passed=True,
                    source_files=[dict(path=p, size=len(b), sha256=digest(b)) for p, b in sorted(files.items())])
    entries = {"MayaProtectedPython.exe": raw, "package-manifest.json": json_bytes(manifest)}
    for path, contents in entries.items():
        write(build / name / path, contents)
    archive = build / (name + ".zip")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for path, contents in entries.items():
            z.writestr(name + "/" + path, contents)
    with zipfile.ZipFile(archive) as z:
        require(len(z.namelist()) == 2 and all(z.read(name + "/" + p) == b for p, b in entries.items()), "sealed archive")
    checks = [dict(name=p.name, size=p.stat().st_size, sha256=digest(p.read_bytes())) for p in (archive, exe)]
    write(build / "checksums.json", json_bytes(checks))
    for r in checks:
        pinned(build / r["name"], r["sha256"], r["size"])
    print(json_bytes(checks).decode(), end="")


if __name__ == "__main__":
    main()
