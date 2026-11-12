"""Build the standalone comparison without running its native entry point."""
import json
import os
from pathlib import Path
import re
import struct

from assemble_maya_journal_access_1 import ROOT, digest, json_bytes, pinned, require, run, write


def main():
    builds = ROOT / ".codex-build"
    base = builds / "maya-delete-child-acl-comparison-1-sealed"
    out = builds / "maya-delete-child-acl-comparison-2-sealed"
    require(not out.exists(), "refuse overwrite")
    old = json.loads(pinned(base / "build-receipt.json",
        "207eb8391d890aed6f2304139e88dc8c8af648182ae323e981ad1e51568d27fc"))

    def verify_old():
        pinned(base / old["executable"], old["sha256"], old["size"])
        require(len(old["source_files"]) == 62, "predecessor inventory")
        for r in old["source_files"]:
            pinned(base / "source-freeze" / r["path"], r["sha256"], r["size"])

    verify_old()
    review_path = "docs/architecture/maya_delete_child_acl_comparison_2_assembly_review.md"
    review = (ROOT / review_path).read_bytes()
    pins = dict(re.findall(r"\| `([\w.]+\.cs)` \| `([a-f0-9]{64})`", review.decode()))
    prefix = "src/project_maya/windows_runtime/"
    native = "tests/windows_delete_child_acl_comparison_native.cs"
    fixture = "tests/windows_delete_child_acl_comparison_fixtures.cs"
    metadata = "scripts/maya_acl_comparison_metadata_check.cs"
    changed = {prefix + n for n in ("DeleteChildAclCollector.cs", "DeleteChildAclComparison.cs",
                                   "DeleteChildAclExpectedPolicy.cs")} | {fixture}
    require(set(pins) == {Path(n).name for n in changed}, "reviewed pins")
    files = {}
    for r in old["source_files"]:
        path = r["path"]
        if path in changed:
            files[path] = pinned(ROOT / path, pins[Path(path).name])
        elif path.startswith(prefix) or path in (native, metadata):
            files[path] = pinned(base / "source-freeze" / path, r["sha256"], r["size"])
    runtime = sorted(n for n in files if n.startswith(prefix))
    require(len(runtime) == 56 and changed <= files.keys(), "exact compile inputs")
    files[review_path] = review
    for p in ("scripts/assemble_maya_journal_access_1.py", Path(__file__).relative_to(ROOT).as_posix()):
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
