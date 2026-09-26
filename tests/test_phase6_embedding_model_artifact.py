import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import prepare_phase6_embedding_model as prepare_model


class TestPhase6EmbeddingModelArtifact(unittest.TestCase):
    def test_prepares_deterministic_pinned_archive_without_network(self):
        files = {
            "model.onnx": b"test-model",
            "tokenizer.json": b'{"version":"1.0"}',
        }
        pinned = {
            name: {
                "path": name,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for name, content in files.items()
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            prepare_model, "PINNED_FILES", pinned
        ):
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            for name, content in files.items():
                (source / name).write_bytes(content)
            work = root / "work"
            first = root / "first.zip"
            second = root / "second.zip"

            result = prepare_model.prepare_embedding_model_artifact(
                work_dir=work,
                archive_path=first,
                source_dir=source,
                download=False,
            )
            prepare_model.prepare_embedding_model_artifact(
                work_dir=work,
                archive_path=second,
                source_dir=source,
                download=False,
            )

            self.assertFalse(result["network_used"])
            self.assertEqual(first.read_bytes(), second.read_bytes())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(
                    set(archive.namelist()),
                    {"embedding-model-manifest.json", "model.onnx", "tokenizer.json"},
                )
                manifest = json.loads(
                    archive.read("embedding-model-manifest.json").decode("utf-8")
                )
            self.assertEqual(manifest["revision"], prepare_model.MODEL_REVISION)
            self.assertEqual(
                manifest["files"],
                {name: item["sha256"] for name, item in pinned.items()},
            )

    def test_rejects_unpinned_local_source(self):
        files = {
            "model.onnx": b"expected-model",
            "tokenizer.json": b"expected-tokenizer",
        }
        pinned = {
            name: {
                "path": name,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
            for name, content in files.items()
        }
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            prepare_model, "PINNED_FILES", pinned
        ):
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "model.onnx").write_bytes(b"tampered")
            (source / "tokenizer.json").write_bytes(files["tokenizer.json"])

            with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                prepare_model.prepare_embedding_model_artifact(
                    work_dir=root / "work",
                    archive_path=root / "model.zip",
                    source_dir=source,
                    download=False,
                )

    def test_failed_download_removes_temporary_file(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
            prepare_model.urllib.request,
            "urlopen",
            side_effect=OSError("offline"),
        ):
            root = Path(tmp)
            with self.assertRaisesRegex(OSError, "offline"):
                prepare_model._download_pinned_file(
                    "model.onnx",
                    {"path": "onnx/model.onnx", "sha256": "0" * 64},
                    root / "model.onnx",
                )
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
