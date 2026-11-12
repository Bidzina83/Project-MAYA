"""Build the standalone comparison without running its native entry point."""
import json
import os
from pathlib import Path
import re
import struct
import zipfile

from assemble_maya_journal_access_1 import ROOT, digest, json_bytes, pinned, require, run, write


def main():
    builds = ROOT / ".codex-build"
    base = builds / "maya-journal-delete-child-3"
    out = builds / "maya-delete-child-acl-comparison-1-sealed"
    name = "Maya-Journal-Delete-Child-3"
    require(not out.exists(), "refuse overwrite")
    manifest = pinned(base / name / "package-manifest.json",
                      "9c184a6109535db79a440f60ba987994d9cfbc5ee3c3f279d07cb2a46d3ddfe6")
    old = json.loads(manifest)

    def verify_old():
        archive = base / (name + ".zip")
        pinned(archive, "0c42914e80aabcef5730d4847e2607b2540808ffddfb4d2e6e71603df79d85cb")
        exe = pinned(base / "MayaProtectedPython.exe",
                     "eaa12204de289dae30de343b5c1d8db1665327dd41cb1d64a59c8c3962095715")
        with zipfile.ZipFile(archive) as z:
            require(z.read(name + "/package-manifest.json") == manifest and
                    z.read(name + "/MayaProtectedPython.exe") == exe, "predecessor archive parity")
        require(len(old["source_files"]) == 64, "predecessor inventory")
        for r in old["source_files"]:
            pinned(base / "source-freeze" / r["path"], r["sha256"], r["size"])

    verify_old()
    review_path = "docs/architecture/maya_delete_child_acl_comparison_assembly_review.md"
    review = (ROOT / review_path).read_bytes()
    pins = dict(re.findall(r"\| `([\w.]+\.cs)` \| `([a-f0-9]{64})`", review.decode()))
    prefix = "src/project_maya/windows_runtime/"
    files = {r["path"]: pinned(base / "source-freeze" / r["path"], r["sha256"], r["size"])
             for r in old["source_files"] if r["path"].startswith(prefix) and r["path"].endswith(".cs")}
    require(len(files) == 53, "runtime source inventory")
    native = "tests/windows_delete_child_acl_comparison_native.cs"
    fixture = "tests/windows_delete_child_acl_comparison_fixtures.cs"
    changed = [prefix + n for n in ("DeleteChildAclCollector.cs", "DeleteChildAclComparison.cs",
                                   "DeleteChildAclExpectedPolicy.cs", "DeleteChildControlCreate.cs")]
    require(set(pins) == {Path(n).name for n in [*changed, native, fixture]}, "reviewed pins")
    for n in [*changed, native, fixture]:
        files[n] = pinned(ROOT / n, pins[Path(n).name])
    runtime = sorted(n for n in files if n.startswith(prefix))
    require(len(runtime) == 56, "exact compile inputs")
    files[review_path] = review
    metadata = "scripts/maya_acl_comparison_metadata_check.cs"
    for p in (metadata, "scripts/assemble_maya_journal_access_1.py", Path(__file__).relative_to(ROOT).as_posix()):
        files[p] = (ROOT / p).read_bytes()
    out.mkdir()
    freeze = out / "source-freeze"
    for p, b in files.items():
        write(freeze / p, b)
    flags = "MAYA_DELETE_CHILD_ACL_COMPARISON_INERT,HERMES_JOURNAL_DELETE_CHILD_SOURCE,HERMES_BRIDGE,HERMES_CONSTRUCTION,HERMES_IMPORT"
    csc = Path(os.environ["WINDIR"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    refs = "/reference:System.Windows.Forms.dll,System.Drawing.dll,System.Web.Extensions.dll,System.IO.Compression.dll,System.IO.Compression.FileSystem.dll"
    common = [csc, "/nologo", "/warnaserror+", "/optimize+", "/platform:x64", "/target:exe", "/define:" + flags, refs]
    sources = [freeze / n for n in runtime]
    exe = out / "MayaDeleteChildAclComparison.exe"
    test = out / "AclComparisonInertChecks.exe"
    for dest, cls, source in [(exe, "DeleteChildAclComparisonNative", native),
                              (test, "DeleteChildAclComparisonFixtures", fixture)]:
        run(common + ["/main:" + cls, "/out:" + str(dest), freeze / source] + sources)
    run([test])
    raw = exe.read_bytes()
    pe = struct.unpack_from("<I", raw, 60)[0]
    require(raw[:2] == b"MZ" and raw[pe:pe+6] == b"PE\0\0\x64\x86" and
            struct.unpack_from("<H", raw, pe+24)[0] == 0x20b and struct.unpack_from("<H", raw, pe+92)[0] == 3,
            "x64 console PE")
    # Reflection-only inspection resolves the managed entry point and resources without executing the assembly.
    metadata_exe = out / "AclComparisonMetadataCheck.exe"
    run(common + ["/out:" + str(metadata_exe), freeze / metadata])
    run([metadata_exe, exe])
    verify_old()
    for p, b in files.items():
        pinned(freeze / p, digest(b), len(b))
    pinned(exe, digest(raw), len(raw))
    receipt = dict(executable=exe.name, sha256=digest(raw), size=len(raw), entry_point="DeleteChildAclComparisonNative",
                   embedded_resources=0, defines=flags.split(","), inert_checks_passed=True,
                   native_run_approved=False, native_execution_performed=False, containment_qualified=False,
                   source_files=[dict(path=p, sha256=digest(b), size=len(b)) for p, b in sorted(files.items())])
    write(out / "build-receipt.json", json_bytes(receipt))
    print(exe.name, receipt["sha256"], len(raw))


if __name__ == "__main__":
    main()
