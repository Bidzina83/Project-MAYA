"""Approved offline build; only inert fixture executables are run."""
import json
import os
from pathlib import Path
import struct
import zipfile

from assemble_maya_journal_access_1 import ROOT, digest, json_bytes, pinned, require, run, write
from assemble_maya_journal_access_2 import BUILD as BASE, NAME as OLD


def main():
    name = "Maya-Journal-Delete-Child-1"
    build = BASE.with_name("maya-journal-delete-child-1")
    old_manifest = BASE / OLD / "package-manifest.json"
    old_raw = old_manifest.read_bytes()
    old = json.loads(old_raw)
    zip_pin = "b889a78290d155373b0850494810e9106ea3ac0a2baafe5112666843b3d2b75d"
    exe_pin = "94a6ff79c85c5210b684f0ebc613b3a59eadde5a94fcb034c80723acf1ec2694"

    def verify_old():
        pinned(BASE / (OLD + ".zip"), zip_pin)
        pinned(BASE / "MayaProtectedPython.exe", exe_pin)
        with zipfile.ZipFile(BASE / (OLD + ".zip")) as z:
            require(z.read(OLD + "/package-manifest.json") == old_raw, "sealed manifest")
        for row in old["source_files"]:
            pinned(BASE / "source-freeze" / row["path"], row["sha256"], row["size"])

    verify_old()
    payload = BASE / "journal-access-payload.zip"
    index = json.loads(pinned(BASE / "journal-access-payload-index.json", old["payload_index_sha256"]))
    pinned(payload, old["payload_zip_sha256"])
    require(index["files"] == old["payload_files"], "baseline inventory")
    omit = {"journal_access_child_entry.py", "journal_access_worker_entry.py"}
    with zipfile.ZipFile(payload) as z:
        require(len(z.namelist()) == len(index["files"]) == 892 and
                set(z.namelist()) == {r["path"] for r in index["files"]}, "baseline paths")
        data = {}
        for r in index["files"]:
            raw = z.read(r["path"])
            require(len(raw) == r["size"] and digest(raw) == r["sha256"], r["path"])
            if r["path"] not in omit:
                data[r["path"]] = raw
    prefix = "src/project_maya/windows_runtime/"
    entry = "journal_delete_child_entry.py"
    data[entry] = pinned(ROOT / (prefix + entry), "c416ddd8009e385f9b8e3666992f0ebb1b1a6e98aeee533a353caf6bd71d4f72")
    require(len(data) == len({n.casefold() for n in data}) == 891 and
            sum(map(len, data.values())) == 37359038, "reviewed payload")
    changed = set("CoordinatorJournalCandidate CoordinatorJournalDescriptor CoordinatorJournalNativeTransport ProductFiles ProtectedPython WindowsBridgeProcess WindowsIsolation".split())
    files = {}
    for r in old["source_files"]:
        n = r["path"]
        if n.startswith(prefix) and n.endswith(".cs"):
            files[n] = (ROOT / n).read_bytes() if Path(n).stem in changed else pinned(ROOT / n, r["sha256"])
    require(len(files) == 44, "predecessor compile inventory")
    for suffix in "ControlCreate ControlDescriptor ControlLease ControlOwner ControlProvision ControlWindowsHandle Exchange Probe Reply".split():
        n = prefix + "DeleteChild" + suffix + ".cs"
        files[n] = (ROOT / n).read_bytes()
    require(len(files) == 53, "successor compile inventory")
    compile_names = sorted(files)
    checker = "scripts/maya_journal_access_offline_check.cs"
    checker_bytes = (BASE / "source-freeze" / checker).read_bytes()
    for a, b in [(b"==892", b"==891"), (b"0.2.2-journal-access.2", b"0.2.3-journal-delete-child.1"),
                 (b"offline-journal-access-matrix-v1", b"offline-journal-delete-child-control-v1"),
                 (b"0.2.2.2", b"0.2.3.1"), (b".JournalAccessRuntime\")!=null", b".DeleteChildControlProvision\")!=null")]:
        require(checker_bytes.count(a) == 1, "checker literal")
        checker_bytes = checker_bytes.replace(a, b)
    fixture = "tests/windows_delete_child_control_descriptor_fixtures.cs"
    py_fixture = "tests/test_journal_delete_child_entry_inert.py"
    legacy = "tests/check_windows_journal_access_profile.ps1"
    role_test = "tests/test_journal_access_role_inert.py"
    review = "docs/architecture/maya_journal_delete_child_package_review.md"
    recipe = Path(__file__).relative_to(ROOT).as_posix()
    files.update({n: (ROOT / n).read_bytes() for n in (fixture, py_fixture, legacy, role_test, review, recipe)})
    files.update({checker: checker_bytes, prefix + entry: data[entry], prefix + "journal_access_role.py": data["journal_access_role.py"]})
    build.mkdir()
    freeze = build / "source-freeze"
    for n, raw in files.items():
        write(freeze / n, raw)

    resource = build / "journal-delete-child-payload.zip"
    index_path = build / "journal-delete-child-payload-index.json"
    with zipfile.ZipFile(resource, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for n, b in sorted(data.items()):
            z.writestr(n, b)
    with zipfile.ZipFile(resource) as z:
        require(z.namelist() == sorted(data) and all(z.read(n) == b for n, b in data.items()), "payload readback")
    inventory = [dict(path=n, size=len(b), sha256=digest(b)) for n, b in sorted(data.items())]
    resource_sha = digest(resource.read_bytes())
    write(index_path, json_bytes(dict(python_version="3.13.14", zip_sha256=resource_sha, files=inventory)))
    flags = "HERMES_JOURNAL_DELETE_CHILD_SOURCE,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT"
    csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    common = [csc, "/nologo", "/warnaserror+", "/optimize+", "/platform:x64", "/define:" + flags,
              "/reference:System.Windows.Forms.dll,System.Drawing.dll,System.Web.Extensions.dll,System.IO.Compression.dll,System.IO.Compression.FileSystem.dll"]
    sources = [freeze / n for n in compile_names]
    exe = build / "MayaProtectedPython.exe"
    run(common + ["/target:winexe", "/main:ProjectMaya.WindowsRuntime.ProtectedPython", "/out:" + str(exe),
                  f"/resource:{resource},MayaPython.payload.zip", f"/resource:{index_path},MayaPython.payload-index.json"] + sources)
    raw = exe.read_bytes()
    pe = struct.unpack_from("<I", raw, 60)[0]
    require(raw[:2] == b"MZ" and raw[pe:pe+6] == b"PE\0\0\x64\x86" and
            struct.unpack_from("<H", raw, pe+92)[0] == 2 and entry.encode("utf-16le") in raw and
            "journal_access_child_entry.py".encode("utf-16le") not in raw, "x64 GUI and fixed selector")
    for cls, src, args in [("JournalAccessOfflineCheck", checker, [exe, index_path, resource]),
                           ("DeleteChildControlDescriptorFixtures", fixture, [])]:
        tool = build / (cls + ".exe")
        run(common + ["/target:exe", "/main:" + cls, "/out:" + str(tool), freeze / src] + sources)
        run([tool, *args])
    run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ROOT / legacy])
    import sys
    run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", py_fixture, role_test])
    verify_old()
    for n, b in files.items():
        pinned(freeze / n, digest(b), len(b))
    pinned(exe, digest(raw), len(raw))
    manifest = dict(artifact=name, version="0.2.3-journal-delete-child.1", file_version="0.2.3.1",
                    scope="offline-journal-delete-child-control-v1", defines=flags.split(","), sealed=True,
                    assembly_approved=True, native_run_approved=False, native_execution_performed=False,
                    production_qualified=False, containment_qualified=False, independent_cleanup_verified=False,
                    real_inference=False, predecessor=OLD, predecessor_zip_sha256=zip_pin,
                    exe_sha256=digest(raw), exe_size=len(raw), payload_zip_sha256=resource_sha,
                    payload_index_sha256=digest(index_path.read_bytes()), payload_files=inventory,
                    expanded_bytes=37359038, payload_added=[entry], payload_omitted=sorted(omit), payload_replaced=[],
                    exact_embedded_resources_verified=True, inert_regressions_passed=True,
                    source_files=[dict(path=n, size=len(b), sha256=digest(b)) for n, b in sorted(files.items())])
    entries = {"MayaProtectedPython.exe": raw, "package-manifest.json": json_bytes(manifest)}
    for n, b in entries.items():
        write(build / name / n, b)
    archive = build / (name + ".zip")
    with zipfile.ZipFile(archive, "x", compression=zipfile.ZIP_DEFLATED) as z:
        for n, b in entries.items():
            z.writestr(name + "/" + n, b)
    with zipfile.ZipFile(archive) as z:
        require(len(z.namelist()) == 2 and all(z.read(name + "/" + n) == b for n, b in entries.items()), "sealed package")
    checks = [dict(name=p.name, size=p.stat().st_size, sha256=digest(p.read_bytes())) for p in (archive, exe)]
    write(build / "checksums.json", json_bytes(checks))
    for r in checks:
        pinned(build / r["name"], r["sha256"], r["size"])
    print(json_bytes(checks).decode(), end="")


if __name__ == "__main__":
    main()
