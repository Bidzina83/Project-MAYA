"""Read-only startup inventory. Never imports Hermes or enables capabilities."""

import ast
import ctypes
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import struct
import tomllib
import xml.etree.ElementTree as ET

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / ".codex-build/governance-v2-lpac-stage"
OUTPUT = ROOT / ".codex-build/gate-a-startup-diagnostics/startup-inventory.json"


def manifest_summary(raw):
    if b"<!doctype" in raw.lower() or b"<!entity" in raw.lower():
        raise ValueError("inventory.unsupported_xml")
    node = ET.fromstring(raw)
    return {
        "dependencies": [dict(n.attrib) for n in node.findall(
            ".//{urn:schemas-microsoft-com:asm.v1}dependentAssembly/"
            "{urn:schemas-microsoft-com:asm.v1}assemblyIdentity")],
        "execution_levels": [dict(n.attrib) for n in node.findall(
            ".//{urn:schemas-microsoft-com:asm.v3}requestedExecutionLevel")],
    }


class ImageReader:
    def __init__(self):
        if os.name != "nt":
            raise ValueError("inventory.windows_required")
        import win32api
        self.api = win32api
        self.dbg = ctypes.WinDLL(str(Path(os.environ["SystemRoot"]) / "System32/dbghelp.dll"))
        self.dbg.ImageNtHeader.argtypes = [ctypes.c_void_p]
        self.dbg.ImageNtHeader.restype = ctypes.c_void_p
        self.dbg.ImageDirectoryEntryToData.argtypes = [ctypes.c_void_p, ctypes.c_ubyte,
            ctypes.c_ushort, ctypes.POINTER(ctypes.c_uint32)]
        self.dbg.ImageDirectoryEntryToData.restype = ctypes.c_void_p
        self.dbg.ImageRvaToVa.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
                                        ctypes.c_void_p]
        self.dbg.ImageRvaToVa.restype = ctypes.c_void_p

    def read(self, path):
        # Resource-only exclusive mapping: neither DllMain nor artifact code runs.
        handle = self.api.LoadLibraryEx(str(path), 0, 0x60)
        try:
            if not handle & 3:
                raise ValueError("inventory.executable_mapping_refused")
            base, image = handle & ~3, bool(handle & 2)
            nt = self.dbg.ImageNtHeader(base)
            if not nt:
                raise ValueError("inventory.invalid_pe")
            machine = ctypes.c_ushort.from_address(nt + 4).value
            magic = ctypes.c_ushort.from_address(nt + 24).value
            if magic == 0x20b:
                preferred_base = ctypes.c_uint64.from_address(nt + 48).value
            elif magic == 0x10b:
                preferred_base = ctypes.c_uint32.from_address(nt + 52).value
            else:
                raise ValueError("inventory.invalid_optional_header")

            def dll_name(rva):
                if not 0 < rva < 0xffffffff:
                    raise ValueError("inventory.invalid_name_rva")
                pointer = base + rva if image else self.dbg.ImageRvaToVa(nt, base, rva, None)
                if not pointer:
                    raise ValueError("inventory.invalid_name_pointer")
                value = ctypes.string_at(pointer).decode("ascii")
                if len(value) > 260 or "/" in value or "\\" in value:
                    raise ValueError("inventory.invalid_dll_name")
                return value.lower()

            imports, delayed = [], []
            for directory, stride, destination in ((1, 20, imports), (13, 32, delayed)):
                size = ctypes.c_uint32()
                pointer = self.dbg.ImageDirectoryEntryToData(base, image, directory, ctypes.byref(size))
                if not pointer:
                    continue
                if size.value > stride * 4096 or size.value < stride:
                    raise ValueError("inventory.invalid_directory_size")
                for offset in range(0, size.value - stride + 1, stride):
                    words = struct.unpack("<" + "I" * (stride // 4),
                                          ctypes.string_at(pointer + offset, stride))
                    if not any(words):
                        break
                    if directory == 1:
                        rva = words[3]
                    else:
                        rva = words[1] if words[0] & 1 else words[1] - preferred_base
                    destination.append(dll_name(rva))
                else:
                    raise ValueError("inventory.unterminated_directory")
            manifests = []
            try:
                names = self.api.EnumResourceNames(handle, 24)
            except self.api.error as error:
                if error.winerror not in {1812, 1813, 1814}:
                    raise
                names = []
            for name in names:
                for language in self.api.EnumResourceLanguages(handle, 24, name):
                    raw = self.api.LoadResource(handle, 24, name, language)
                    manifests.append({"id": name, "language": language,
                                      "sha256": hashlib.sha256(raw).hexdigest(),
                                      **manifest_summary(raw)})
            return {"machine": machine, "imports": sorted(set(imports)),
                    "delay_imports": sorted(set(delayed)), "manifests": manifests}
        finally:
            self.api.FreeLibrary(handle)


def main():
    raw_manifest = (STAGE / "runtime-manifest.json").read_bytes()
    manifest = json.loads(raw_manifest)
    if manifest["patches_applied"] or manifest["pin"] != "b13e2fd6948a59eeb59fe618914147d97a2ee90a":
        raise ValueError("inventory.invalid_runtime")
    reader, images = ImageReader(), []
    for record in manifest["files"]:
        path = (STAGE / record["path"]).resolve()
        if not path.is_relative_to((STAGE / "runtime").resolve()):
            raise ValueError("inventory.path_escape")
        if hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            raise ValueError("inventory.changed_artifact")
        if path.suffix.lower() in {".exe", ".dll", ".pyd"}:
            images.append({"path": record["path"], "sha256": record["sha256"], **reader.read(path)})
    installed, distributions = {}, {}
    for distribution in importlib.metadata.distributions(path=[str(STAGE / "runtime/dependencies")]):
        name = distribution.metadata["Name"]
        if name:
            normalized = canonicalize_name(name)
            installed[normalized] = distribution.version
            distributions[normalized] = distribution
    project = tomllib.loads((STAGE / "runtime/hermes/pyproject.toml").read_text(encoding="utf-8"))["project"]
    requirements = []
    for text in project["dependencies"]:
        req = Requirement(text)
        if req.marker and not req.marker.evaluate({"extra": ""}):
            continue
        version = installed.get(canonicalize_name(req.name))
        requirements.append({"name": req.name, "specifier": str(req.specifier),
            "installed": version, "matches": version is not None and req.specifier.contains(version),
            "extras": sorted(req.extras), "direct_url": bool(req.url)})
    pending = [(r["name"], set(r["extras"])) for r in requirements]
    selected, edges = {}, {}
    while pending:
        name, extras = pending.pop()
        name = canonicalize_name(name)
        if name in selected and extras.issubset(selected[name]):
            continue
        selected.setdefault(name, set()).update(extras)
        distribution = distributions.get(name)
        if distribution is None:
            continue
        for text in distribution.requires or []:
            req = Requirement(text)
            if req.marker and not any(req.marker.evaluate({"extra": extra})
                                     for extra in selected[name] | {""}):
                continue
            dependency = canonicalize_name(req.name)
            version = installed.get(dependency)
            edges[(name, dependency, str(req.specifier))] = {
                "parent": name, "dependency": dependency, "specifier": str(req.specifier),
                "installed": version, "matches": version is not None and req.specifier.contains(version),
                "direct_url": bool(req.url), "extras": sorted(req.extras)}
            pending.append((dependency, set(req.extras)))
    source_imports = {}
    for relative in ("run_agent.py", "agent/agent_init.py", "model_tools.py", "hermes_logging.py",
                     "hermes_bootstrap.py", "hermes_state.py", "agent/memory_manager.py"):
        path = STAGE / "runtime/hermes" / relative
        tree = ast.parse(path.read_text(encoding="utf-8"))
        source_imports[relative] = sorted({node.module for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module} | {
            alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names})
    names = sorted({name for image in images for name in image["imports"] + image["delay_imports"]})
    lookup = {}
    for name in names:
        lookup[name] = {"staged_candidates": [i["path"] for i in images if Path(i["path"]).name.lower() == name],
            "system32_exists": (Path(os.environ["SystemRoot"]) / "System32" / name).is_file(),
            "api_set_contract": name.startswith(("api-ms-", "ext-ms-"))}
    report = {"schema": "maya.gate_a.startup_inventory.v1", "production_qualified": False,
        "inspection_only": True, "runtime_code_executed": False,
        "runtime_manifest_sha256": hashlib.sha256(raw_manifest).hexdigest(),
        "pin": manifest["pin"], "native_images": images, "import_candidates": lookup,
        "installed_distributions": installed, "hermes_python_requirement": project["requires-python"],
        "core_requirements": requirements, "source_import_inventory": source_imports,
        "transitive_requirements": list(edges.values()),
        "selected_extras": {name: sorted(extras) for name, extras in selected.items()},
        "limitations": ["not loader resolution proof", "metadata is not import/file closure",
                        "not dynamic import proof", "not LPAC allowed-operation qualification"]}
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "inspected", "native_image_count": len(images),
        "distribution_count": len(installed), "unsatisfied_core": [r for r in requirements if not r["matches"]],
        "unsatisfied_transitive": [r for r in edges.values() if not r["matches"]],
        "manifest_images": [i["path"] for i in images if i["manifests"]], "production_qualified": False}))


if __name__ == "__main__":
    main()
