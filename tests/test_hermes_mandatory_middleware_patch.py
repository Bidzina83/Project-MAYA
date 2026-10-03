"""Apply the candidate patch to the real pinned source; never contact a provider."""

import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest.mock import Mock, patch

from project_maya.config import config_from_mapping
from project_maya.governance import PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import (
    GovernanceBoundaryError, MayaGovernancePlugin, bind_request_identity, require_runtime_contract,
)
from tests.test_phase0_contracts import valid_config_mapping


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "hermes_middleware" / "middleware.py"
PATCH = ROOT / "patches" / "hermes" / "0001-opt-in-mandatory-middleware.patch"
SOURCE_SHA256 = "699f514c4f437670e345277de7b105a8a7b18e052af68b1a2bbef904eef99f6c"


class TestMandatoryHermesMiddlewarePatch(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        target = Path(self.tmp.name) / "hermes_cli" / "middleware.py"
        target.parent.mkdir()
        shutil.copyfile(FIXTURE, target)
        result = subprocess.run(
            ["git", "apply", "--whitespace=error", str(PATCH)],
            cwd=self.tmp.name, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.manager = SimpleNamespace(_middleware={})
        plugins = ModuleType("hermes_cli.plugins")
        plugins.get_plugin_manager = lambda: self.manager
        plugins_patch = patch.dict(sys.modules, {"hermes_cli.plugins": plugins})
        plugins_patch.start()
        self.addCleanup(plugins_patch.stop)
        self.engine = self.load_module("_hermes_middleware_candidate", target)
        self.original = self.load_module("_hermes_middleware_original", FIXTURE)
        self.transport = Mock(return_value="synthetic result")
        self.request = {"model": "synthetic-model", "messages": []}

    def load_module(self, name, path):
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        module_patch = patch.dict(sys.modules, {name: module})
        module_patch.start()
        self.addCleanup(module_patch.stop)
        spec.loader.exec_module(module)
        return module

    def register(self, kind, callback):
        self.manager._middleware.setdefault(kind, []).append(callback)

    def require_gates(self, model=None, tool=None):
        self.model_gate = model or (lambda request, next_call, **kw: next_call(request))
        self.tool_gate = tool or (lambda args, next_call, **kw: next_call(args))
        for kind, callback in (("llm_execution", self.model_gate), ("tool_execution", self.tool_gate)):
            self.register(kind, callback)
            self.engine.require_middleware(kind, callback)

    def model(self, engine=None):
        return (engine or self.engine).run_llm_execution_middleware(self.request, self.transport)

    def test_fixture_matches_pinned_artifact(self):
        normalized = FIXTURE.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(normalized).hexdigest(), SOURCE_SHA256)

    def test_partial_patch_does_not_claim_full_maya_contract(self):
        self.assertFalse(hasattr(self.engine, "MAYA_GOVERNANCE_CONTRACT"))
        with self.assertRaises(GovernanceBoundaryError):
            require_runtime_contract(self.engine)

    def test_default_mode_has_no_gate_requirement(self):
        self.assertFalse(self.engine.validate_mandatory_middleware())
        self.assertEqual(self.model(), "synthetic result")
        self.transport.assert_called_once_with(self.request)

    def test_default_error_remains_fail_open_like_upstream(self):
        def broken(**kw):
            raise ValueError("synthetic failure")
        self.register("llm_execution", broken)
        for engine in (self.original, self.engine):
            with self.subTest(engine=engine.__name__), self.assertLogs(engine.logger, "WARNING"):
                self.transport.reset_mock()
                self.assertEqual(self.model(engine), "synthetic result")
                self.transport.assert_called_once()

    def test_default_post_execution_error_preserves_result_without_reexecution(self):
        def broken(request, next_call, **kw):
            next_call(request)
            raise ValueError("synthetic failure")
        self.register("llm_execution", broken)
        for engine in (self.original, self.engine):
            with self.subTest(engine=engine.__name__), self.assertLogs(engine.logger, "WARNING"):
                self.transport.reset_mock()
                self.assertEqual(self.model(engine), "synthetic result")
                self.transport.assert_called_once()

    def test_default_short_circuit_remains_supported(self):
        self.register("llm_execution", lambda **kw: "cached result")
        for engine in (self.original, self.engine):
            self.assertEqual(self.model(engine), "cached result")
        self.transport.assert_not_called()

    def test_default_downstream_error_is_preserved(self):
        self.register("llm_execution", lambda request, next_call, **kw: next_call(request))
        failure = RuntimeError("inert transport failure")
        self.transport.side_effect = failure
        for engine in (self.original, self.engine):
            with self.assertRaises(RuntimeError) as caught:
                self.model(engine)
            self.assertIs(caught.exception, failure)

    def test_opt_in_before_discovery_blocks_missing_gates(self):
        self.engine.enable_mandatory_middleware()
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_missing"):
            self.model()
        self.transport.assert_not_called()

    def test_both_boundaries_required_even_for_one_model_call(self):
        gate = lambda request, next_call, **kw: next_call(request)
        self.register("llm_execution", gate)
        self.engine.require_middleware("llm_execution", gate)
        self.assertFalse(self.engine.validate_mandatory_middleware())
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.model()
        self.transport.assert_not_called()

    def test_bound_method_registration_uses_equality_not_object_identity(self):
        class Gate:
            def run(self, request, next_call, **kw):
                return next_call(request)
        gate = Gate()
        self.register("llm_execution", gate.run)
        self.engine.require_middleware("llm_execution", gate.run)
        tool = lambda args, next_call, **kw: next_call(args)
        self.register("tool_execution", tool)
        self.engine.require_middleware("tool_execution", tool)
        self.assertTrue(self.engine.validate_mandatory_middleware())
        self.assertEqual(self.model(), "synthetic result")

    def test_registration_cannot_replace_a_required_callback(self):
        self.require_gates()
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "binding_replaced"):
            self.engine.require_middleware("llm_execution", lambda **kw: None)

    def test_removal_replacement_and_duplicate_registration_block(self):
        for replacement in ([], [lambda **kw: None], None):
            with self.subTest(replacement=replacement):
                self.manager._middleware["llm_execution"] = []
                if not hasattr(self, "model_gate"):
                    self.require_gates()
                self.manager._middleware["llm_execution"] = (
                    replacement if replacement is not None else [self.model_gate, self.model_gate]
                )
                with self.assertRaises(self.engine.MandatoryMiddlewareError):
                    self.model()
        self.transport.assert_not_called()

    def test_plugin_manager_reset_does_not_disable_mandatory_mode(self):
        self.require_gates()
        self.manager._middleware.clear()
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.model()
        self.transport.assert_not_called()

    def test_gate_failure_is_secret_safe_and_never_executes(self):
        def deny(**kw):
            raise ValueError("sensitive fixture value")
        self.require_gates(model=deny)
        with self.assertNoLogs(self.engine.logger, "WARNING"):
            with self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
                self.model()
        self.assertEqual(str(caught.exception), "mandatory_middleware.callback_failed")
        self.assertTrue(caught.exception.__suppress_context__)
        self.transport.assert_not_called()

    def test_tool_failure_never_executes(self):
        def deny(**kw):
            raise RuntimeError("synthetic policy failure")
        self.require_gates(tool=deny)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.engine.run_tool_execution_middleware("write_file", {"path": "synthetic"}, self.transport)
        self.transport.assert_not_called()

    def test_authorization_sees_final_transformed_payload(self):
        seen = []
        def gate(request, next_call, **kw):
            seen.append(request["model"])
            return next_call(request)
        self.require_gates(model=gate)
        # A later ordinary registration must still run before the required gate.
        self.register("llm_execution", lambda request, next_call, **kw: next_call({**request, "model": "changed"}))
        self.model()
        self.assertEqual(seen, ["changed"])
        self.assertEqual(self.transport.call_args.args[0]["model"], "changed")

    def test_ordinary_short_circuit_cannot_skip_required_gate(self):
        self.require_gates()
        self.register("llm_execution", lambda **kw: "pretend healthy")
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_bypassed"):
            self.model()
        self.transport.assert_not_called()

    def test_outer_callback_cannot_swallow_denial(self):
        def deny(**kw):
            raise ValueError("synthetic denial")
        self.require_gates(model=deny)
        def swallow(request, next_call, **kw):
            try:
                return next_call(request)
            except Exception:
                return "pretend healthy"
        self.register("llm_execution", swallow)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.model()
        self.transport.assert_not_called()

    def test_gate_removed_during_authorization_blocks_before_transport(self):
        def gate(request, next_call, **kw):
            self.manager._middleware.clear()
            return next_call(request)
        self.require_gates(model=gate)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.model()
        self.transport.assert_not_called()

    def test_post_execution_validation_failure_withholds_result(self):
        def gate(request, next_call, **kw):
            next_call(request)
            raise RuntimeError("synthetic result validation failure")
        self.require_gates(model=gate)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.model()
        self.transport.assert_called_once()

    def test_next_call_cannot_execute_twice_even_if_error_is_swallowed(self):
        def gate(request, next_call, **kw):
            result = next_call(request)
            try:
                next_call(request)
            except Exception:
                pass
            return result
        self.require_gates(model=gate)
        with self.assertRaises(self.engine.MandatoryMiddlewareError):
            self.model()
        self.transport.assert_called_once()

    def test_saved_callback_cannot_execute_outside_authorization_scope(self):
        saved = []
        def gate(request, next_call, **kw):
            saved.append(next_call)
            return "no execution"
        self.require_gates(model=gate)
        with self.assertRaisesRegex(self.engine.MandatoryMiddlewareError, "gate_bypassed"):
            self.model()
        with self.assertRaises(Exception):
            saved[0](self.request)
        self.transport.assert_not_called()

    def test_mandatory_mode_preserves_normal_transport_failure(self):
        self.require_gates()
        failure = RuntimeError("synthetic SDK failure")
        self.transport.side_effect = failure
        with self.assertRaises(RuntimeError) as caught:
            self.model()
        self.assertIs(caught.exception, failure)
        self.transport.assert_called_once()

    def setup_maya_gates(self):
        data = valid_config_mapping()
        data["deployment"]["data_dir"] = self.tmp.name
        data["llm"].update(mode="customer_owned", provider="openai", model="synthetic-model", endpoint="https://api.openai.com/v1")
        gateway = PolicyAuthorizationGateway((
            PolicyRule("model.egress", target="model:openai", operation="infer", actor_id="alice"),
        ))
        self.audit = Mock()
        plugin = MayaGovernancePlugin(config_from_mapping(data), gateway, self.audit)
        # Exercise real callbacks without pretending the partial runtime passes
        # Maya's full startup compatibility guard or activating an installation.
        self.require_gates(model=plugin.model_execution, tool=plugin.tool_execution)

    def maya_model(self):
        return self.engine.run_llm_execution_middleware(
            self.request, self.transport, provider="openai", base_url="https://api.openai.com/v1",
        )

    def test_real_maya_gateway_allows_each_authenticated_call(self):
        self.setup_maya_gates()
        with bind_request_identity("alice"):
            for _ in range(3):
                self.assertEqual(self.maya_model(), "synthetic result")
        self.assertEqual(self.transport.call_count, 3)
        self.assertEqual(self.audit.write.call_count, 3)

    def test_real_maya_denial_never_reaches_transport(self):
        self.setup_maya_gates()
        with bind_request_identity("unapproved-user"):
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.maya_model()
        self.transport.assert_not_called()

    def test_real_maya_audit_failure_never_reaches_transport(self):
        self.setup_maya_gates()
        self.audit.write.side_effect = OSError("sensitive audit error fixture")
        with bind_request_identity("alice"):
            with self.assertRaises(self.engine.MandatoryMiddlewareError) as caught:
                self.maya_model()
        self.assertNotIn("sensitive", str(caught.exception))
        self.transport.assert_not_called()

    def test_unknown_worker_identity_is_denied_not_invented(self):
        self.setup_maya_gates()
        with bind_request_identity("alice"), ThreadPoolExecutor(max_workers=1) as pool:
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                pool.submit(self.maya_model).result()
        self.transport.assert_not_called()

    def test_real_maya_unbounded_tool_remains_denied(self):
        self.setup_maya_gates()
        with bind_request_identity("alice"):
            with self.assertRaises(self.engine.MandatoryMiddlewareError):
                self.engine.run_tool_execution_middleware("terminal", {"command": "synthetic"}, self.transport)
        self.transport.assert_not_called()


if __name__ == "__main__":
    unittest.main()
