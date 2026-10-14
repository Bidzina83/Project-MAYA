"""Read-only Gate A prerequisites; never creates profiles, ACLs or WFP filters."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
from pathlib import PurePosixPath


PIN = "b13e2fd6948a59eeb59fe618914147d97a2ee90a"
REQUIRED_APIS = {
    "kernel32": ("CreateProcessW", "UpdateProcThreadAttribute", "CreateJobObjectW",
                 "AssignProcessToJobObject", "SetInformationJobObject"),
    "userenv": ("CreateAppContainerProfile", "DeleteAppContainerProfile",
                "DeriveAppContainerSidFromAppContainerName"),
    "fwpuclnt": ("FwpmEngineOpen0", "FwpmEngineClose0", "FwpmFilterAdd0",
                 "FwpmFilterEnum0", "FwpmTransactionBegin0", "FwpmTransactionCommit0"),
    "advapi32": ("OpenProcessToken", "GetTokenInformation", "SetNamedSecurityInfoW"),
}


def validate_baseline(stage: Path) -> dict:
    manifest_bytes = (stage / "baseline-manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    if (manifest.get("pin") != PIN or manifest.get("patches_applied") is not False
            or manifest.get("packaging_changes") or manifest.get("production_qualified") is not False):
        raise ValueError("preflight.wrong_pin")
    expected_effective = [{k: item[k] for k in ("path", "mode", "sha256")}
                          for item in manifest["baseline_files"]]
    if expected_effective != manifest.get("effective_files"):
        raise ValueError("preflight.patched_inventory")
    source = (stage / "source").resolve()
    seen = set()
    for item in manifest["baseline_files"]:
        name = PurePosixPath(item["path"])
        if (name.is_absolute() or ".." in name.parts or "\\" in str(name)
                or ":" in str(name) or str(name) in seen):
            raise ValueError("preflight.invalid_inventory")
        seen.add(str(name))
        path = source.joinpath(*name.parts)
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError("preflight.invalid_source_path")
        data = path.read_bytes()
        blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
        if hashlib.sha256(data).hexdigest() != item["sha256"] or blob != item["git_blob"]:
            raise ValueError("preflight.source_changed")
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if actual != seen:
        raise ValueError("preflight.source_inventory_changed")
    return {"manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            "manifest": manifest}


def windows_prerequisites() -> dict:
    if os.name != "nt":
        return {"status": "blocked", "reason_code": "preflight.windows_required"}
    missing = []
    for library, names in REQUIRED_APIS.items():
        dll = ctypes.WinDLL(library, use_last_error=True)
        for name in names:
            if not hasattr(dll, name):
                missing.append(f"{library}.{name}")
    class Version(ctypes.Structure):
        _fields_ = [("size", wintypes.DWORD), ("major", wintypes.DWORD),
                    ("minor", wintypes.DWORD), ("build", wintypes.DWORD),
                    ("service_pack", wintypes.WCHAR * 128)]
    version = Version()
    version.size = ctypes.sizeof(version)
    ntdll = ctypes.WinDLL("ntdll")
    ntdll.RtlGetVersion.argtypes = [ctypes.POINTER(Version)]
    ntdll.RtlGetVersion.restype = ctypes.c_long
    if ntdll.RtlGetVersion(ctypes.byref(version)) != 0:
        raise OSError("preflight.version_unavailable")
    wfp = ctypes.WinDLL("fwpuclnt", use_last_error=True)
    wfp.FwpmEngineOpen0.argtypes = [wintypes.LPCWSTR, wintypes.DWORD,
                                  ctypes.c_void_p, ctypes.c_void_p,
                                  ctypes.POINTER(wintypes.HANDLE)]
    wfp.FwpmEngineOpen0.restype = wintypes.DWORD
    wfp.FwpmEngineClose0.argtypes = [wintypes.HANDLE]
    wfp.FwpmEngineClose0.restype = wintypes.DWORD
    engine = wintypes.HANDLE()
    # Opening a session queries engine availability; no filters are installed.
    code = wfp.FwpmEngineOpen0(None, 10, None, None, ctypes.byref(engine))
    if code == 0:
        close_code = wfp.FwpmEngineClose0(engine)
        if close_code:
            raise OSError("preflight.engine_close_failed")
    return {"status": "observed", "os_version":
            {"major": version.major, "minor": version.minor, "build": version.build},
            "missing_apis": missing, "wfp_engine_open_code": int(code),
            "wfp_provisioning_permission": "not_requested",
            "enforcement": "not_provisioned", "containment_qualified": False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    try:
        baseline = validate_baseline(args.baseline)
        report = {"status": "preflight_only", "production_qualified": False,
                  "baseline_manifest_sha256": baseline["manifest_sha256"],
                  "windows": windows_prerequisites(),
                  "remaining": ["provisioning_permission", "native_launcher",
                                "wfp_enforcement", "native_product_slice",
                                "A01-A20_qualification"]}
        print(json.dumps(report, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError):
        print(json.dumps({"status": "blocked", "reason_code": "preflight.failed",
                          "production_qualified": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
