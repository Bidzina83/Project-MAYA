"""Synthetic interface fixtures only; no Hermes, SDK or bundled code is loaded."""
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / "src/project_maya/windows_runtime"
spec = importlib.util.spec_from_file_location("maya_memory_probe", SOURCE / "hermes_memory_check.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.state = Path(self.temp.name).resolve()
        self.directory = self.state / "memories"
        self.stores = []
        outer = self

        class Store:
            def __init__(self, memory_char_limit=2200, user_char_limit=1375):
                self.memory_char_limit, self.user_char_limit = memory_char_limit, user_char_limit
                self.memory_entries, self.user_entries = [], []
                self.snapshot = {}
                outer.stores.append(self)

            def _path_for(self, target):
                return outer.directory / probe.TARGETS[target]

            def load_from_disk(self):
                outer.directory.mkdir(exist_ok=True)
                for target in probe.TARGETS:
                    path = self._path_for(target)
                    values = path.read_text().split("\n--\n") if path.exists() else []
                    setattr(self, target + "_entries", values)
                    self.snapshot[target] = self._render_block(target, values) if values else None

            def _render_block(self, target, values):
                return target + ":" + "|".join(values)

            def format_for_system_prompt(self, target):
                return self.snapshot.get(target)

            def persist(self, target):
                path = self._path_for(target)
                path.write_text("\n--\n".join(probe.entries(self, target)), encoding="utf-8")
                path.with_name(path.name + ".lock").touch()
                return dict(success=True, done=True, target=target, entry_count=len(probe.entries(self, target)))

            def add(self, target, content):
                probe.entries(self, target).append(content)
                return self.persist(target)

            def replace(self, target, old_text, new_content):
                values = probe.entries(self, target)
                values[values.index(old_text)] = new_content
                return self.persist(target)

            def remove(self, target, old_text):
                probe.entries(self, target).remove(old_text)
                return self.persist(target)

        class Client:
            closed = False
            def is_closed(self):
                return self.closed

        class Compressor:
            context_length = 131072

        self.store_type, self.client_type, self.compressor_type = Store, Client, Compressor
        self.locking = SimpleNamespace(locking=Mock(), LK_NBLCK=2, LK_UNLCK=0)
        self.module = SimpleNamespace(MemoryStore=Store, ENTRY_DELIMITER="\n--\n", fcntl=None,
                                      msvcrt=self.locking, get_memory_dir=lambda: self.directory)
        self.modules = patch.dict(probe.sys.modules, {"openai": SimpleNamespace(OpenAI=Client),
            "agent.context_compressor": SimpleNamespace(ContextCompressor=Compressor)})
        self.modules.start()
        self.addCleanup(self.modules.stop)
        self.report = {name: False for name in probe.FLAGS}
        self.report.update(operation_failure_stage="", operation_checks={}, mutations_verified=0, memory_peak_bytes=0)
        self.agent = None

    def factory(self, **kwargs):
        store = self.store_type()
        store.load_from_disk()
        client = self.client_type()
        agent = SimpleNamespace(client=client, tools=[], valid_tool_names=set(), _memory_store=store,
            _memory_enabled=True, _user_profile_enabled=True, _memory_manager=None, _session_db=kwargs["session_db"],
            context_compressor=self.compressor_type(), compression_enabled=False, _environment_probe=False,
            _config_context_length=131072, _checkpoint_mgr=SimpleNamespace(enabled=False), session_api_calls=0,
            shutdown_memory_provider=Mock())
        def close():
            client.closed = True
            agent.client = None
        agent.close = Mock(side_effect=close)
        self.agent = agent
        return agent

    def exercise(self, factory=None):
        with patch.object(probe, "save"):
            probe.exercise_memory(factory or self.factory, self.module, self.locking, "a" * 32, self.state, self.report)

    def test_success_eight_mutations_reload_and_locks(self):
        factory = Mock(side_effect=self.factory)
        self.exercise(factory)
        self.assertFalse(factory.call_args.kwargs["skip_memory"])
        self.assertIsNone(factory.call_args.kwargs["session_db"])
        self.assertEqual(self.report["mutations_verified"], 8)
        self.assertEqual(set(self.report["operation_checks"]), set(probe.OPERATIONS))
        self.assertTrue(all(self.report["operation_checks"].values()))
        self.assertEqual(self.report["lock_probe_count"], 2)
        self.assertEqual(self.locking.locking.call_count, 4)
        self.assertEqual(len(self.stores), 2)
        self.assertTrue(all(self.report[key] for key in probe.FLAGS if key not in ("fresh_home_verified", "memory_class_verified")))
        self.agent.close.assert_called_once_with()
        self.agent.shutdown_memory_provider.assert_called_once_with([])
        for target, name in probe.TARGETS.items():
            self.assertEqual((self.directory / name).read_text(), probe.fixture(target, "a" * 32)[2])

    def test_constructor_failure_no_fake_cleanup(self):
        with self.assertRaises(RuntimeError):
            self.exercise(Mock(side_effect=RuntimeError("fixture")))
        self.assertIsNone(self.agent)
        self.assertEqual(self.report["operation_failure_stage"], "constructor_entry")

    def test_preexisting_files_rejected(self):
        self.directory.mkdir()
        (self.directory / "MEMORY.md").touch()
        with self.assertRaisesRegex(ValueError, "already_populated"):
            self.exercise()
        self.assertIsNone(self.agent)

    def test_empty_bootstrap_directory_allowed(self):
        self.directory.mkdir()
        self.exercise()
        self.assertTrue(self.report["initial_empty"])

    def test_missing_store_or_enabled_flags_close_agent(self):
        for key, value in (("_memory_store", None), ("_memory_enabled", False), ("_memory_manager", object())):
            with self.subTest(key=key):
                def factory(**kwargs):
                    agent = self.factory(**kwargs)
                    setattr(agent, key, value)
                    return agent
                with self.assertRaisesRegex(ValueError, "constructor_postconditions"):
                    self.exercise(factory)
                self.agent.close.assert_called_once()

    def test_missing_windows_locking_rejected(self):
        self.module.msvcrt = None
        with self.assertRaisesRegex(ValueError, "locking_missing"):
            self.exercise()
        self.agent.close.assert_called_once()

    def test_false_mutation_result_rejected(self):
        with patch.object(self.store_type, "add", return_value={"success": False}):
            with self.assertRaisesRegex(ValueError, "mutation_result"):
                self.exercise()
        self.agent.close.assert_called_once()

    def test_empty_file_cannot_substitute_for_readback(self):
        original = self.store_type.persist
        def persist(store, target):
            result = original(store, target)
            store._path_for(target).write_text("")
            return result
        with patch.object(self.store_type, "persist", persist):
            with self.assertRaisesRegex(ValueError, "readback"):
                self.exercise()
        self.assertEqual(self.report["mutations_verified"], 0)

    def test_lock_failure_stops_and_closes(self):
        self.locking.locking.side_effect = OSError("fixture")
        with self.assertRaises(OSError):
            self.exercise()
        self.agent.close.assert_called_once()
        self.assertEqual(self.report["operation_failure_stage"], "memory_lock_probes")

    def test_snapshot_mismatch_blocks(self):
        original = self.store_type.format_for_system_prompt
        def snapshot(store, target):
            return "wrong" if len(self.stores) == 2 else original(store, target)
        with patch.object(self.store_type, "format_for_system_prompt", snapshot):
            with self.assertRaisesRegex(ValueError, "reload_postconditions"):
                self.exercise()

    def test_changed_hashes_block(self):
        with patch.object(probe, "file_hashes", side_effect=[{"a": "1"}, {"a": "2"}]):
            with self.assertRaisesRegex(ValueError, "reload_postconditions"):
                self.exercise()

    def test_inventory_rejects_residue_and_oversize(self):
        self.directory.mkdir()
        path = self.directory / ".mem_fixture.tmp"
        path.touch()
        with self.assertRaisesRegex(ValueError, "unexpected_file"):
            probe.inventory(self.directory, self.report)
        path.unlink()
        (self.directory / "MEMORY.md").write_bytes(b"a" * (probe.STORAGE_LIMIT + 1))
        with self.assertRaisesRegex(ValueError, "size_limit"):
            probe.inventory(self.directory, self.report)

    def test_non_windows_guard_never_imports_hermes(self):
        with patch.object(probe.sys, "platform", "not-windows"), patch.object(probe.importlib, "import_module") as imported:
            self.assertEqual(probe.main(), 2)
            imported.assert_not_called()

    def test_strict_config_and_fixture(self):
        self.assertTrue(probe.config_matches(probe.CONFIG, probe.CONFIG))
        self.assertFalse(probe.config_matches(True, 1))
        self.assertTrue(all(len(x.encode("ascii")) <= 256 for x in probe.fixture("memory", "a" * 32)))


if __name__ == "__main__":
    unittest.main()
