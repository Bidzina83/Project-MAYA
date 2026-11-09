"""M08 setup ordering only; in-memory peers, no product/native entry point."""
import ast
import builtins
import hashlib
import json
from pathlib import Path

import pytest

from project_maya.bridge import model_worker
from project_maya.bridge.model_service import ModelDenied
import test_model_final_text_inert as fixture


@pytest.mark.parametrize("fail", [False, True])
def test_m08_helper_import_precedes_construction_ready_and_issue(monkeypatch, fail):
    trace = []
    original_import = builtins.__import__
    original_service = model_worker.OfflineModelBridge

    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "model_final_text" and globals and globals.get("__name__") == model_worker.__name__:
            trace.append("helpers")
            assert tuple(fromlist) == ("final_text_evidence", "final_guard_evidence")
            if fail:
                raise ImportError("inert fixed import failure")
        return original_import(name, globals, locals, fromlist, level)

    original_init, original_issue = original_service.__init__, original_service.issue
    def constructing(self, *args, **kwargs):
        trace.append("construct")
        original_init(self, *args, **kwargs)
    def issuing(self):
        trace.append("issue")
        return original_issue(self)

    monkeypatch.setattr(builtins, "__import__", importing)
    monkeypatch.setattr(original_service, "__init__", constructing)
    monkeypatch.setattr(original_service, "issue", issuing)
    retained = []
    if fail:
        with pytest.raises(ImportError):
            fixture.worker_fixture(retained=retained)
        raw, channel = retained
        assert channel.sent == [] and raw.getvalue() == b""
        assert trace == ["helpers"]
    else:
        effects, raw, channel = fixture.worker_fixture()
        assert trace == ["helpers", "construct", "issue"]
        assert channel.sent[0]["type"] == "model_worker_ready"
        assert len(effects) == 26 and fixture.verify(raw, channel) == 5


def test_non_m08_does_not_import_final_helpers(monkeypatch):
    original = builtins.__import__
    def importing(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "model_final_text" and globals and globals.get("__name__") == model_worker.__name__:
            raise AssertionError("M08 helper imported by another mode")
        return original(name, globals, locals, fromlist, level)
    monkeypatch.setattr(builtins, "__import__", importing)
    # This peer deliberately mutates final text; base mode must still reject it.
    with pytest.raises(ModelDenied):
        fixture.worker_fixture(mode=False)


def test_only_worker_ast_change_is_fixed_import_relocation():
    root = Path(__file__).resolve().parents[1]
    base = root / ".codex-build/maya-offline-model-final-20261104-2"
    name = "src/project_maya/bridge/model_worker.py"
    manifest = json.loads((base / "Maya-Offline-Model-Final-2/package-manifest.json").read_bytes())
    old = (base / "source-freeze" / name).read_bytes()
    assert hashlib.sha256(old).hexdigest() == next(i["sha256"] for i in manifest["source_files"] if i["path"] == name)
    before, after = ast.parse(old), ast.parse((root / name).read_bytes())
    class RemoveImport(ast.NodeTransformer):
        def visit_ImportFrom(self, node):
            if node.module == "model_final_text":
                assert [a.name for a in node.names] == ["final_text_evidence", "final_guard_evidence"]
                return None
            return node
        def visit_If(self, node):
            self.generic_visit(node)
            return node if node.body else None
    assert ast.dump(RemoveImport().visit(before)) == ast.dump(RemoveImport().visit(after))
    # Inspect the unmodified AST again, since the comparison removed imports.
    serve = next(n for n in ast.parse((root / name).read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name == "serve_model")
    imports = [(i, n) for i, n in enumerate(serve.body) if isinstance(n, ast.If)
               and any(isinstance(x, ast.ImportFrom) and x.module == "model_final_text" for x in n.body)]
    assert len(imports) == 1
    construct = next(i for i, n in enumerate(serve.body) if isinstance(n, ast.Assign)
                     and any(isinstance(t, ast.Name) and t.id == "service" for t in n.targets))
    assert imports[0][0] < construct
