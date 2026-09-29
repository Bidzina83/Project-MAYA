import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

from project_maya.adapters.hermes import HermesRuntimeAdapter
from project_maya.config import config_from_mapping
from project_maya.governance import AuthorizationResult, GovernanceDecision, PolicyAuthorizationGateway, PolicyRule
from project_maya.hermes_plugins.governance import (
    CONTRACT_VERSION, REQUIRED_CAPABILITIES, GovernanceBoundaryError,
    MayaGovernancePlugin, bind_request_identity, require_runtime_contract,
)
from tests.test_phase0_contracts import valid_config_mapping


class TestHermesGovernancePlugin(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        data = valid_config_mapping()
        data["deployment"]["data_dir"] = self.tmp.name
        data["llm"].update(mode="customer_owned", provider="openai", model="test-model", endpoint="https://api.openai.com/v1")
        self.config = config_from_mapping(data)
        self.audit = Mock()
        self.gateway = PolicyAuthorizationGateway((
            PolicyRule("model.egress", target="model:openai", operation="infer", actor_id="alice"),
            PolicyRule("memory.read", operation="search", actor_id="alice"),
            PolicyRule("file.read", operation="read", actor_id="alice"),
        ))
        self.plugin = MayaGovernancePlugin(self.config, self.gateway, self.audit)
        self.context = {"provider": "openai", "base_url": "https://api.openai.com/v1"}
        self.request = {"model": "test-model", "messages": [{"role": "user", "content": "Synthetic business question"}]}

    def model(self, next_call, **context):
        return self.plugin.model_execution(request=self.request, next_call=next_call, **(self.context | context))

    def test_contract_rejects_current_unqualified_runtime(self):
        with self.assertRaisesRegex(GovernanceBoundaryError, "contract_unsupported"):
            require_runtime_contract(SimpleNamespace())

    def test_contract_requires_all_execution_paths(self):
        for capability in REQUIRED_CAPABILITIES:
            with self.subTest(capability=capability):
                module = self.contract()
                module.MAYA_GOVERNANCE_CONTRACT["capabilities"] = list(REQUIRED_CAPABILITIES - {capability})
                with self.assertRaisesRegex(GovernanceBoundaryError, "contract_incomplete"):
                    require_runtime_contract(module)

    @staticmethod
    def contract():
        return SimpleNamespace(
            MAYA_GOVERNANCE_CONTRACT={"version": CONTRACT_VERSION, "capabilities": list(REQUIRED_CAPABILITIES)},
            run_llm_execution_middleware=Mock(), run_tool_execution_middleware=Mock(),
            require_middleware=Mock(), validate_mandatory_middleware=Mock(return_value=True),
        )

    def test_registers_native_mandatory_execution_adapters(self):
        ctx, module = Mock(), self.contract()
        self.plugin.register(ctx, runtime_module=module)
        self.assertEqual(ctx.register_middleware.call_count, 2)
        self.assertEqual(module.require_middleware.call_count, 2)
        self.assertEqual(ctx.register_middleware.call_args_list[0].args[0], "llm_execution")

    def test_startup_guard_blocks_before_factory_construction(self):
        factory = Mock()
        guard = Mock(side_effect=GovernanceBoundaryError("governance.hermes_contract_unsupported"))
        adapter = HermesRuntimeAdapter(factory=factory, startup_guard=guard)
        self.assertFalse(adapter.compatibility().compatible)
        with self.assertRaises(GovernanceBoundaryError):
            adapter.start(agent_name="maya")
        factory.assert_not_called()

    def test_model_requires_trusted_identity_ignores_spoofed_actor(self):
        execute = Mock()
        with self.assertRaisesRegex(GovernanceBoundaryError, "identity_missing"):
            self.model(execute, actor_id="alice")
        with bind_request_identity("mallory"):
            with self.assertRaisesRegex(GovernanceBoundaryError, "action_denied"):
                self.model(execute, actor_id="alice")
        execute.assert_not_called()

    def test_each_model_request_is_authorized(self):
        execute = Mock(return_value="synthetic response")
        with bind_request_identity("alice"):
            for _ in range(3):
                self.assertEqual(self.model(execute), "synthetic response")
        self.assertEqual(execute.call_count, 3)
        self.assertEqual(self.audit.write.call_count, 3)

    def test_changed_endpoint_provider_or_model_never_executes(self):
        for context in ({"base_url": "https://other.example/v1"}, {"provider": "other"}):
            with self.subTest(context=context), bind_request_identity("alice"):
                execute = Mock()
                with self.assertRaisesRegex(GovernanceBoundaryError, "route_mismatch"):
                    self.model(execute, **context)
                execute.assert_not_called()
        self.request["model"] = "other-model"
        with bind_request_identity("alice"), self.assertRaises(GovernanceBoundaryError):
            self.model(Mock())

    def test_policy_and_audit_failures_prevent_execution(self):
        for dependency in ("gateway", "audit"):
            with self.subTest(dependency=dependency), bind_request_identity("alice"):
                execute = Mock()
                broken = Mock()
                getattr(broken, "authorize" if dependency == "gateway" else "write").side_effect = RuntimeError("sensitive fixture text")
                with patch.object(self.plugin, dependency, broken):
                    reason = "authorization_unavailable" if dependency == "gateway" else "audit_unavailable"
                    with self.assertRaisesRegex(GovernanceBoundaryError, reason) as exc:
                        self.model(execute)
                self.assertNotIn("sensitive", str(exc.exception))
                execute.assert_not_called()

    def test_approval_and_redaction_decisions_do_not_execute(self):
        for decision in GovernanceDecision:
            if decision is GovernanceDecision.ALLOW:
                continue
            with self.subTest(decision=decision), bind_request_identity("alice"):
                execute = Mock()
                gateway = Mock()
                gateway.authorize.return_value = AuthorizationResult(decision, "fixture")
                with patch.object(self.plugin, "gateway", gateway), self.assertRaises(GovernanceBoundaryError):
                    self.model(execute)
                execute.assert_not_called()

    def test_secrets_in_outbound_context_are_blocked_without_logging(self):
        secret = "sk-proj-" + "x" * 32
        self.request["messages"][0]["content"] = secret
        execute = Mock()
        with bind_request_identity("alice"), self.assertRaisesRegex(GovernanceBoundaryError, "sensitive_payload"):
            self.model(execute)
        execute.assert_not_called()
        self.assertNotIn(secret, self.audit.write.call_args.args[0].to_json())

    def test_unknown_and_unbounded_tools_are_denied(self):
        for tool in ("terminal", "execute_code", "delegate_task", "cronjob", "unknown_connector"):
            with self.subTest(tool=tool), bind_request_identity("alice"):
                execute = Mock()
                with self.assertRaisesRegex(GovernanceBoundaryError, "tool_unmapped"):
                    self.plugin.tool_execution(tool_name=tool, args={}, next_call=execute)
                execute.assert_not_called()

    def test_memory_search_uses_existing_gateway(self):
        execute = Mock(return_value='{"records": []}')
        with bind_request_identity("alice"):
            result = self.plugin.tool_execution(tool_name="maya_business_memory_search", args={"query": "synthetic"}, next_call=execute)
        self.assertEqual(result, '{"records": []}')
        self.assertEqual(self.audit.write.call_count, 2)

    def test_files_are_canonicalized_and_confined(self):
        root = Path(self.tmp.name) / "documents"
        root.mkdir()
        execute = Mock(return_value="synthetic document")
        with bind_request_identity("alice"):
            self.plugin.tool_execution(tool_name="read_file", args={"path": "note.txt"}, next_call=execute)
            self.assertEqual(execute.call_args.args[0]["path"], str((root / "note.txt").resolve()))
            execute.reset_mock()
            with self.assertRaisesRegex(GovernanceBoundaryError, "outside_root"):
                self.plugin.tool_execution(tool_name="read_file", args={"path": "../outside.txt"}, next_call=execute)
            execute.assert_not_called()

    def test_secret_tool_result_is_not_returned_or_audited(self):
        secret = "sk-proj-" + "y" * 32
        with bind_request_identity("alice"), self.assertRaisesRegex(GovernanceBoundaryError, "sensitive_payload"):
            self.plugin.tool_execution(tool_name="maya_business_memory_search", args={}, next_call=Mock(return_value=secret))
        records = [call.args[0].to_json() for call in self.audit.write.call_args_list]
        self.assertNotIn(secret, "".join(records))
        self.assertEqual(len(records), 2)

    def test_allow_with_constraints_is_not_unconditional_permission(self):
        self.gateway = Mock()
        self.gateway.authorize.return_value = AuthorizationResult(
            GovernanceDecision.ALLOW, "fixture", constraints=("require-approval",),
        )
        self.plugin.gateway = self.gateway
        execute = Mock()
        with bind_request_identity("alice"), self.assertRaises(GovernanceBoundaryError):
            self.model(execute)
        execute.assert_not_called()

    def test_json_tool_results_with_secret_fields_are_withheld(self):
        with bind_request_identity("alice"), self.assertRaisesRegex(GovernanceBoundaryError, "sensitive_payload"):
            self.plugin.tool_execution(
                tool_name="maya_business_memory_search", args={},
                next_call=Mock(return_value=json.dumps({"access_token": "synthetic-private-value"})),
            )
        self.assertNotIn("synthetic-private-value", "".join(call.args[0].to_json() for call in self.audit.write.call_args_list))

    def test_downstream_boundary_exception_is_secret_safe(self):
        secret = "sk-proj-" + "z" * 32
        execute = Mock(side_effect=GovernanceBoundaryError(secret))
        with bind_request_identity("alice"):
            with self.assertRaisesRegex(GovernanceBoundaryError, "authorization_unavailable") as exc:
                self.model(execute)
        self.assertNotIn(secret, str(exc.exception))
        self.assertNotIn(secret, "".join(call.args[0].to_json() for call in self.audit.write.call_args_list))

    def test_identity_does_not_leak_between_threads_or_after_request(self):
        def run(actor):
            with bind_request_identity(actor):
                try:
                    self.model(lambda request: "allowed")
                    return "allowed"
                except GovernanceBoundaryError:
                    return "denied"
        with ThreadPoolExecutor(max_workers=2) as executor:
            self.assertEqual(list(executor.map(run, ["alice", "mallory"])), ["allowed", "denied"])
        with self.assertRaisesRegex(GovernanceBoundaryError, "identity_missing"):
            self.model(Mock())


if __name__ == "__main__":
    unittest.main()
