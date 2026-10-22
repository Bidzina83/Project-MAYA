"""Inert state-entry fixtures. Never import Hermes, SDK or bundled native code."""
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "src/project_maya/windows_runtime"
spec = importlib.util.spec_from_file_location("maya_state_probe", SOURCE / "hermes_state_check.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class FixtureClosed(Exception):
    pass


class FixtureConnection:
    def __init__(self, path):
        self.path = path
        self.closed = False
        self.mode = "wal"

    def execute(self, sql):
        if self.closed:
            raise FixtureClosed()
        if sql == "PRAGMA database_list":
            return SimpleNamespace(fetchall=lambda: [(0, "main", str(self.path))])
        if sql == "PRAGMA journal_mode":
            return SimpleNamespace(fetchone=lambda: (self.mode,))
        if sql == "SELECT 1":
            return None
        raise AssertionError("unexpected fixture query")


class FixtureDB:
    def __init__(self, db_path, read_only=False, shared=None):
        self.db_path, self.read_only = db_path, read_only
        self.shared = shared if shared is not None else {"session": None, "messages": []}
        self._conn = FixtureConnection(db_path)
        self._fts_enabled = self._trigram_available = False
        self.close_calls = 0

    def create_session(self, session_id, source, **kwargs):
        self.shared["session"] = dict(id=session_id, source=source, model=kwargs["model"],
            message_count=0, tool_call_count=0, ended_at=None, end_reason=None)
        return session_id

    def append_message(self, session_id, role, content=None):
        row_id = len(self.shared["messages"]) + 1
        self.shared["messages"].append(dict(id=row_id, session_id=session_id, role=role, content=content))
        self.shared["session"]["message_count"] += 1
        return row_id

    def get_session(self, session_id):
        return self.shared["session"]

    def get_messages(self, session_id, include_inactive=False):
        return self.shared["messages"]

    def session_count(self, include_archived=False):
        return int(self.shared["session"] is not None)

    def message_count(self):
        return len(self.shared["messages"])

    def end_session(self, session_id, end_reason):
        self.shared["session"].update(ended_at=1.0, end_reason=end_reason)

    def close(self):
        self.close_calls += 1
        self._conn.closed = True
        self._conn = None


class StateTests(unittest.TestCase):
    def setUp(self):
        class Client:
            def __init__(self):
                self.closed = False

            def is_closed(self):
                return self.closed
        class Compressor:
            context_length = 131072
        self.client_type, self.compressor_type = Client, Compressor
        self.modules = patch.dict(probe.sys.modules, {
            "openai": SimpleNamespace(OpenAI=Client),
            "agent.context_compressor": SimpleNamespace(ContextCompressor=Compressor),
            "sqlite3": SimpleNamespace(ProgrammingError=FixtureClosed)})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.state = Path("fixture-state").resolve()
        self.report = {name: False for name in probe.FLAGS}
        self.report.update(operation_failure_stage="", db_peak_bytes=0, db_cleanup_reason_type="")
        self.dbs = []
        self.shared = {"session": None, "messages": []}
        self.agent = None

    def db_factory(self, db_path, read_only=False):
        db = FixtureDB(db_path, read_only, self.shared)
        self.dbs.append(db)
        return db

    def factory(self, **kwargs):
        client = self.client_type()
        agent = SimpleNamespace(client=client, tools=[], valid_tool_names=set(),
            _memory_manager=None, _memory_store=None, _memory_enabled=False, _user_profile_enabled=False,
            _session_db=kwargs["session_db"], session_id=kwargs["session_id"],
            context_compressor=self.compressor_type(), compression_enabled=False,
            _environment_probe=False, _config_context_length=131072, _checkpoint_mgr=SimpleNamespace(enabled=False),
            session_api_calls=0, shutdown_memory_provider=Mock())
        def close():
            client.closed = True
            agent.client = None
            agent._session_db.end_session(agent.session_id, "agent_close")
        agent.close = Mock(side_effect=close)
        self.agent = agent
        return agent

    def run_exercise(self, factory=None, db_factory=None):
        with patch.object(probe, "save"), patch.object(probe, "storage_bytes", return_value=4096), patch.object(probe.os.path, "lexists", return_value=False):
            probe.exercise_state(factory or self.factory, db_factory or self.db_factory, "a" * 32, self.state, self.report)

    def test_non_windows_never_imports_hermes(self):
        with patch.object(probe.sys, "platform", "not-windows"), patch.object(probe.importlib, "import_module") as imported:
            self.assertEqual(probe.main(), 2)
            imported.assert_not_called()

    def test_complete_native_interface_sequence(self):
        factory = Mock(side_effect=self.factory)
        self.run_exercise(factory=factory)
        self.assertEqual(len(self.dbs), 2)
        self.assertFalse(self.dbs[0].read_only)
        self.assertTrue(self.dbs[1].read_only)
        self.assertIs(factory.call_args.kwargs["session_db"], self.dbs[0])
        self.assertEqual(factory.call_args.kwargs["enabled_toolsets"], [])
        self.assertTrue(factory.call_args.kwargs["skip_memory"])
        self.assertTrue(all(self.report[name] for name in probe.FLAGS if name != "db_class_verified"))
        self.assertTrue(all(x._conn is None and x.close_calls == 1 for x in self.dbs))
        self.agent.close.assert_called_once_with()
        self.assertEqual(self.shared["session"]["end_reason"], "agent_close")
        self.assertEqual(self.report["message_count"], 2)

    def test_constructor_failure_closes_db_not_fake_agent(self):
        with self.assertRaises(RuntimeError):
            self.run_exercise(factory=Mock(side_effect=RuntimeError("fixture")))
        self.assertIsNone(self.agent)
        self.assertEqual(self.dbs[0].close_calls, 1)
        self.assertEqual(self.report["operation_failure_stage"], "constructor_entry")

    def test_delete_journal_mode_stops_before_agent(self):
        def db_factory(**kwargs):
            db = self.db_factory(**kwargs)
            db._conn.mode = "delete"
            return db
        with self.assertRaises(ValueError):
            self.run_exercise(db_factory=db_factory)
        self.assertEqual(self.report["journal_mode"], "delete")
        self.assertIsNone(self.agent)
        self.assertIsNone(self.dbs[0]._conn)

    def test_preexisting_db_blocks_open(self):
        with patch.object(probe, "save"), patch.object(probe.os.path, "lexists", return_value=True), self.assertRaises(ValueError):
            probe.exercise_state(self.factory, self.db_factory, "a" * 32, self.state, self.report)
        self.assertFalse(self.dbs)

    def test_failed_append_still_closes_agent_and_writer(self):
        def db_factory(**kwargs):
            db = self.db_factory(**kwargs)
            db.append_message = Mock(side_effect=OSError("fixture"))
            return db
        with self.assertRaises(OSError):
            self.run_exercise(db_factory=db_factory)
        self.agent.close.assert_called_once_with()
        self.assertIsNone(self.dbs[0]._conn)
        self.assertEqual(self.report["operation_failure_stage"], "message_append_1")

    def test_suppressed_session_end_failure_is_detected(self):
        def db_factory(**kwargs):
            db = self.db_factory(**kwargs)
            db.end_session = Mock()
            return db
        with self.assertRaisesRegex(ValueError, "session_end_readback"):
            self.run_exercise(db_factory=db_factory)
        self.assertFalse(self.report["session_end_verified"])
        self.assertIsNone(self.dbs[0]._conn)

    def test_read_only_reopen_failure_does_not_reuse_writer(self):
        def db_factory(**kwargs):
            if kwargs.get("read_only"):
                raise OSError("fixture")
            return self.db_factory(**kwargs)
        with self.assertRaises(OSError):
            self.run_exercise(db_factory=db_factory)
        self.assertTrue(self.report["writer_closed"])
        self.assertFalse(self.report["read_only_reopened"])
        self.assertEqual(self.dbs[0].close_calls, 1)

    def test_corrupt_reopen_readback_still_closes_reader(self):
        def db_factory(**kwargs):
            db = self.db_factory(**kwargs)
            if kwargs.get("read_only"):
                db.shared["messages"][0]["content"] = "wrong"
            return db
        with self.assertRaisesRegex(ValueError, "reopen_readback"):
            self.run_exercise(db_factory=db_factory)
        self.assertTrue(all(x._conn is None for x in self.dbs))
        self.assertFalse(self.report["reopen_readback"])

    def test_closed_reference_without_closed_connection_rejected(self):
        db = FixtureDB(self.state / "state.db")
        db.close = lambda: setattr(db, "_conn", None)
        with self.assertRaisesRegex(ValueError, "db_connection_still_open"):
            probe.close_database(db)

    def test_wrong_db_path_and_readonly_binding_rejected(self):
        db = FixtureDB(self.state / "elsewhere.db")
        with self.assertRaises(ValueError):
            probe.inspect_db(db, self.state / "state.db", False)
        db = FixtureDB(self.state / "state.db", False)
        with self.assertRaises(ValueError):
            probe.inspect_db(db, db.db_path, True)

    def test_size_ceiling_is_strict_and_tracks_peak(self):
        with patch.object(probe, "storage_bytes", return_value=probe.STORAGE_LIMIT):
            probe.check_size(self.state, self.report)
        with patch.object(probe, "storage_bytes", return_value=probe.STORAGE_LIMIT + 1), self.assertRaises(ValueError):
            probe.check_size(self.state, self.report)
        with patch.object(probe, "storage_bytes", return_value=1), self.assertRaises(ValueError):
            probe.check_size(self.state, self.report)
        self.assertFalse(self.report["storage_within_limit"])

    def test_storage_counts_only_disclosed_files(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory).resolve()
            (state / "state.db").write_bytes(b"fixture")
            (state / "state.db-wal").write_bytes(b"wal")
            (state / "unrelated.txt").write_bytes(b"ignore")
            self.assertEqual(probe.storage_bytes(state), 10)
            (state / "state.db-shm").mkdir()
            with self.assertRaises(ValueError):
                probe.storage_bytes(state)

    def test_fixed_synthetic_records_and_no_model_execution(self):
        messages = probe.synthetic_messages("a" * 32)
        self.assertEqual(tuple(x[0] for x in messages), ("user", "assistant"))
        self.assertTrue(all(len(x[1].encode("ascii")) <= 512 for x in messages))
        text = (SOURCE / "hermes_state_check.py").read_text()
        for forbidden in (".run_conversation(", ".chat(", "subprocess", "__new__(", "sqlite3.connect(", "CREATE TABLE", "journal_mode=WAL"):
            self.assertNotIn(forbidden, text)
        self.assertIn("time.monotonic() + 22", text)
        self.assertIn("client.is_closed() is True", text)

    def test_oversized_report_never_writes(self):
        with patch("builtins.open") as opened, self.assertRaises(ValueError):
            probe.save({"x": "x" * probe.LIMIT})
        opened.assert_not_called()


if __name__ == "__main__":
    unittest.main()
