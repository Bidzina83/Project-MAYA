"""Inert probe wiring tests. No native API, sockets or product startup execute."""

import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, mock_open, patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/project_maya/windows_runtime"
spec = importlib.util.spec_from_file_location("maya_screen_check", SOURCE / "containment_check.py")
screen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(screen)


class ContainmentScreenTests(unittest.TestCase):
    def token_probe(self, *, values=None, lengths=None, capacity=8, failure=None, sizing_success=False):
        probe = self.probe()
        probe.k = Mock()
        probe.a = Mock()
        calls = []
        def opened(process, rights, token):
            token._obj.value = 99
            return True
        def query(token, info, buffer, length, returned):
            calls.append((info, length))
            if failure == (info, length):
                return False
            if buffer is None:
                returned._obj.value = capacity
                return sizing_success
            returned._obj.value = (lengths or {}).get(info, length)
            buffer[:4] = (values or {}).get(info, {20: 0, 29: 1, 30: 0}[info]).to_bytes(4, "little")
            return True
        probe.a.OpenProcessToken.side_effect = opened
        probe.a.GetTokenInformation.side_effect = query
        return probe, calls

    def test_token_queries_use_exact_scalars_and_sized_capability_buffer(self):
        for capacity in (4, 8, 24, 4096):
            with self.subTest(capacity=capacity):
                probe, calls = self.token_probe(capacity=capacity)
                with patch.object(screen.ctypes, "get_last_error", return_value=122):
                    self.assertEqual(probe.own_token(), (True, 0, 0))
                self.assertEqual(calls, [(20, 4), (29, 4), (30, 0), (30, capacity)])
                probe.k.CloseHandle.assert_called_once()

    def test_token_scalar_return_length_must_be_exact(self):
        for info in (20, 29):
            for length in (0, 3, 8):
                with self.subTest(info=info, length=length):
                    probe, _ = self.token_probe(lengths={info: length})
                    self.assertEqual(probe.own_token(), (False, 0, 0))
                    probe.k.CloseHandle.assert_called_once()

    def test_token_values_still_require_non_elevated_appcontainer_without_capabilities(self):
        for info, value in ((20, 1), (29, 0), (30, 1)):
            with self.subTest(info=info):
                probe, _ = self.token_probe(values={info: value})
                with patch.object(screen.ctypes, "get_last_error", return_value=122):
                    self.assertEqual(probe.own_token(), (False, 0, 0))
                probe.k.CloseHandle.assert_called_once()

    def test_capability_size_query_is_bounded_and_does_not_retry(self):
        for capacity in (0, 3, 4097):
            with self.subTest(capacity=capacity):
                probe, calls = self.token_probe(capacity=capacity)
                with patch.object(screen.ctypes, "get_last_error", return_value=122):
                    self.assertEqual(probe.own_token(), (False, 0, 0))
                self.assertEqual(calls, [(20, 4), (29, 4), (30, 0)])
        probe, _ = self.token_probe(sizing_success=True)
        self.assertEqual(probe.own_token(), (False, 0, 0))

    def test_capability_return_length_stays_inside_allocated_buffer(self):
        for length in (0, 3, 9):
            probe, _ = self.token_probe(lengths={30: length})
            with patch.object(screen.ctypes, "get_last_error", return_value=122):
                self.assertEqual(probe.own_token(), (False, 0, 0))
            probe.k.CloseHandle.assert_called_once()

    def test_token_query_native_failures_and_exceptions_close_handle(self):
        for failure in ((20, 4), (29, 4), (30, 0)):
            probe, _ = self.token_probe(failure=failure)
            with patch.object(screen.ctypes, "get_last_error", return_value=24):
                self.assertEqual(probe.own_token(), (False, 24, 0))
            probe.k.CloseHandle.assert_called_once()
        probe, _ = self.token_probe()
        probe.a.GetTokenInformation.side_effect = RuntimeError("query fixture failure")
        with self.assertRaises(RuntimeError):
            probe.own_token()
        probe.k.CloseHandle.assert_called_once()

    def test_failed_token_open_does_not_query_or_close_invalid_handle(self):
        probe, _ = self.token_probe()
        probe.a.OpenProcessToken.side_effect = None
        probe.a.OpenProcessToken.return_value = False
        with patch.object(screen.ctypes, "get_last_error", return_value=5):
            self.assertEqual(probe.own_token(), (False, 5, 0))
        probe.a.GetTokenInformation.assert_not_called()
        probe.k.CloseHandle.assert_not_called()

    def probe(self):
        probe = object.__new__(screen.Probes)
        probe.plan = {"nonce": "a" * 32, "host_pid": 1, "protected": {name: name for name in
                      ("document", "memory", "business", "policy", "audit", "secret")},
                      "runtime_canary": "runtime", "routes": {name: name for name in
                      ("absolute", "traversal", "ads", "symlink", "junction")}}
        probe.rows = []
        probe.udp = []
        probe.deadline = float("inf")
        probe.save = Mock()
        return probe

    def test_duplicate_plan_keys_rejected(self):
        with self.assertRaises(ValueError):
            json.loads('{"nonce":"a","nonce":"b"}', object_pairs_hook=screen.unique)

    def test_all_47_child_cases_are_fixed_and_unique(self):
        probe = self.probe()
        calls = []
        probe.one = lambda identifier, action, allowed=False: calls.append((identifier, allowed))
        probe.run()
        self.assertEqual(len(calls), 47)
        self.assertEqual(len(set(identifier for identifier, _ in calls)), 47)
        self.assertEqual(sum(allowed for _, allowed in calls), 5)
        for store in ("document", "memory", "business", "policy", "audit", "secret"):
            for operation in ("read", "write", "create", "delete"):
                self.assertIn((f"C02.{store}.{operation}", False), calls)
        self.assertIn(("C07.mapping", False), calls)
        self.assertIn(("C06.spawn", False), calls)

    def test_unexpected_success_stops_and_preserves_row(self):
        probe = self.probe()
        with patch.object(screen.os.path, "exists", return_value=False):
            with self.assertRaisesRegex(RuntimeError, "unauthorized_effect"):
                probe.one("C02.document.read", lambda: (True, 0, 32))
        self.assertEqual(probe.rows[0]["outcome"], "effect")
        probe.save.assert_called_once()

    def test_host_stop_and_deadline_prevent_next_operation(self):
        probe = self.probe()
        operation = Mock()
        with patch.object(screen.os.path, "exists", return_value=True):
            with self.assertRaises(RuntimeError):
                probe.one("next", operation)
        probe.deadline = 0
        with patch.object(screen.os.path, "exists", return_value=False):
            with self.assertRaises(TimeoutError):
                probe.one("next", operation)
        operation.assert_not_called()

    def test_timeout_exception_is_inconclusive_not_denied(self):
        probe = self.probe()
        with patch.object(screen.os.path, "exists", return_value=False):
            probe.one("network", Mock(side_effect=TimeoutError()))
        self.assertEqual(probe.rows[0]["outcome"], "inconclusive")

    def test_socket_successful_udp_send_is_measured_not_claimed_denial(self):
        probe = self.probe()
        probe.plan["ports"] = {"4udp": 1234}
        socket = Mock()
        socket.getsockname.return_value = ("127.0.0.1", 45000)
        socket.sendto.return_value = 38
        context = Mock()
        context.__enter__ = Mock(return_value=socket)
        context.__exit__ = Mock(return_value=False)
        with patch.object(screen.socket, "socket", return_value=context):
            self.assertEqual(probe.network(4, screen.socket.SOCK_DGRAM, "send"), (False, 0, 38))
        self.assertEqual(probe.udp[0]["local_port"], 45000)
        self.assertEqual(probe.udp[0]["sent_bytes"], 38)

    def test_udp_bind_failure_does_not_qualify_packet_denial(self):
        probe = self.probe()
        probe.plan["ports"] = {"4udp": 1234}
        stream = Mock()
        error = OSError()
        error.winerror = 10013
        stream.bind.side_effect = error
        context = Mock(__enter__=Mock(return_value=stream), __exit__=Mock(return_value=False))
        with patch.object(screen.socket, "socket", return_value=context):
            self.assertEqual(probe.udp_network(4, "receive"), (False, 0, 0))
        self.assertEqual(probe.udp[0]["bind_error"], 10013)
        stream.recvfrom.assert_not_called()

    def test_udp_receipt_is_effect_and_request_contains_no_address(self):
        probe = self.probe()
        probe.plan["ports"] = {"6udp": 1234}
        stream = Mock()
        stream.getsockname.return_value = ("::1", 45000, 0, 0)
        stream.recvfrom.return_value = (b"received", ("::1", 1234))
        context = Mock(__enter__=Mock(return_value=stream), __exit__=Mock(return_value=False))
        sink = io.BytesIO()
        sink.close = lambda: None
        with patch.object(screen.socket, "socket", return_value=context), patch("builtins.open", return_value=sink) as opened:
            self.assertEqual(probe.udp_network(6, "receive"), (True, 0, 8))
        opened.assert_called_once_with("udp6-request.txt", "xb")
        self.assertEqual(sink.getvalue(), ("a" * 32 + ":45000").encode("ascii"))

    def test_udp_receive_timeout_never_claims_denial(self):
        probe = self.probe()
        probe.plan["ports"] = {"4udp": 1234}
        stream = Mock()
        stream.getsockname.return_value = ("127.0.0.1", 45000)
        stream.recvfrom.side_effect = TimeoutError()
        context = Mock(__enter__=Mock(return_value=stream), __exit__=Mock(return_value=False))
        with patch.object(screen.socket, "socket", return_value=context), patch("builtins.open", mock_open()):
            self.assertEqual(probe.udp_network(4, "receive"), (False, 0, 0))

    def test_tcp_connection_success_remains_effect_if_send_fails(self):
        probe = self.probe()
        probe.plan["ports"] = {"4tcp": 1234}
        socket = Mock()
        socket.send.side_effect = OSError()
        context = Mock()
        context.__enter__ = Mock(return_value=socket)
        context.__exit__ = Mock(return_value=False)
        with patch.object(screen.socket, "socket", return_value=context):
            self.assertEqual(probe.network(4, screen.socket.SOCK_STREAM, "connect"), (True, 0, 0))

    def test_report_is_bounded_and_attempt_bound(self):
        probe = self.probe()
        del probe.save
        sink = io.BytesIO()
        sink.close = lambda: None
        with patch("builtins.open", return_value=sink) as opened:
            probe.save()
        opened.assert_called_once_with("screen-result.json", "wb")
        self.assertEqual(json.loads(sink.getvalue())["nonce"], "a" * 32)
        probe.rows = [{"id": "x" * screen.LIMIT}]
        with patch("builtins.open") as opened:
            with self.assertRaisesRegex(ValueError, "report_size"):
                probe.save()
            opened.assert_not_called()

    def test_wrong_platform_never_instantiates_native_probes(self):
        with patch.object(screen.sys, "platform", "not-windows"), patch.object(screen, "Probes") as probes:
            self.assertEqual(screen.main(), 2)
            probes.assert_not_called()

    def test_host_wires_setup_before_resume_and_cleanup_before_revocation(self):
        host = (SOURCE / "ProtectedPython.cs").read_text()
        self.assertLess(host.index("screen.Prepare();"), host.index("isolation.Start("))
        self.assertLess(host.index("screen.WritePlan("), host.index("isolation.ResumeAndWait();"))
        self.assertLess(host.index("isolation.Stop();"), host.index("screen.Collect(record)"))
        self.assertLess(host.index("screen.Cleanup();"), host.index("ProductFiles.Revoke("))
        self.assertIn('record["screen_independent_cleanup_verified"] = false;', host)
        self.assertIn('{"containment_qualified", false}', host)

    def test_ads_creation_and_readback_use_fixed_native_handle_path(self):
        host = (SOURCE / "ContainmentScreen.cs").read_text()
        self.assertIn('Path = BasePath + ":maya-screen";', host)
        self.assertIn('ProductFiles.NoLinks(request.BasePath);', host)
        self.assertIn('CreateFileW(request.Path, request.Access, AdsRequest.Share,', host)
        self.assertIn('new SafeFileHandle(raw, true)', host)
        self.assertIn('new FileStream(handle, write ? FileAccess.Write : FileAccess.Read)', host)
        self.assertIn('using (var ads = OpenAds(directory, true))', host)
        self.assertIn('using (var ads = OpenAds(directory, false))', host)
        self.assertNotIn('new FileStream(document + ":maya-screen"', host)
        self.assertNotIn('new FileStream(Path.Combine(fixture, "document", "canary.txt:maya-screen")', host)
        self.assertIn('new byte[33]', host)

    def test_error_reporting_keeps_failure_stage_separate_from_cleanup(self):
        host = (SOURCE / "ProtectedPython.cs").read_text()
        for prefix in ("screen_failure", "screen_evidence_failure", "screen_cleanup_failure"):
            self.assertIn(f'RecordStageFailure(record, "{prefix}", screen.Stage, error);', host)
        screen_host = (SOURCE / "ContainmentScreen.cs").read_text()
        for stage in ("ads_create", "ads_readback", "mapping_create", "junction_create"):
            self.assertIn(f'Stage = "{stage}";', screen_host)


if __name__ == "__main__":
    unittest.main()
