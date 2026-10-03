"""Run native Hermes controls in a prepared offline environment, never install deps."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import tempfile
import shutil

from prepare_governance_baseline import CONTRACT, digest


# Loaded by the selected interpreter inside the native stage. It checks actual
# installed versions against the pinned resolution before importing native tests.
PREFLIGHT = r'''
import importlib.metadata as m, json, sys, tomllib
from pathlib import Path
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name as canonical
project=tomllib.loads(Path("pyproject.toml").read_text())["project"]
lock=tomllib.loads(Path("uv.lock").read_text())
versions={}
for p in lock["package"]:
    versions.setdefault(canonical(p["name"]),set()).add(p["version"])
required=list(project["dependencies"])
for extra in ("dev","messaging","anthropic"):
    required.extend(project["optional-dependencies"][extra])
missing=[]
for raw in required:
    r=Requirement(raw)
    if r.marker and not r.marker.evaluate(): continue
    try: v=m.version(r.name)
    except m.PackageNotFoundError: missing.append(canonical(r.name)); continue
    if v not in versions.get(canonical(r.name),set()) or v not in r.specifier:
        missing.append(canonical(r.name))
installed=[]
for d in m.distributions():
    raw_name=d.metadata.get("Name")
    if not raw_name:
        missing.append("environment.invalid_distribution_metadata")
        continue
    name=canonical(raw_name)
    installed.append({"name":name,"version":d.version})
    if name in versions and d.version not in versions[name]: missing.append(name)
print(json.dumps({"blocked_dependencies":sorted(set(missing)),
                  "installed":sorted(installed,key=lambda x:x["name"])}))
sys.exit(bool(missing))
'''

PLUGIN = r'''
import json, socket, ipaddress
from contextvars import ContextVar
from pathlib import Path
import pytest
_connect=socket.socket.connect
_connect_ex=socket.socket.connect_ex
_socketpair=socket.socketpair
_ipc=ContextVar("g0_socketpair",default=False)
def no_network(*args,**kwargs): raise RuntimeError("g0.network_forbidden")
def connect(sock,address):
    if _ipc.get() and isinstance(address,tuple) and ipaddress.ip_address(address[0]).is_loopback:
        return _connect(sock,address)
    return no_network()
def connect_ex(sock,address):
    if _ipc.get() and isinstance(address,tuple) and ipaddress.ip_address(address[0]).is_loopback:
        return _connect_ex(sock,address)
    return no_network()
def socketpair(*args,**kwargs):
    token=_ipc.set(True)
    try: return _socketpair(*args,**kwargs)
    finally: _ipc.reset(token)
socket.socket.connect=connect
socket.socket.connect_ex=connect_ex
socket.socketpair=socketpair
socket.create_connection=no_network
def pytest_sessionfinish(session,exitstatus):
    reporter=session.config.pluginmanager.get_plugin("terminalreporter")
    stats=reporter.stats if reporter else {}
    skipped=len(stats.get("skipped",[]))
    failed=len(stats.get("failed",[]))+len(stats.get("error",[]))
    passed=len(stats.get("passed",[]))
    if skipped or not passed: session.exitstatus=1
    import os
    Path(os.environ["G0_NATIVE_RESULT"]).write_text(json.dumps({"passed":passed,"failed":failed,
        "skipped":skipped,"exit_code":int(session.exitstatus),"production_qualified":False}))
'''


def clean_environment(home, python=None):
    env = {k: v for k, v in os.environ.items()
           if k.upper() in {"PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP"}}
    env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home),
               LOCALAPPDATA=str(home), HERMES_HOME=str(home / "hermes"),
               PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1",
               PYTEST_DISABLE_PLUGIN_AUTOLOAD="1", UV_OFFLINE="1")
    if python is not None and os.name == "posix":
        # Hosted Python can need its own shared library; never inherit loader paths.
        library = Path(python).resolve().parent.parent / "lib"
        if library.is_dir():
            env["LD_LIBRARY_PATH"] = str(library)
    return env


def verify_stage(stage, contract):
    manifest = json.loads((stage / "baseline-manifest.json").read_text())
    if manifest["contract_sha256"] != digest(CONTRACT.read_bytes()):
        raise ValueError("regression.contract_changed")
    if manifest["pin"] != contract["pin"] or manifest["production_qualified"]:
        raise ValueError("regression.invalid_stage")
    source = stage / "source"
    expected = {row["path"] for row in manifest["effective_files"]}
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if actual != expected or any(p.is_symlink() for p in source.rglob("*")):
        raise ValueError("regression.unexpected_stage_files")
    for row in manifest["effective_files"]:
        if digest((source / row["path"]).read_bytes()) != row["sha256"]:
            raise ValueError("regression.stage_modified")
    return source


def run(stage, python, mode, test_files=None):
    contract = json.loads(CONTRACT.read_text())
    source = verify_stage(stage, contract)
    with tempfile.TemporaryDirectory(prefix="maya-g0-native-") as temp:
        home = Path(temp)
        # No ambient provider keys, Hermes profiles, Python paths or plugin flags.
        env = clean_environment(home, python)
        prepared = subprocess.run([str(python), "-c", PREFLIGHT], cwd=source,
                                  env=env, capture_output=True, text=True)
        if not prepared.stdout.strip():
            raise ValueError("regression.prepared_environment_unavailable")
        deps = json.loads(prepared.stdout)
        (stage / "native-dependencies.json").write_text(json.dumps(deps, indent=2) + "\n")
        if prepared.returncode:
            return {"status": "blocked", "reason_code": "regression.dependencies_not_prepared",
                    "dependencies": deps["blocked_dependencies"], "production_qualified": False}
        # Native conftest creates its own gateway cache. Tests run on a disposable
        # copy, preserving the exported evidence tree and excluding inherited caches.
        test_source = home / "source"
        test_source.mkdir()
        for path in source.rglob("*"):
            if path.is_file():
                target = test_source / path.relative_to(source)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        (home / "g0_pytest_plugin.py").write_text(PLUGIN)
        # Only the pytest reporting/network plugin path is added, never Maya's
        # repo, fixture imports or replacement native modules.
        env["PYTHONPATH"] = str(home)
        env["G0_NATIVE_RESULT"] = str(home / "native-result.json")
        tests = ([r["path"] for r in contract["ordinary_regressions"]] if mode == "bounded"
                 else sorted(p.relative_to(source).as_posix() for p in (source / "tests").rglob("test_*.py")))
        required = list(tests)
        if test_files:
            if mode != "bounded" or any(p not in required for p in test_files) or len(set(test_files)) != len(test_files):
                raise ValueError("regression.unregistered_test_subset")
            tests = list(test_files)
        results = []
        for index, test in enumerate(tests):
            report = home / ("native-result-" + str(index) + ".json")
            env["G0_NATIVE_RESULT"] = str(report)
            command = [str(python), "-m", "pytest", "-p", "pytest_asyncio.plugin",
                       "-p", "g0_pytest_plugin", "-o", "addopts=", "-m", "not integration",
                       "-p", "no:cacheprovider", "-q", "--maxfail=1",
                       "--basetemp", str(home / ("pytest-" + str(index))), test]
            completed = subprocess.run(command, cwd=test_source, env=env)
            item = json.loads(report.read_text()) if report.exists() else {"reason_code": "regression.no_result"}
            item.update(path=test, exit_code=completed.returncode)
            results.append(item)
            if completed.returncode:
                break
        result = {"mode": mode, "status": "passed" if len(results) == len(tests) and
                  all(r["exit_code"] == 0 for r in results) else "failed",
                  "files": results, "not_run_files": tests[len(results):],
                  "production_qualified": False}
        if test_files:
            result["scope"] = "diagnostic_subset_not_gate_acceptance"
            result["omitted_files"] = [p for p in required if p not in tests]
            if result["status"] == "passed":
                result["status"] = "partial"
        (stage / ("native-" + mode + "-result.json")).write_text(json.dumps(result, indent=2) + "\n")
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, type=Path)
    parser.add_argument("--python", required=True, type=Path)
    parser.add_argument("--mode", choices=("bounded", "full"), required=True)
    parser.add_argument("--test-file", action="append", help="Registered bounded subset; never accepts the gate")
    args = parser.parse_args()
    try:
        result = run(args.stage.resolve(), args.python.absolute(), args.mode, args.test_file)
    except (ValueError, OSError, KeyError) as exc:
        code = str(exc) if str(exc).startswith("regression.") else "regression.job_failed"
        result = {"status": "blocked", "reason_code": code, "production_qualified": False}
    print(json.dumps(result))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
