"""Compile, verify and seal the approved diagnostic successor without running it."""

import json
import os
from pathlib import Path
import re
import struct
import zipfile

from assemble_maya_journal_access_1 import (
    ROOT, BUILD as BASE, FLAGS, digest, json_bytes, pinned, predecessor, require, run, write,
)


BUILD = BASE.with_name("maya-journal-access-20261110-2")
NAME = "Maya-Journal-Access-2"
OLD = "Maya-Journal-Access-1"
VERSION = "0.2.2-journal-access.2"
FILE_VERSION = "0.2.2.2"
REVIEW = "docs/architecture/maya_journal_access_2_package_review.md"
CHECK = "scripts/maya_journal_access_offline_check.cs"
FIXTURE = "tests/windows_journal_access_profile_fixtures.cs"
PROFILE_TEST = "tests/check_windows_journal_access_profile.ps1"
NATIVE_TEST = ".codex-build/maya-journal-token-access-native-inert-20261110/check.ps1"
JOURNAL_TEST = ".codex-build/maya-coordinator-journal-inert-20261109/check.ps1"
OLD_EXE = "3751980ddc1d1a3353f8b1bce226cc2572df0629c37cc3cc890006626ac22257"
OLD_ZIP = "30bc1e1110877e72f116dd35292aca5eda8ab2a66dbd63fa0d4c4cdf86febd1d"
OLD_MANIFEST = "4ca51d22855217de1e490dfc1447a87611870622bd5e90438d683c697e308f3b"
ZIP_RESOURCE = "journal-access-payload.zip"
INDEX_RESOURCE = "journal-access-payload-index.json"


def verify_base():
    predecessor()
    executable = pinned(BASE / "MayaProtectedPython.exe", OLD_EXE)
    pinned(BASE / (OLD + ".zip"), OLD_ZIP)
    manifest_raw = pinned(BASE / OLD / "package-manifest.json", OLD_MANIFEST)
    with zipfile.ZipFile(BASE / (OLD + ".zip")) as archive:
        require(archive.read(OLD + "/package-manifest.json") == manifest_raw and
                archive.read(OLD + "/MayaProtectedPython.exe") == executable, "predecessor package parity")
    manifest = json.loads(manifest_raw)
    require(len(manifest["source_files"]) == 52 and manifest["sealed"] is True, "predecessor source inventory")
    for row in manifest["source_files"]:
        pinned(BASE / "source-freeze" / row["path"], row["sha256"], row["size"])
    return manifest


def update_literals(raw, changes):
    for old, new, count in changes:
        require(raw.count(old) == count, "version literal count")
        raw = raw.replace(old, new)
    return raw


def main():
    require(not BUILD.exists(), "refuse build overwrite")
    old = verify_base()
    review = pinned(ROOT / REVIEW, "8be6fe57a989967c11f08a6c7fd721fff383392cf8a46c60e0484cac99e41bfe")
    changes = dict(re.findall(r"\| `([\w.]+\.cs)` \| `([a-f0-9]{64})`", review.decode()))
    require(set(changes) == {"JournalAccessRuntime.cs", "JournalTokenAccessFixture.cs",
                             "JournalTokenAccessNativeFixture.cs"}, "exact diagnostic source paths")
    approved_index = "62340398b3c9776384de448b05464256aa65b68fb9903e5963498a42a22a7455"
    approved_payload = "3a96765a0cdc077907a96870bca536a21dfabecec34a701b956ad996188c11d0"
    require(old["payload_index_sha256"] == approved_index and old["payload_zip_sha256"] == approved_payload,
            "reviewed resource pins")
    payload = pinned(BASE / ZIP_RESOURCE, approved_payload)
    index_bytes = pinned(BASE / INDEX_RESOURCE, approved_index)
    index = json.loads(index_bytes)
    require(index["files"] == old["payload_files"] and index["zip_sha256"] == approved_payload and
            len(index["files"]) == 892 and sum(r["size"] for r in index["files"]) == 37359018, "payload inventory")
    with zipfile.ZipFile(BASE / ZIP_RESOURCE) as archive:
        names = archive.namelist()
        require(len(names) == len({n.casefold() for n in names}) == 892 and
                set(names) == {r["path"] for r in index["files"]}, "resource inventory")
        for row in index["files"]:
            raw = archive.read(row["path"])
            require(len(raw) == row["size"] and digest(raw) == row["sha256"], row["path"])

    sources = {}
    working = {}
    for row in old["source_files"]:
        name = row["path"]
        if not name.startswith("src/project_maya/windows_runtime/"):
            continue
        leaf = Path(name).name
        expected = changes.get(leaf, row["sha256"])
        raw = pinned(ROOT / name, expected)
        working[name] = expected
        if leaf == "ProtectedPython.cs":
            raw = update_literals(raw, [(b'"0.2.2.1"', b'"0.2.2.2"', 1),
                                       (b'"0.2.2-journal-access.1"', b'"0.2.2-journal-access.2"', 2)])
        sources[name] = raw
    compile_names = sorted(n for n in sources if n.endswith(".cs"))
    require(len(compile_names) == 44 and len(sources) == 47, "source inventory")
    checker_original = next(r["sha256"] for r in old["source_files"] if r["path"] == CHECK)
    checker = update_literals(pinned(ROOT / CHECK, checker_original),
                              [(b'"0.2.2.1"', b'"0.2.2.2"', 1),
                               (b'"0.2.2-journal-access.1"', b'"0.2.2-journal-access.2"', 1)])
    fixture_hash = "4f7abfa509d063efd56b02b4e12a84b6c6aa09bfa0e178dd4fabbb8601e184e0"
    sources.update({CHECK: checker, REVIEW: review, FIXTURE: pinned(ROOT / FIXTURE, fixture_hash)})
    for name in (PROFILE_TEST, NATIVE_TEST, JOURNAL_TEST, "scripts/assemble_maya_journal_access_1.py",
                 Path(__file__).relative_to(ROOT).as_posix()):
        sources[name] = (ROOT / name).read_bytes()
    BUILD.mkdir()
    freeze = BUILD / "source-freeze"
    for name, raw in sorted(sources.items()):
        write(freeze / name, raw)
    write(BUILD / ZIP_RESOURCE, payload)
    write(BUILD / INDEX_RESOURCE, index_bytes)
    csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    refs = "/reference:System.Windows.Forms.dll,System.Drawing.dll,System.Web.Extensions.dll,System.IO.Compression.dll,System.IO.Compression.FileSystem.dll"
    common = [csc, "/nologo", "/warnaserror+", "/optimize+", "/platform:x64", "/define:" + FLAGS, refs]
    exe = BUILD / "MayaProtectedPython.exe"
    compile_paths = [freeze / n for n in compile_names]
    run(common + ["/target:winexe", "/main:ProjectMaya.WindowsRuntime.ProtectedPython", "/out:" + str(exe),
                  f"/resource:{BUILD / ZIP_RESOURCE},MayaPython.payload.zip",
                  f"/resource:{BUILD / INDEX_RESOURCE},MayaPython.payload-index.json"] + compile_paths)
    raw = exe.read_bytes()
    pe = struct.unpack_from("<I", raw, 60)[0]
    require(raw[:2] == b"MZ" and raw[pe:pe+6] == b"PE\0\0\x64\x86" and
            struct.unpack_from("<H", raw, pe+24)[0] == 0x20B and struct.unpack_from("<H", raw, pe+92)[0] == 2, "x64 GUI PE")
    for role in ("worker", "child"):
        require(f"journal_access_{role}_entry.py".encode("utf-16le") in raw, "fixed selector")
    inspect = BUILD / "JournalAccessOfflineCheck.exe"
    run(common + ["/target:exe", "/main:JournalAccessOfflineCheck", "/out:" + str(inspect), freeze / CHECK] + compile_paths)
    run([inspect, exe, BUILD / INDEX_RESOURCE, BUILD / ZIP_RESOURCE])
    active_fixture = BUILD / "JournalAccessActiveFixture.exe"
    run(common + ["/target:exe", "/main:JournalAccessProfileFixtures", "/out:" + str(active_fixture), freeze / FIXTURE] + compile_paths)
    run([active_fixture])
    for name in (PROFILE_TEST, NATIVE_TEST, JOURNAL_TEST):
        pinned(ROOT / name, digest(sources[name]))
        run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ROOT / name])
        pinned(ROOT / name, digest(sources[name]))
    require(verify_base() == old, "preserve predecessor")
    for name, sha in working.items():
        pinned(ROOT / name, sha)
    for name, frozen in sources.items():
        pinned(freeze / name, digest(frozen), len(frozen))
    pinned(ROOT / FIXTURE, fixture_hash)
    pinned(exe, digest(raw), len(raw))

    manifest = dict(schema="maya.journal_access.offline_package.v1", artifact=NAME, version=VERSION, file_version=FILE_VERSION,
                    scope=old["scope"], defines=FLAGS.split(","), sealed=True, assembly_approved=True,
                    native_run_approved=False, native_execution_performed=False, real_inference=False,
                    independent_cleanup_verified=False, containment_qualified=False, production_qualified=False,
                    predecessor=OLD, predecessor_zip_sha256=OLD_ZIP, predecessor_exe_sha256=OLD_EXE,
                    exe_sha256=digest(raw), exe_size=len(raw), payload_zip_sha256=approved_payload,
                    payload_index_sha256=approved_index, payload_files=index["files"], expanded_bytes=37359018,
                    payload_added=[], payload_replaced=[], payload_omitted=[], exact_embedded_resources_verified=True,
                    inert_regressions_passed=True,
                    source_files=[dict(path=n, size=len(b), sha256=digest(b)) for n, b in sorted(sources.items())])
    entries = {"MayaProtectedPython.exe": raw, "package-manifest.json": json_bytes(manifest)}
    for name, contents in entries.items():
        write(BUILD / NAME / name, contents)
    archive_path = BUILD / (NAME + ".zip")
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, contents in sorted(entries.items()):
            archive.writestr(NAME + "/" + name, contents)
    with zipfile.ZipFile(archive_path) as archive:
        require(set(archive.namelist()) == {NAME + "/" + n for n in entries}, "sealed archive inventory")
        for name, contents in entries.items():
            require(archive.read(NAME + "/" + name) == contents, "sealed archive parity")
    checksums = [dict(name=f.name, size=f.stat().st_size, sha256=digest(f.read_bytes())) for f in (archive_path, exe)]
    write(BUILD / "checksums.json", json_bytes(checksums))
    for row in checksums:
        pinned(BUILD / row["name"], row["sha256"], row["size"])
    print(json_bytes(checksums).decode("ascii"), end="")


if __name__ == "__main__":
    main()
