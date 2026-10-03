"""G0 provenance checks, without credentials or a substitute runtime."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("baseline", ROOT / "scripts/prepare_governance_baseline.py")
baseline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(baseline)
with patch.object(sys, "path", [str(ROOT / "scripts"), *sys.path]):
    native_spec = importlib.util.spec_from_file_location("native_regressions", ROOT / "scripts/run_governance_native_regressions.py")
    native = importlib.util.module_from_spec(native_spec)
    native_spec.loader.exec_module(native)


class TestGovernanceBaseline(unittest.TestCase):
    def contract(self):
        return json.loads(baseline.CONTRACT.read_text())

    def test_register_has_explicit_unqualified_roots_and_existing_test_suites(self):
        contract = self.contract()
        baseline.validate_contract(contract)
        self.assertEqual(contract["profile"]["customer_route"]["status"],
                         "selected_documented_not_runtime_qualified")
        self.assertFalse(contract["production_qualified"])
        self.assertTrue(any(row["status"] == "unresolved" for row in contract["coverage"]))
        self.assertEqual(contract["historical_installer"]["patches"], 12)
        self.assertEqual(contract["historical_installer"]["gate_count"], 4)
        self.assertEqual(contract["profile"]["customer_route"]["model"], "gpt-6-luna")
        self.assertEqual(contract["profile"]["customer_route"]["api"], "responses")

    def test_patch_identity_order_and_complete_native_change_inventory(self):
        contract = self.contract()
        joined, changed = bytearray(), set()
        for item in contract["patches"]:
            data = (ROOT / "patches/hermes" / item["filename"]).read_bytes()
            self.assertEqual(baseline.digest(data), item["sha256"])
            joined.extend(data)
            changed.update(baseline.patch_paths(data))
        self.assertEqual(baseline.digest(joined), contract["patch_series_sha256"])
        self.assertEqual(len(changed), 24)

    def test_invalid_contract_order_or_production_claim_is_rejected(self):
        for key in ("patches", "production_qualified"):
            c = copy.deepcopy(self.contract())
            if key == "patches":
                c[key].reverse()
            else:
                c[key] = True
            with self.assertRaises(ValueError):
                baseline.validate_contract(c)

    def test_unknown_root_fallback_and_missing_test_are_rejected(self):
        c = self.contract()
        c["profile"]["unknown_roots"] = "allow"
        with self.assertRaises(ValueError):
            baseline.validate_contract(c)
        c = self.contract()
        c["coverage"][0]["tests"] = ["tests.nonexistent_g0_test"]
        with self.assertRaises(ValueError):
            baseline.validate_contract(c)

    def test_untrusted_paths_and_patch_renames_are_rejected(self):
        for name in ("../outside", "/outside", "C:/outside", "a\\b", "a/.git/config"):
            with self.assertRaises(ValueError):
                baseline.safe_path(name)
        with self.assertRaises(ValueError):
            baseline.patch_paths(b"--- a/a.py\n+++ b/b.py\n")

    def test_existing_output_is_never_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "output_must_be_new"):
                baseline.prepare(Path(directory), Path(directory))

    def test_native_job_removes_ambient_credentials_and_plugin_settings(self):
        with patch.dict("os.environ", {"OPENAI_API_KEY": "synthetic-never-log",
                                      "HERMES_PROXY_URL": "https://invalid.example",
                                      "PYTHONPATH": "untrusted", "PYTEST_ADDOPTS": "--skip"}):
            env = native.clean_environment(Path("isolated"))
        for key in ("OPENAI_API_KEY", "HERMES_PROXY_URL", "PYTHONPATH", "PYTEST_ADDOPTS"):
            self.assertNotIn(key, env)
        self.assertEqual(env["HERMES_HOME"], str(Path("isolated/hermes")))
        self.assertEqual(env["UV_OFFLINE"], "1")
        self.assertEqual(env["HERMES_DISABLE_LAZY_INSTALLS"], "1")
        self.assertIn('"bedrock"', native.PREFLIGHT)

    def test_linux_job_is_manual_pinned_and_does_not_build_an_installer(self):
        import yaml
        job = yaml.load((ROOT / ".github/workflows/governance-native-regressions.yml").read_text(), Loader=yaml.BaseLoader)
        self.assertEqual(set(job["on"]), {"workflow_dispatch"})
        steps = job["jobs"]["native-linux"]["steps"]
        pinned = [s for s in steps if s.get("with", {}).get("repository") == "Bidzina83/hermes-agent"]
        self.assertEqual(pinned[0]["with"]["ref"], baseline.PIN)
        self.assertEqual(pinned[0]["with"]["persist-credentials"], "false")
        commands = "\n".join(s.get("run", "") for s in steps)
        self.assertIn("--locked", commands)
        self.assertIn("--no-install-project", commands)
        self.assertIn("--extra bedrock", commands)
        self.assertIn("run_governance_native_regressions.py", commands)
        self.assertNotIn("build_phase6_release", commands)

    def test_native_job_rejects_tampered_and_extra_source_files(self):
        with tempfile.TemporaryDirectory() as directory:
            stage = Path(directory)
            source = stage / "source"
            source.mkdir()
            (source / "native.py").write_bytes(b"value = 1\n")
            manifest = {"contract_sha256": baseline.digest(baseline.CONTRACT.read_bytes()),
                        "pin": baseline.PIN, "production_qualified": False,
                        "effective_files": [{"path": "native.py", "sha256": baseline.digest(b"value = 1\n")}]}
            (stage / "baseline-manifest.json").write_text(json.dumps(manifest))
            native.verify_stage(stage, self.contract())
            (source / "extra.py").write_text("unsafe = True")
            with self.assertRaisesRegex(ValueError, "unexpected_stage_files"):
                native.verify_stage(stage, self.contract())
            (source / "extra.py").unlink()
            (source / "native.py").write_text("value = 2")
            with self.assertRaisesRegex(ValueError, "stage_modified"):
                native.verify_stage(stage, self.contract())

    def test_required_native_skips_fail_the_job(self):
        import types
        with tempfile.TemporaryDirectory() as directory:
            plugin = {}
            with patch.dict(sys.modules, {"pytest": types.ModuleType("pytest")}), patch.dict("os.environ", {"G0_NATIVE_RESULT": str(Path(directory) / "result.json")}):
                # Executing the reporting plugin does not import/replace Hermes.
                import socket
                with patch.object(socket.socket, "connect"), patch.object(socket.socket, "connect_ex"), patch.object(socket, "create_connection"), patch.object(socket, "socketpair"):
                    exec(native.PLUGIN, plugin)
                    reporter = types.SimpleNamespace(stats={"passed": [object()], "skipped": [object()]})
                    manager = types.SimpleNamespace(get_plugin=lambda name: reporter)
                    session = types.SimpleNamespace(config=types.SimpleNamespace(pluginmanager=manager), exitstatus=0)
                    plugin["pytest_sessionfinish"](session, 0)
            self.assertEqual(session.exitstatus, 1)
            self.assertEqual(json.loads((Path(directory) / "result.json").read_text())["skipped"], 1)

    def test_native_socketpair_ipc_does_not_open_external_network(self):
        import socket
        import types
        original_pair, original_connect = socket.socketpair, socket.socket.connect
        plugin = {}
        with patch.dict(sys.modules, {"pytest": types.ModuleType("pytest")}), \
                patch.object(socket.socket, "connect", original_connect), \
                patch.object(socket.socket, "connect_ex", socket.socket.connect_ex), \
                patch.object(socket, "create_connection", socket.create_connection), \
                patch.object(socket, "socketpair", original_pair):
            exec(native.PLUGIN, plugin)
            left, right = socket.socketpair()
            try:
                left.sendall(b"synthetic IPC")
                self.assertEqual(right.recv(13), b"synthetic IPC")
            finally:
                left.close()
                right.close()
            with socket.socket() as sock:
                for host in ("127.0.0.1", "192.0.2.1"):
                    with self.assertRaisesRegex(RuntimeError, "network_forbidden"):
                        sock.connect((host, 9))

    def test_git_objects_not_dirty_files_or_checkout_filters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo, stage = root / "repo", root / "stage"
            repo.mkdir()
            stage.mkdir()
            def git(*args):
                return baseline.git(repo, *args)
            git("init", "-q")
            git("config", "core.autocrlf", "false")
            (repo / "native.py").write_bytes(b"value = 1\n")
            git("add", "native.py")
            git("-c", "user.name=G0 Test", "-c", "user.email=synthetic@example.invalid",
                "commit", "-qm", "synthetic object baseline")
            pin = git("rev-parse", "HEAD").decode().strip()
            (repo / "native.py").write_bytes(b"dirty host credential marker\r\n")
            (repo / "untracked.env").write_bytes(b"not an input")
            records = baseline.export_objects(repo, baseline.tree(repo, pin), stage)
            self.assertEqual((stage / "native.py").read_bytes(), b"value = 1\n")
            self.assertEqual([r["path"] for r in records], ["native.py"])
            self.assertFalse((stage / "untracked.env").exists())

    def test_patch_application_does_not_inherit_enclosing_repository(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            baseline.git(parent, "init", "-q")
            source = parent / "export" / "source"
            source.mkdir(parents=True)
            target = source / "native.py"
            target.write_bytes(b"value = 1\n")
            candidate = parent / "candidate.patch"
            candidate.write_bytes(
                b"diff --git a/native.py b/native.py\n"
                b"--- a/native.py\n+++ b/native.py\n"
                b"@@ -1 +1 @@\n-value = 1\n+value = 2\n"
            )
            baseline.git(source, "apply", "--no-index", "--whitespace=error", str(candidate))
            self.assertEqual(target.read_bytes(), b"value = 2\n")
            self.assertFalse((parent / "native.py").exists())

    def test_native_cli_preserves_selected_virtual_environment_path(self):
        import types
        selected = Path("selected-venv") / "bin" / "python"
        args = types.SimpleNamespace(stage=ROOT, python=selected, mode="bounded", test_file=None,
                                     security_checkpoint=False)
        with patch.object(native.argparse.ArgumentParser, "parse_args", return_value=args), \
                patch.object(native, "run", return_value={"status": "passed"}) as run, \
                patch("builtins.print"):
            self.assertEqual(native.main(), 0)
        self.assertEqual(run.call_args.args[1], selected.absolute())

    def test_native_environment_uses_only_selected_python_library(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            python = root / "prepared" / "bin" / "python"
            library = root / "prepared" / "lib"
            library.mkdir(parents=True)
            with patch.object(native.os, "name", "posix"), \
                    patch.object(native, "Path", side_effect=lambda value: value), \
                    patch.dict("os.environ", {"LD_LIBRARY_PATH": "untrusted-loader-path"}):
                env = native.clean_environment(root, python)
            self.assertEqual(env["LD_LIBRARY_PATH"], str(library))
            self.assertNotIn("untrusted-loader-path", env.values())


if __name__ == "__main__":
    unittest.main()
