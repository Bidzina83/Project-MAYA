"""G1 contract foundations; not complete native caller qualification."""
import asyncio
from contextvars import copy_context
from pathlib import Path
import unittest
from unittest.mock import patch

from project_maya.hermes_plugins import governance as g


class TestRequestLifecycle(unittest.TestCase):
    def scope(self, **kwargs):
        return g.bind_session_write("request-1", "fixed-session", Path("synthetic.db"),
                                    frozenset({"append"}), **kwargs)

    def test_versioned_context_and_normal_exit(self):
        with g.bind_request_identity("operator", "restricted"):
            with self.scope(timeout_seconds=120) as context:
                self.assertEqual(context.contract, "project-maya.request-lifecycle.v1")
                self.assertEqual(context.identity, g.RequestIdentity("operator", "restricted"))
                self.assertEqual(context.operations, frozenset({"append"}))
                self.assertTrue(context.lease.is_active)
                captured = copy_context()
            self.assertFalse(captured.run(lambda: g._session_write.get().lease.is_active))
            self.assertEqual(context.lease.termination, "completed")
        self.assertIsNone(g._session_write.get())

    def test_deadline_revokes_root_and_existing_descendants(self):
        with patch.object(g, "monotonic", return_value=100) as clock:
            with g.bind_request_identity("operator"):
                with self.scope(timeout_seconds=5) as context:
                    child = g._SessionWriteLease(parent=context.lease)
                    self.assertTrue(child.is_active)
                    clock.return_value = 105
                    self.assertFalse(child.is_active)
                    self.assertEqual(context.lease.termination, "timeout")
                    clock.return_value = 101
                    self.assertFalse(context.lease.is_active)
            self.assertEqual(context.lease.termination, "timeout")

    def test_exception_and_cancellation_propagate_with_revoked_lease(self):
        for error, reason in ((RuntimeError("synthetic failure"), "failed"),
                              (asyncio.CancelledError(), "cancelled")):
            with self.subTest(reason=reason), g.bind_request_identity("operator"):
                with self.assertRaises(type(error)):
                    with self.scope(timeout_seconds=5) as context:
                        raise error
                self.assertFalse(context.lease.is_active)
                self.assertEqual(context.lease.termination, reason)

    def test_expired_scope_exit_is_not_labelled_completed_without_an_effect_check(self):
        with patch.object(g, "monotonic", return_value=100) as clock:
            with g.bind_request_identity("operator"):
                with self.scope(timeout_seconds=5) as context:
                    clock.return_value = 105
                self.assertEqual(context.lease.termination, "timeout")

    def test_explicit_host_revocation_is_terminal(self):
        with g.bind_request_identity("operator"):
            with self.scope(timeout_seconds=5) as context:
                context.lease.revoke("cancelled")
                self.assertFalse(context.lease.is_active)
            self.assertEqual(context.lease.termination, "cancelled")

    def test_receiver_revocation_invalidates_root_and_siblings(self):
        with g.bind_request_identity("operator"):
            with self.scope(timeout_seconds=5) as context:
                child = g._SessionWriteLease(parent=context.lease)
                receiver = g._SessionWriteLease(parent=child)
                sibling = g._SessionWriteLease(parent=context.lease)
                receiver.revoke_request("cancelled")
                self.assertFalse(context.lease.is_active)
                self.assertFalse(child.is_active)
                self.assertFalse(sibling.is_active)
                self.assertEqual(context.lease.termination, "cancelled")

    def test_request_revocation_preserves_prior_timeout_reason(self):
        with g.bind_request_identity("operator"):
            with self.scope(timeout_seconds=5) as context:
                context.lease.revoke("timeout")
                child = g._SessionWriteLease(parent=context.lease)
                child.revoke_request("cancelled")
                self.assertEqual(context.lease.termination, "timeout")

    def test_invalid_timeouts_fail_before_context_is_bound(self):
        for value in (True, False, 0, -1, 3601, 10**1000, float("inf"), float("nan"), "120"):
            with self.subTest(value=value), g.bind_request_identity("operator"):
                with self.assertRaisesRegex(g.GovernanceBoundaryError, "request_timeout_invalid"):
                    with self.scope(timeout_seconds=value):
                        self.fail("invalid timeout entered scope")
                self.assertIsNone(g._session_write.get())


if __name__ == "__main__":
    unittest.main()
