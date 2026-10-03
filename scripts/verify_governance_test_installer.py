"""Verify the dedicated candidate artifact and optionally its offline startup."""
import argparse
import json
import os
import subprocess
from pathlib import Path

import build_phase6_release as release
from verify_phase6_release import _windows_authenticode_status
from project_maya.hermes_plugins.candidate import CANDIDATE_SHA256
from project_maya.hermes_plugins.candidate_qualification import SCENARIOS
from project_maya.hermes_plugins.governance import _checked_payload


def verify(directory: Path, *, allow_unsigned: bool, run_payload: bool) -> None:
    if not __debug__:
        raise RuntimeError("Verification requires Python assertions enabled.")
    directory = directory.resolve()
    manifest = json.loads((directory / "governance-test-installer.json").read_text(encoding="utf-8"))
    assert manifest["qualification"] == "test_only_unqualified" and manifest["production_qualified"] is False
    assert manifest["hermes_sha256"] == CANDIDATE_SHA256
    file_manifest = directory / "payload-files.json"
    assert release.sha256_file(file_manifest) == manifest["payload_manifest_sha256"]
    payload = directory / "payload"
    for required in ("runtime/python/python.exe", "runtime/maya_runtime.py", "runtime/runtime-manifest.json",
                     "runtime/site-packages/run_agent.py", "runtime/site-packages/agent/conversation_loop.py",
                     "runtime/site-packages/hermes_cli/middleware.py",
                     "runtime/site-packages/agent/context_compressor.py",
                     "runtime/site-packages/agent/background_review.py",
                     "runtime/site-packages/agent/turn_finalizer.py",
                     "runtime/site-packages/hermes_cli/plugins.py",
                     "runtime/site-packages/project_maya/hermes_plugins/candidate.py",
                     "runtime/site-packages/project_maya/hermes_plugins/candidate_qualification.py",
                     "runtime/site-packages/project_maya/hermes_plugins/candidate_transport.py",
                     "config-templates/candidate.json"):
        assert (payload / required).is_file(), "Missing real candidate component: " + required
    hermes_wheels = list((payload / "wheels").glob("hermes_agent-*.whl"))
    assert len(hermes_wheels) == 1 and release.sha256_file(hermes_wheels[0]) == CANDIDATE_SHA256
    runtime = json.loads((payload / "runtime/runtime-manifest.json").read_text(encoding="utf-8"))
    assert runtime["qualification"] == "test_only_unqualified" and runtime["production_qualified"] is False
    expected = set()
    for file in json.loads(file_manifest.read_text(encoding="utf-8"))["files"]:
        path = (payload / file["path"]).resolve()
        assert payload in path.parents, "Manifest path escapes payload"
        assert release.sha256_file(path) == file["sha256"], file["path"]
        assert not set(path.relative_to(payload).parts) & {"__pycache__", "tests", ".git"}
        expected.add(file["path"])
    assert expected == {p.relative_to(payload).as_posix() for p in payload.rglob("*") if p.is_file()}
    installer = (directory / manifest["installer"]["path"]).resolve()
    assert directory in installer.parents
    assert release.sha256_file(installer) == manifest["installer"]["sha256"]
    assert release.sha256_file(directory / "inno/maya-governance-standard.iss") == manifest["inno_source_sha256"]
    if not (allow_unsigned and manifest["signing"] == "unsigned-local-smoke-only"):
        assert _windows_authenticode_status(installer) == "Valid", "Installer must be Authenticode signed"
    launcher = (payload / "bin/qualify-governance.cmd").read_text(encoding="utf-8")
    assert "runtime\\python\\python.exe" in launcher and "candidate_qualification" in launcher
    assert "Maya Governance Test" in launcher and "py -3" not in launcher
    assert ' '.join(SCENARIOS) in launcher and "if errorlevel 1 goto failed" in launcher
    if run_payload:
        env = {k: os.environ[k] for k in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "LOCALAPPDATA", "APPDATA") if k in os.environ}
        env.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1",
                   MAYA_DATA_DIR=str(directory / "qualification-data"), HERMES_HOME=str(directory / "qualification-data/hermes"),
                   HOME=str(directory / "qualification-data"), USERPROFILE=str(directory / "qualification-data"))
        outcomes = []
        for scenario in SCENARIOS:
            result = subprocess.run([
                str(payload / "runtime/python/python.exe"), str(payload / "runtime/maya_runtime.py"),
                "-m", "project_maya.hermes_plugins.candidate_qualification", "--install-dir", str(payload),
                "--data-root", str(directory / "qualification-data"), "--scenario", scenario,
            ], cwd=directory, env=env, capture_output=True, text=True, timeout=180)
            assert result.returncode == 0, "Offline candidate qualification failed: " + result.stdout[-1500:] + result.stderr[-1500:]
            outcome = json.loads(result.stdout.splitlines()[-1])
            assert outcome["scenario"] == scenario
            assert outcome["status"] == "passed" and outcome["production_qualified"] is False
            required = {"binding_before_construction", "governed_memory_retrieval", "production_guard_preserved", "secret_safe",
                        "native_persistence_denial_propagated", "denied_session_state_preserved",
                        "zero_denied_store_calls", "raw_api_observers_suppressed"}
            required.update({"model-denial": {"native_model_denial_audited", "zero_denied_request_transport"},
                             "model-allow": {"single_sdk_attempt", "native_model_allow_audited", "native_output_validated"},
                             "tool-denial": {"single_sdk_attempt", "native_file_denial_audited", "zero_tool_handler_calls", "protected_file_unchanged"},
                             "tool-allow": {"zero_sdk_retries", "two_model_requests", "native_file_allow_audited", "native_tool_result_validated", "one_native_tool_dispatch", "followup_model_reauthorized", "native_output_validated", "approved_file_unchanged"},
                             "compression-denial": {"native_model_denial_audited", "zero_denied_request_transport", "compression_denial_propagated", "single_summary_attempt", "zero_summary_fallbacks", "summary_state_preserved", "zero_summary_transport"},
                             "background-denial": {"native_model_allow_audited", "native_output_validated", "single_sdk_attempt", "finalizer_background_denial_propagated", "native_background_factory_called", "zero_background_threads", "zero_background_agents"}}[scenario])
            assert required.issubset(outcome["checks"]), "Missing qualification evidence"
            assert all(outcome["checks"].values())
            _checked_payload(result.stdout + result.stderr)
            assert "local-test-only" not in result.stdout + result.stderr
            assert "Synthetic business question" not in result.stdout + result.stderr
            assert "Synthetic compression question" not in result.stdout + result.stderr
            outcomes.append(outcome)
        release.write_canonical_json(directory / "release-payload-smoke.json", {"scenarios": outcomes, "production_qualified": False})
    print("Candidate artifact verified; production qualification remains blocked.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-unsigned-local-smoke", action="store_true")
    parser.add_argument("--run-payload", action="store_true")
    args = parser.parse_args(argv)
    verify(args.directory, allow_unsigned=args.allow_unsigned_local_smoke, run_payload=args.run_payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
