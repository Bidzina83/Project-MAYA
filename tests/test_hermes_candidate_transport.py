import json
import io
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

from project_maya.hermes_plugins.candidate_transport import completion_response


class TestCandidateTransport(unittest.TestCase):
    def request(self, *, stream=False, model="synthetic-model", path="/v1/chat/completions"):
        import httpx
        return httpx.Request("POST", "http://127.0.0.1:9" + path,
                             json={"model": model, "stream": stream})

    def test_response_is_sdk_compatible_and_synthetic(self):
        result = completion_response(self.request(), tool=False).json()
        self.assertEqual(result["choices"][0]["message"]["content"], "Synthetic approved response")

    def test_stream_contains_bounded_native_file_call(self):
        result = completion_response(self.request(stream=True), tool=True)
        chunks = [json.loads(line[6:]) for line in result.text.splitlines()
                  if line.startswith("data: ") and line != "data: [DONE]"]
        function = chunks[0]["choices"][0]["delta"]["tool_calls"][0]["function"]
        self.assertEqual(function["name"], "read_file")
        self.assertEqual(json.loads(function["arguments"]), {"path": "denied.txt", "offset": 1, "limit": 1})
        self.assertEqual(chunks[-1]["choices"][0]["finish_reason"], "tool_calls")

    def test_unexpected_routes_and_models_fail_closed(self):
        for request in (self.request(path="/other"), self.request(model="other")):
            with self.assertRaises(RuntimeError):
                completion_response(request, tool=False)

    def test_allowed_proposal_selects_only_synthetic_document(self):
        result = completion_response(self.request(), tool=True, tool_path="approved.txt").json()
        args = json.loads(result["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"])
        self.assertEqual(args, {"path": "approved.txt", "offset": 1, "limit": 1})

    def test_blocked_readiness_is_specific_but_does_not_expose_errors(self):
        from project_maya.hermes_plugins.candidate_qualification import main
        for message, reason in (("candidate.native_shell_missing", "candidate.native_shell_missing"),
                                ("sensitive unexpected failure", "candidate.qualification_failed")):
            output = io.StringIO()
            with patch("project_maya.hermes_plugins.candidate_qualification.qualify", side_effect=RuntimeError(message)), redirect_stdout(output):
                code = main(["--install-dir", "unused", "--data-root", "unused", "--scenario", "tool-allow"])
            self.assertEqual(code, 1)
            report = json.loads(output.getvalue())
            self.assertEqual(report["reason_code"], reason)
            self.assertEqual(report["status"], "blocked")
            self.assertNotIn("sensitive unexpected failure", output.getvalue())

    @unittest.skipUnless(os.name == "nt", "Windows shell discovery")
    def test_windows_shell_discovery_rejects_wsl_and_missing_dependency(self):
        from project_maya.hermes_plugins.candidate_qualification import _configure_native_shell
        with patch.dict(os.environ, {"HERMES_GIT_BASH_PATH": "C:/Windows/System32/bash.exe"}), patch.object(Path, "is_file", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "native_shell_missing"):
                _configure_native_shell()
        with patch.dict(os.environ, {"HERMES_GIT_BASH_PATH": "C:/missing/bash.exe"}), patch.object(Path, "is_file", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "native_shell_missing"):
                _configure_native_shell()


@unittest.skipUnless(os.environ.get("MAYA_GOVERNANCE_TEST_PAYLOAD"), "built candidate payload not supplied")
class TestInstalledCandidateLoop(unittest.TestCase):
    def test_real_installed_sdk_and_native_loop(self):
        payload = Path(os.environ["MAYA_GOVERNANCE_TEST_PAYLOAD"]).resolve()
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as temporary:
            env = {k: os.environ[k] for k in ("PATH", "SystemRoot", "WINDIR", "TEMP", "TMP", "LOCALAPPDATA", "APPDATA") if k in os.environ}
            env.update(HOME=temporary, USERPROFILE=temporary, MAYA_DATA_DIR=temporary,
                       HERMES_HOME=str(Path(temporary) / "hermes"), PYTHONUTF8="1",
                       PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
            from project_maya.hermes_plugins.candidate_qualification import SCENARIOS
            for scenario in SCENARIOS:
                with self.subTest(scenario=scenario):
                    result = subprocess.run([str(payload / "runtime/python/python.exe"),
                        str(payload / "runtime/maya_runtime.py"), "-m",
                        "project_maya.hermes_plugins.candidate_qualification",
                        "--install-dir", str(payload), "--data-root", temporary,
                        "--scenario", scenario], cwd=temporary, env=env,
                        capture_output=True, text=True, timeout=180)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    report = json.loads(result.stdout.strip())
                    self.assertEqual(report["scenario"], scenario)
                    self.assertEqual(report["status"], "passed")
                    self.assertFalse(report["production_qualified"])
                    self.assertTrue(report["checks"])
                    self.assertTrue(all(report["checks"].values()))
                    self.assertNotIn("local-test-only", result.stdout + result.stderr)
                    self.assertNotIn("Candidate protected file content", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
