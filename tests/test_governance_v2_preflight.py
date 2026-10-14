"""Baseline validation tests; no Windows provisioning or native qualification."""

import hashlib
import ctypes
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from scripts.preflight_governance_v2_windows import PIN, validate_baseline
from scripts.governance_v2_worker import require_lpac


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.stage = Path(self.tmp.name)
        (self.stage / "source").mkdir()
        data = b"synthetic source\n"
        (self.stage / "source" / "run_agent.py").write_bytes(data)
        item = {"path": "run_agent.py", "mode": "100644",
                "sha256": hashlib.sha256(data).hexdigest(),
                "git_blob": hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()}
        self.manifest = dict(pin=PIN, patches_applied=False, packaging_changes=[],
                             production_qualified=False, baseline_files=[item],
                             effective_files=[{k: item[k] for k in ("path", "mode", "sha256")}])
        self.save()

    def save(self):
        (self.stage / "baseline-manifest.json").write_text(json.dumps(self.manifest))

    def test_exact_ordinary_inventory(self):
        self.assertIn("manifest_sha256", validate_baseline(self.stage))

    def test_patched_manifest_refused(self):
        self.manifest["patches_applied"] = True
        self.save()
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

    def test_changed_bytes_refused(self):
        (self.stage / "source" / "run_agent.py").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

    def test_unlisted_file_refused(self):
        (self.stage / "source" / "extra.py").write_bytes(b"extra")
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

    def test_changed_effective_inventory_refused(self):
        self.manifest["effective_files"][0]["sha256"] = "wrong"
        self.save()
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)

    def test_path_escape_refused(self):
        self.manifest["baseline_files"][0]["path"] = "../escape"
        self.manifest["effective_files"][0]["path"] = "../escape"
        self.save()
        with self.assertRaises(ValueError):
            validate_baseline(self.stage)


class WorkerTokenGuardTests(unittest.TestCase):
    """Fault-injected API contracts, not native containment qualification."""

    def setUp(self):
        self.kernel, self.advapi = Mock(), Mock()
        self.kernel.CloseHandle.return_value = True
        self.kernel.LocalFree.return_value = None
        self.kernel.GetCurrentProcess.return_value = 123
        self.advapi.OpenProcessToken.side_effect = self.open_token
        self.advapi.GetTokenInformation.side_effect = self.token_info
        self.advapi.DuplicateToken.side_effect = self.duplicate
        self.advapi.ConvertSidToStringSidW.side_effect = self.sid_text
        self.advapi.AccessCheck.side_effect = self.access_check
        self.results = iter([True, False, False, False])
        self.buffers = []
        self.enter_context(patch("scripts.governance_v2_worker.os.name", "nt"))
        self.enter_context(patch("scripts.governance_v2_worker.ctypes.WinDLL", create=True,
                                side_effect=lambda name, **kwargs: getattr(self, name.removesuffix("32"))
                                if name == "kernel32" else self.advapi))

    def enter_context(self, context):
        context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)

    @staticmethod
    def open_token(process, access, result):
        result._obj.value = 1
        return True

    @staticmethod
    def duplicate(token, level, result):
        result._obj.value = 2
        return True

    @staticmethod
    def token_info(token, kind, memory, size, needed):
        if kind == 29:
            memory._obj.value = 1
        else:
            ctypes.cast(memory, ctypes.POINTER(ctypes.c_void_p))[0] = kind
        return True

    def sid_text(self, sid, result):
        value = {31: "S-1-15-2-123", 1: "S-1-5-21-123", 25: "S-1-16-4096"}[sid.value]
        buffer = ctypes.create_unicode_buffer(value)
        self.buffers.append(buffer)
        result._obj.value = ctypes.addressof(buffer)
        return True

    def access_check(self, descriptor, token, access, mapping, privileges, length, granted, status):
        allowed = next(self.results)
        granted._obj.value = 1 if allowed else 0
        status._obj.value = allowed
        return True

    def test_expected_lpac_behavior(self):
        require_lpac()
        self.assertEqual(self.advapi.AccessCheck.call_count, 4)
        self.assertEqual(self.kernel.CloseHandle.call_count, 2)

    def test_aap_access_is_not_lpac(self):
        self.results = iter([True, True])
        with self.assertRaisesRegex(RuntimeError, "worker.lpac_behavior_required"):
            require_lpac()

    def test_package_access_must_work(self):
        self.results = iter([False])
        with self.assertRaisesRegex(RuntimeError, "worker.lpac_behavior_required"):
            require_lpac()

    def test_wrong_package_access_blocks(self):
        self.results = iter([True, False, True])
        with self.assertRaisesRegex(RuntimeError, "worker.lpac_behavior_required"):
            require_lpac()

    def test_no_grant_access_blocks(self):
        self.results = iter([True, False, False, True])
        with self.assertRaisesRegex(RuntimeError, "worker.lpac_behavior_required"):
            require_lpac()

    def test_api_error_is_not_successful_denial(self):
        self.advapi.AccessCheck.side_effect = None
        self.advapi.AccessCheck.return_value = False
        with self.assertRaisesRegex(RuntimeError, "worker.probe_api_failed"):
            require_lpac()

    def test_cleanup_failure_blocks(self):
        self.kernel.CloseHandle.return_value = False
        with self.assertRaisesRegex(RuntimeError, "worker.token_cleanup_failed"):
            require_lpac()

    def test_unavailable_token_blocks(self):
        self.advapi.OpenProcessToken.side_effect = None
        self.advapi.OpenProcessToken.return_value = False
        with self.assertRaisesRegex(RuntimeError, "worker.token_unavailable"):
            require_lpac()

    def test_ordinary_process_blocks_before_access_probes(self):
        self.advapi.GetTokenInformation.side_effect = None
        self.advapi.GetTokenInformation.return_value = True
        with self.assertRaisesRegex(RuntimeError, "worker.appcontainer_required"):
            require_lpac()
        self.advapi.AccessCheck.assert_not_called()
