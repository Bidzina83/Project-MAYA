"""Preparation/probe unit tests only; no managed Python or LPAC execution."""

import ast
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, mock_open, patch

from scripts import governance_v2_python_probe as probe
from scripts import prepare_governance_v2_python_repro as prep


class PreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.stage, self.output = self.root / "source", self.root / "output"
        self.python = self.stage / "runtime/python"
        self.python.mkdir(parents=True)
        self.helper = self.root / "helper.exe"
        self.helper.write_bytes(b"inert helper fixture")
        self.entries = []
        for name in ("python.exe", "python313.dll", "python3.dll", "vcruntime140.dll",
                     "vcruntime140_1.dll", "Lib/encodings/__init__.py"):
            target = self.python / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(b"inert Python fixture")
            self.entries.append({"path": f"runtime/python/{name}", "sha256": prep.digest(target.read_bytes())})
        (self.stage / "runtime/worker.py").write_bytes(b"original worker must not change")
        self.entries.append({"path": "runtime/hermes/run_agent.py", "sha256": "not copied"})
        self.save()
        patcher = patch.object(prep, "FROZEN_HELPER", prep.digest(self.helper.read_bytes()))
        patcher.start()
        self.addCleanup(patcher.stop)

    def save(self, **overrides):
        manifest = {"pin": prep.PIN, "patches_applied": False, "files": self.entries}
        manifest.update(overrides)
        data = json.dumps(manifest).encode()
        (self.stage / "runtime-manifest.json").write_bytes(data)
        prep.FROZEN_RUNTIME = prep.digest(data)

    def tearDown(self):
        prep.FROZEN_RUNTIME = "0ed977a4f7269ec86d01468e19820d616fc4e74cacd21b2919131d88457a5b32"

    def prepare(self):
        return prep.prepare(self.stage, self.helper, self.output)

    def test_exact_python_only_copy_and_nonexecution_status(self):
        report = self.prepare()
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["production_qualified"])
        self.assertFalse(report["hermes_included"])
        self.assertFalse(report["external_sharing_authorized"])
        self.assertIsNone(report["reference"]["binary_sha256"])
        self.assertEqual((self.stage / "runtime/worker.py").read_bytes(), b"original worker must not change")
        self.assertEqual((self.output / prep.STAGE_NAME / "runtime/worker.py").read_bytes(), prep.PROBE.read_bytes())
        self.assertEqual(list((self.output / prep.STAGE_NAME / "state").iterdir()), [])
        names = {item["path"] for item in report["files"]}
        self.assertFalse(any("hermes/" in name or "dependencies/" in name for name in names))
        actual = {p.relative_to(self.output).as_posix() for p in self.output.rglob("*") if p.is_file()}
        self.assertEqual(actual, names | {"reproduction-manifest.json"})
        for item in report["files"]:
            self.assertEqual(prep.digest((self.output / item["path"]).read_bytes()), item["sha256"])
        manifest_text = (self.output / "reproduction-manifest.json").read_text()
        self.assertNotIn(str(self.root), manifest_text)

    def test_existing_output_refused(self):
        self.output.mkdir()
        with self.assertRaisesRegex(ValueError, "output_must_be_new"):
            self.prepare()

    def test_default_retains_historical_contract_and_layout(self):
        report = self.prepare()
        self.assertNotIn("profile", report)
        self.assertEqual((self.output / "comparison-contract.json").read_bytes(), prep.CONTRACT.read_bytes())
        self.assertEqual((self.output / "COMPARISON.md").read_bytes(), prep.RUNBOOK.read_bytes())
        self.assertEqual(json.loads((self.output / "comparison-contract.json").read_bytes())["vm"]["version"], "25H2")
        self.assertFalse((self.output / prep.CONTRACT_26H2.name).exists())

    def test_26h2_explicit_binding_is_self_contained_and_nonexecuting(self):
        report = prep.prepare(self.stage, self.helper, self.output, profile="26h2")
        self.assertEqual(report["profile"], "26h2")
        self.assertFalse(report["execution_authorized"])
        self.assertFalse(report["external_sharing_authorized"])
        self.assertFalse(report["production_qualified"])
        self.assertFalse(report["gate_a_accepted"])
        self.assertIsNone(report["reference"]["binary_sha256"])
        contract = json.loads((self.output / report["contract_input"]["path"]).read_bytes())
        self.assertEqual((contract["vm"]["version"], contract["vm"]["build"], contract["vm"]["ubr"]),
                         ("26H2", 26300, 9711))
        self.assertFalse(contract["vm"]["guest_verified"])
        original = json.loads((self.output / prep.CONTRACT.name).read_bytes())
        for field in ("common", "cases", "budget", "reference", "python_arguments"):
            self.assertEqual(contract[field], original[field])
        for item in [report["contract_input"], report["runbook_input"], *report["predecessor_inputs"]]:
            self.assertEqual(prep.digest((self.output / item["path"]).read_bytes()), item["sha256"])
        actual = {path.relative_to(self.output).as_posix() for path in self.output.rglob("*") if path.is_file()}
        self.assertEqual(actual, {item["path"] for item in report["files"]} | {"reproduction-manifest.json"})
        for item in report["files"]:
            self.assertEqual(prep.digest((self.output / item["path"]).read_bytes()), item["sha256"])
        self.assertEqual((self.stage / "runtime/worker.py").read_bytes(), b"original worker must not change")
        self.assertNotIn(str(self.root), (self.output / "reproduction-manifest.json").read_text())
        self.assertEqual(list((self.output / prep.STAGE_NAME / "state").iterdir()), [])

    def test_26h2_does_not_retarget_or_overwrite_historical_bundle(self):
        self.prepare()
        original = {path.relative_to(self.output): path.read_bytes()
                    for path in self.output.rglob("*") if path.is_file()}
        successor = self.root / "successor"
        prep.prepare(self.stage, self.helper, successor, profile="26h2")
        self.assertEqual(original, {path.relative_to(self.output): path.read_bytes()
                                   for path in self.output.rglob("*") if path.is_file()})
        with self.assertRaisesRegex(ValueError, "output_must_be_new"):
            prep.prepare(self.stage, self.helper, self.output, profile="26h2")

    def test_unknown_profile_refused_without_output(self):
        with self.assertRaisesRegex(ValueError, "unknown_profile"):
            prep.prepare(self.stage, self.helper, self.output, profile="latest")
        self.assertFalse(self.output.exists())

    def test_26h2_predecessor_drift_refused_without_output(self):
        changed = self.root / "changed.json"
        changed.write_bytes(prep.CONTRACT.read_bytes() + b" ")
        with patch.object(prep, "CONTRACT", changed), self.assertRaisesRegex(ValueError, "comparison_input_changed"):
            prep.prepare(self.stage, self.helper, self.output, profile="26h2")
        self.assertFalse(self.output.exists())

    def test_26h2_input_drift_refused_without_output(self):
        for attribute in ("CONTRACT_26H2", "RUNBOOK_26H2", "RUNBOOK"):
            with self.subTest(attribute=attribute):
                changed = self.root / "changed-input"
                changed.write_bytes(getattr(prep, attribute).read_bytes() + b" ")
                with patch.object(prep, attribute, changed), self.assertRaisesRegex(ValueError, "comparison_input_changed"):
                    prep.prepare(self.stage, self.helper, self.output, profile="26h2")
                self.assertFalse(self.output.exists())

    def test_26h2_altered_permissions_or_budget_refused(self):
        for field, key, value in (("common", "lpac_required", False),
                                  ("vm", "host_folder_clipboard_device_or_credential_sharing", True),
                                  ("budget", "automatic_retries", 1),
                                  ("reference", "binary_sha256", "unreviewed")):
            with self.subTest(field=field, key=key):
                contract = json.loads(prep.CONTRACT_26H2.read_bytes())
                contract[field][key] = value
                changed = self.root / "changed-contract.json"
                changed.write_text(json.dumps(contract))
                with patch.object(prep, "CONTRACT_26H2", changed), self.assertRaisesRegex(ValueError, "comparison_input_changed"):
                    prep.prepare(self.stage, self.helper, self.output, profile="26h2")
                self.assertFalse(self.output.exists())

    def test_cli_passes_only_explicit_profile(self):
        output = prep.ROOT / ".codex-build" / "inert-cli-profile-fixture"
        for options, profile in (([], "25h2"), (["--profile", "26h2"], "26h2")):
            with self.subTest(profile=profile), patch("sys.argv", ["prepare", "--output", str(output), *options]), \
                    patch.object(prep, "prepare", return_value={"status": "prepared_not_executed", "files": []}) as prepare, \
                    redirect_stdout(io.StringIO()):
                self.assertEqual(prep.main(), 0)
                self.assertEqual(prepare.call_args.kwargs, {"profile": profile})

    def test_overlapping_output_refused(self):
        with self.assertRaisesRegex(ValueError, "overlapping_output"):
            prep.prepare(self.stage, self.helper, self.stage / "new")

    def test_manifest_hash_drift_refused_before_copy(self):
        (self.stage / "runtime-manifest.json").write_bytes(b"{}")
        with self.assertRaisesRegex(ValueError, "frozen_input_changed"):
            self.prepare()
        self.assertFalse(self.output.exists())

    def test_helper_drift_refused(self):
        self.helper.write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "frozen_input_changed"):
            self.prepare()

    def test_python_drift_refused(self):
        (self.python / "python313.dll").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "python_changed"):
            self.prepare()

    def test_unlisted_file_refused(self):
        (self.python / "extra.dll").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "python_inventory_changed"):
            self.prepare()

    def test_missing_core_file_refused(self):
        self.entries = [item for item in self.entries if item["path"] != "runtime/python/python3.dll"]
        (self.python / "python3.dll").unlink()
        self.save()
        with self.assertRaisesRegex(ValueError, "python_inventory_changed"):
            self.prepare()

    def test_patched_baseline_refused(self):
        self.save(patches_applied=True)
        with self.assertRaisesRegex(ValueError, "invalid_baseline"):
            self.prepare()

    def test_invalid_inventory_names_refused(self):
        for name in ("../escape", "runtime/python/../worker.py", "C:/escape", "/escape", "runtime\\python\\x", "./runtime/python/x"):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "invalid_inventory"):
                prep.inventory_name(name)

    def test_duplicate_inventory_refused(self):
        self.entries.append(self.entries[0].copy())
        self.save()
        with self.assertRaisesRegex(ValueError, "duplicate_inventory"):
            self.prepare()

    def test_startup_file_refused_even_if_listed(self):
        target = self.python / "evil.pth"
        target.write_bytes(b"inert startup fixture")
        self.entries.append({"path": "runtime/python/evil.pth", "sha256": prep.digest(target.read_bytes())})
        self.save()
        with self.assertRaisesRegex(ValueError, "generated_or_startup_file"):
            self.prepare()

    def test_reparse_attributes_refused(self):
        with patch.object(Path, "lstat", return_value=SimpleNamespace(st_mode=0, st_file_attributes=0x400)):
            with self.assertRaisesRegex(ValueError, "reparse_path"):
                prep.plain_path(self.stage)

    def test_cli_rejects_nonignored_output(self):
        with patch("sys.argv", ["prepare", "--output", str(self.output)]), redirect_stdout(io.StringIO()):
            self.assertEqual(prep.main(), 1)
        self.assertFalse(self.output.exists())

    def test_preparer_has_no_execution_or_network_imports(self):
        tree = ast.parse(Path(prep.__file__).read_text())
        modules = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
        modules |= {alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names}
        self.assertFalse(modules & {"subprocess", "ctypes", "socket", "urllib", "requests", "project_maya", "run_agent"})

    def test_matrix_is_fixed_and_not_execution_authorization(self):
        contract = json.loads(prep.CONTRACT.read_bytes())
        self.assertFalse(contract["execution_authorized"])
        self.assertEqual([c["id"] for c in contract["cases"]], list("ABCD"))
        self.assertEqual([c["extra_capabilities"] for c in contract["cases"]],
                         [[], [], ["registryRead"], ["registryRead", "lpacCom"]])
        self.assertEqual(contract["budget"]["runs_per_case"], 1)
        self.assertEqual(contract["budget"]["automatic_corrections"], 0)
        self.assertFalse(contract["vm"]["network_adapters_connected_during_runs"])


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.system = SimpleNamespace(version_info=(3, 13, 14),
            flags=SimpleNamespace(isolated=1, no_site=1), stdout=Mock())
        self.file = mock_open()
        self.file.return_value.write.side_effect = len
        self.sleep = Mock()
        for context in (patch.object(probe, "sys", self.system),
                        patch.object(probe.time, "sleep", self.sleep), patch("builtins.open", self.file)):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def test_entry_marker_and_bounded_observation(self):
        self.assertEqual(probe.main(), 0)
        self.file.assert_called_once_with("python-startup.json", "x", encoding="ascii")
        self.sleep.assert_called_once_with(5)
        self.assertEqual(json.loads(self.system.stdout.write.call_args.args[0])["status"], "python_entered")

    def test_wrong_version_does_not_write(self):
        self.system.version_info = (3, 12, 2)
        self.assertEqual(probe.main(), 2)
        self.file.assert_not_called()

    def test_missing_flags_do_not_write(self):
        for name in ("isolated", "no_site"):
            setattr(self.system.flags, name, 0)
            self.assertEqual(probe.main(), 2)
            setattr(self.system.flags, name, 1)
        self.file.assert_not_called()

    def test_stale_marker_refused(self):
        self.file.side_effect = FileExistsError()
        self.assertEqual(probe.main(), 3)
        self.system.stdout.write.assert_not_called()

    def test_short_write_is_not_success(self):
        self.file.return_value.write.side_effect = lambda data: len(data) - 1
        self.assertEqual(probe.main(), 3)
        self.system.stdout.write.assert_not_called()
        self.sleep.assert_not_called()

    def test_only_two_builtin_dependencies(self):
        tree = ast.parse(Path(probe.__file__).read_text())
        imports = [alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names]
        self.assertEqual(imports, ["sys", "time"])


if __name__ == "__main__":
    unittest.main()
