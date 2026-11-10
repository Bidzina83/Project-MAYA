"""Verify the staged diagnostic with inert fixtures, then seal it offline."""

import json
from pathlib import Path
import sys
import zipfile

from assemble_maya_journal_access_1 import (
    BUILD, NAME, ROOT, digest, json_bytes, pinned, predecessor, require, run, write,
)


def main():
    receipt = json.loads((BUILD / "staging-receipt.json").read_bytes())
    exe = BUILD / "MayaProtectedPython.exe"
    index = BUILD / "journal-access-payload-index.json"
    payload = BUILD / "journal-access-payload.zip"
    package = BUILD / NAME
    archive_path = BUILD / (NAME + ".zip")
    require(not package.exists() and not archive_path.exists() and not (BUILD / "checksums.json").exists(),
            "refuse overwrite of sealed build")
    require(receipt["artifact"] == NAME and receipt["exact_embedded_resources_verified"] is True and
            receipt["native_execution_performed"] is False, "valid staging receipt")
    pinned(exe, receipt["exe_sha256"], receipt["exe_size"])
    pinned(index, receipt["payload_index_sha256"])
    pinned(payload, receipt["payload_zip_sha256"])
    for row in receipt["source_files"]:
        pinned(BUILD / "source-freeze" / row["path"], row["sha256"], row["size"])
        pinned(ROOT / row["path"], row["sha256"], row["size"])

    tests = [
        "tests/check_windows_journal_access_profile.ps1",
        ".codex-build/maya-journal-access-python-parity-20261110/check.ps1",
        ".codex-build/maya-journal-token-access-native-inert-20261110/check.ps1",
        ".codex-build/maya-coordinator-journal-inert-20261109/check.ps1",
    ]
    for test in tests:
        run(["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ROOT / test])
    python_tests = [
        "tests/test_final_output_inert.py",
        "tests/test_model_final_eager_import_inert.py",
        "tests/test_model_final_text_inert.py",
        "tests/test_model_final_guard_diagnostics_inert.py",
    ]
    run([sys.executable, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *python_tests])
    run([BUILD / "JournalAccessOfflineCheck.exe", exe, index, payload])
    predecessor()

    test_records = []
    for name in [*tests, *python_tests, Path(__file__).relative_to(ROOT).as_posix()]:
        raw = (ROOT / name).read_bytes()
        write(BUILD / "verification-freeze" / name, raw)
        test_records.append(dict(path=name, size=len(raw), sha256=digest(raw)))
    receipt["inert_verification_inputs"] = test_records
    receipt["inert_regressions_passed"] = True
    receipt["sealed"] = True
    product = pinned(exe, receipt["exe_sha256"], receipt["exe_size"])
    manifest = json_bytes(receipt)
    files = {"MayaProtectedPython.exe": product, "package-manifest.json": manifest}
    for name, raw in files.items():
        write(package / name, raw)
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            archive.writestr(NAME + "/" + name, raw)
    with zipfile.ZipFile(archive_path) as archive:
        require(set(archive.namelist()) == {NAME + "/" + name for name in files}, "sealed archive inventory")
        for name, raw in files.items():
            require(archive.read(NAME + "/" + name) == raw, "sealed archive parity: " + name)
    checksums = [dict(name=f.name, size=f.stat().st_size, sha256=digest(f.read_bytes()))
                 for f in (archive_path, exe)]
    write(BUILD / "checksums.json", json_bytes(checksums))
    for row in checksums:
        pinned(BUILD / row["name"], row["sha256"], row["size"])
    print(json_bytes(checksums).decode("ascii"), end="")


if __name__ == "__main__":
    main()
