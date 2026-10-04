"""Create authority preflight tests, not native transition qualification."""
import asyncio
from contextvars import copy_context
from dataclasses import replace
import json
from pathlib import Path
from threading import Event, Thread
import tempfile
import unittest
from unittest.mock import patch

from project_maya.audit import LocalJsonlAuditSink, NullAuditSink
from project_maya.governance import (
    AuthorizationResult, GovernanceDecision, PolicyAuthorizationGateway, PolicyRule,
)
from project_maya.hermes_plugins.governance import GovernanceBoundaryError, RequestIdentity, _session_write
from project_maya.hermes_plugins import session_transitions as candidate
from project_maya.hermes_plugins.session_requests import ACKNOWLEDGEMENT


class TestCreateSessionAuthority(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.database = self.root / "native.db"
        self.database.touch()  # Path validation only; native schema tests are separate.
        self.owner = RequestIdentity("alice", "confidential")
        self.audit = LocalJsonlAuditSink(self.root / "audit.jsonl")
        self.rules = (
            PolicyRule("session.read", operation="route_state", actor_id="alice"),
            PolicyRule("session.transition", operation="create", actor_id="alice"),
            PolicyRule("session.write", operation="create", actor_id="alice"),
        )
        self.binding = self.make_binding()

    def make_binding(self, **overrides):
        args = dict(owner=self.owner, instance_id="test-instance", database=self.database,
                    route_slot="telegram:test-private-slot", binding_version=1,
                    gateway=PolicyAuthorizationGateway(self.rules), audit_sink=self.audit,
                    acknowledgement=ACKNOWLEDGEMENT)
        return candidate.CandidateCreateSessionBinding(**(args | overrides))

    def test_host_allocates_unique_create_only_descriptors_without_conversation_authority(self):
        descriptors = []
        for _ in range(2):
            with self.binding.authenticated_create(self.owner) as authority:
                descriptor = authority.descriptor
                descriptors.append(descriptor)
                self.assertEqual(descriptor.principal, "alice")
                self.assertEqual(descriptor.expected_route_version, 0)
                self.assertEqual(descriptor.operation, "create")
                self.assertIsNone(_session_write.get())
                self.assertRegex(descriptor.digest, r"^sha256:[0-9a-f]{64}$")
        self.assertNotEqual(descriptors[0].target_session, descriptors[1].target_session)
        self.assertNotEqual(descriptors[0].correlation_id, descriptors[1].correlation_id)
        self.assertEqual(self.database.read_bytes(), b"")

    def test_owner_and_classification_must_match(self):
        for identity in (None, RequestIdentity("mallory", "confidential"), RequestIdentity("alice", "public")):
            with self.subTest(identity=identity), self.assertRaises(GovernanceBoundaryError):
                with self.binding.authenticated_create(identity):
                    self.fail("wrong identity reached scope")
        self.assertFalse(self.audit.path.exists())

    def test_independent_permissions_required(self):
        for rules in ((), self.rules[:1], self.rules[1:], self.rules[:2]):
            binding = self.make_binding(gateway=PolicyAuthorizationGateway(rules))
            with self.subTest(rules=rules), self.assertRaisesRegex(GovernanceBoundaryError, "transition_denied"):
                with binding.authenticated_create(self.owner):
                    self.fail("incomplete policy reached scope")

    def test_failures_and_nonexact_allows_are_secret_safe(self):
        class Gateway:
            def authorize(self, request):
                raise RuntimeError("synthetic-private-provider-value")
        with self.assertRaisesRegex(GovernanceBoundaryError, "^governance.authorization_unavailable$"):
            with self.make_binding(gateway=Gateway()).authenticated_create(self.owner):
                pass
        class ConstrainedGateway:
            def authorize(self, request):
                return AuthorizationResult(GovernanceDecision.ALLOW, "private", constraints=("narrow",))
        with self.assertRaisesRegex(GovernanceBoundaryError, "transition_denied"):
            with self.make_binding(gateway=ConstrainedGateway()).authenticated_create(self.owner):
                pass

    def test_audit_failure_never_yields_authority(self):
        class BrokenAudit:
            def write(self, record):
                raise RuntimeError("synthetic-private-audit-value")
        with self.assertRaisesRegex(GovernanceBoundaryError, "^governance.audit_unavailable$"):
            with self.make_binding(audit_sink=BrokenAudit()).authenticated_create(self.owner):
                self.fail("audit failure yielded authority")

    def test_forged_or_copied_descriptor_rejected(self):
        with self.binding.authenticated_create(self.owner) as authority:
            for descriptor in (replace(authority.descriptor), replace(authority.descriptor, operation="reset"),
                               replace(authority.descriptor, target_session="foreign-session")):
                with self.subTest(descriptor=descriptor), self.assertRaises(GovernanceBoundaryError):
                    authority.authorize(self.owner, descriptor)

    def test_descriptor_cannot_be_replaced_and_changed_host_binding_denies(self):
        with self.binding.authenticated_create(self.owner) as authority:
            with self.assertRaises(AttributeError):
                authority.descriptor = replace(authority.descriptor, target_session="foreign")
            self.binding.binding_version += 1
            with self.assertRaises(GovernanceBoundaryError):
                authority.authorize(self.owner, authority.descriptor)

    def test_other_task_and_pending_cancellation_deny(self):
        async def exercise():
            with self.binding.authenticated_create(self.owner) as authority:
                async def other_task():
                    with self.assertRaises(GovernanceBoundaryError):
                        authority.authorize(self.owner, authority.descriptor)
                await asyncio.create_task(other_task())
                asyncio.current_task().cancel()
                with self.assertRaises(GovernanceBoundaryError):
                    authority.authorize(self.owner, authority.descriptor)
                try:
                    await asyncio.sleep(0)
                except asyncio.CancelledError:
                    pass
        asyncio.run(exercise())

    def test_expiry_and_scope_exit_revoke(self):
        with patch.object(candidate, "monotonic", return_value=100) as clock:
            with self.binding.authenticated_create(self.owner) as authority:
                clock.return_value = 220
                with self.assertRaises(GovernanceBoundaryError):
                    authority.authorize(self.owner, authority.descriptor)
        with self.assertRaises(GovernanceBoundaryError):
            authority.authorize(self.owner, authority.descriptor)

    def test_commit_guard_consumes_even_failed_attempt(self):
        with self.binding.authenticated_create(self.owner) as authority:
            with self.assertRaises(RuntimeError):
                with authority.commit_guard(self.owner, authority.descriptor):
                    raise RuntimeError("fixture transaction failed")
            with self.assertRaises(GovernanceBoundaryError):
                with authority.commit_guard(self.owner, authority.descriptor):
                    self.fail("replayed guard")

    def test_unknown_operation_never_gains_authority_even_with_allow_policy(self):
        with self.binding.authenticated_create(self.owner) as authority:
            descriptor = replace(authority.descriptor, operation="reset")
            forged = candidate.CandidateCreateSessionAuthority(self.binding, descriptor, 120)
            with self.assertRaises(GovernanceBoundaryError):
                forged.authorize(self.owner, descriptor)

    def test_commit_guard_reauthorizes_policy(self):
        with self.binding.authenticated_create(self.owner) as authority:
            self.binding.gateway = PolicyAuthorizationGateway(())
            with self.assertRaisesRegex(GovernanceBoundaryError, "transition_denied"):
                with authority.commit_guard(self.owner, authority.descriptor):
                    self.fail("revoked policy reached commit")

    def test_revocation_before_guard_prevents_commit(self):
        with self.binding.authenticated_create(self.owner) as authority:
            thread = Thread(target=authority.revoke)
            thread.start()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            with self.assertRaises(GovernanceBoundaryError):
                with authority.commit_guard(self.owner, authority.descriptor):
                    self.fail("revoked authority reached commit")

    def test_revocation_serializes_after_entered_guard(self):
        with self.binding.authenticated_create(self.owner) as authority:
            started, finished = Event(), Event()
            def revoke():
                started.set()
                authority.revoke()
                finished.set()
            with authority.commit_guard(self.owner, authority.descriptor):
                thread = Thread(target=revoke)
                thread.start()
                self.assertTrue(started.wait(2))
                self.assertFalse(finished.wait(0.05))
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertTrue(finished.is_set())

    def test_context_copy_to_other_thread_cannot_expand_authority(self):
        with self.binding.authenticated_create(self.owner) as authority:
            failures = []
            def check():
                try:
                    authority.authorize(self.owner, authority.descriptor)
                except GovernanceBoundaryError as failure:
                    failures.append(str(failure))
            context = copy_context()
            thread = Thread(target=lambda: context.run(check))
            thread.start()
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
            self.assertEqual(failures, ["governance.transition_context_invalid"])

    def test_same_host_scope_cannot_overlap(self):
        with self.binding.authenticated_create(self.owner):
            with self.assertRaisesRegex(GovernanceBoundaryError, "transition_busy"):
                with self.binding.authenticated_create(self.owner):
                    pass
        with self.binding.authenticated_create(self.owner):
            pass

    def test_invalid_binding_inputs(self):
        for override in ({"timeout_seconds": value} for value in (None, True, 0, float("nan"), float("inf"))):
            with self.subTest(override=override), self.assertRaises(GovernanceBoundaryError):
                self.make_binding(**override)
        for override in ({"binding_version": True}, {"binding_version": 0}, {"audit_sink": NullAuditSink()},
                         {"database": self.root / "missing.db"}, {"database": self.root},
                         {"acknowledgement": "production"}, {"route_slot": "untrusted\nslot"}):
            with self.subTest(override=override), self.assertRaises(GovernanceBoundaryError):
                self.make_binding(**override)

    def test_audit_contains_only_fixed_codes_and_hashed_selectors(self):
        with self.binding.authenticated_create(self.owner) as authority:
            descriptor = authority.descriptor
        records = [json.loads(line) for line in self.audit.path.read_text().splitlines()]
        self.assertEqual(len(records), 3)
        raw = self.audit.path.read_text()
        for value in (descriptor.database, descriptor.route_slot, descriptor.target_session, descriptor.correlation_id):
            self.assertNotIn(value, raw)
        self.assertTrue(all(record["metadata"]["qualification"] == "source_preflight_only" for record in records))
