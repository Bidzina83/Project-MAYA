#!/usr/bin/env python3
"""Prepare Maya's pinned offline embedding-model release artifact."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path


MODEL_ID = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
MODEL_REVISION = "f16484b452bc5449a3ad85665709a2648b51d735"
MODEL_LICENSE = "apache-2.0"
MODEL_SOURCE = f"https://huggingface.co/{MODEL_ID}"
MODEL_DIMENSION = 384
MODEL_MAX_LENGTH = 256
PINNED_FILES = {
    "model.onnx": {
        "path": "onnx/model.onnx",
        "sha256": "10f7a088420252b26caf819236ca2c9d2987afd0fc06fec7553b542a5655a05a",
    },
    "tokenizer.json": {
        "path": "tokenizer.json",
        "sha256": "2c3387be76557bd40970cec13153b3bbf80407865484b209e655e5e4729076b8",
    },
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare the pinned Maya ONNX embedding-model archive."
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--source-dir",
        type=Path,
        help="Directory containing already-downloaded model.onnx and tokenizer.json.",
    )
    source.add_argument(
        "--download",
        action="store_true",
        help="Explicitly download files from the immutable upstream revision.",
    )
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args(argv)

    result = prepare_embedding_model_artifact(
        work_dir=args.work_dir,
        archive_path=args.archive,
        source_dir=args.source_dir,
        download=args.download,
    )
    print(json.dumps(result, sort_keys=True))
    return 0


def prepare_embedding_model_artifact(
    *,
    work_dir: Path,
    archive_path: Path,
    source_dir: Path | None,
    download: bool,
) -> dict[str, object]:
    if (source_dir is None) == (not download):
        raise ValueError("select exactly one model source")
    work_dir = work_dir.resolve()
    archive_path = archive_path.resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    archive_path.parent.mkdir(parents=True, exist_ok=True)

    hashes: dict[str, str] = {}
    for name, metadata in PINNED_FILES.items():
        target = work_dir / name
        if source_dir is not None:
            source_path = source_dir.resolve() / name
            if not source_path.is_file():
                raise RuntimeError(f"embedding source file is missing: {name}")
            if source_path != target:
                shutil.copy2(source_path, target)
        elif not target.is_file() or _sha256(target) != metadata["sha256"]:
            _download_pinned_file(name, metadata, target)
        actual = _sha256(target)
        if actual != metadata["sha256"]:
            raise RuntimeError(f"embedding source checksum mismatch: {name}")
        hashes[name] = actual

    manifest = {
        "schema_version": 1,
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "license": MODEL_LICENSE,
        "source": MODEL_SOURCE,
        "dimension": MODEL_DIMENSION,
        "max_length": MODEL_MAX_LENGTH,
        "files": hashes,
    }
    manifest_path = work_dir / "embedding-model-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _write_deterministic_archive(
        archive_path,
        (manifest_path, work_dir / "model.onnx", work_dir / "tokenizer.json"),
    )
    return {
        "archive": str(archive_path),
        "archive_sha256": _sha256(archive_path),
        "model_id": MODEL_ID,
        "revision": MODEL_REVISION,
        "files": hashes,
        "network_used": download,
    }


def _download_pinned_file(name: str, metadata: dict[str, str], target: Path) -> None:
    url = f"{MODEL_SOURCE}/resolve/{MODEL_REVISION}/{metadata['path']}"
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            with urllib.request.urlopen(url, timeout=120) as response:
                shutil.copyfileobj(response, temporary, length=1024 * 1024)
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    if temporary_path is None:
        raise RuntimeError(f"could not create embedding download file: {name}")
    if _sha256(temporary_path) != metadata["sha256"]:
        temporary_path.unlink(missing_ok=True)
        raise RuntimeError(f"downloaded embedding checksum mismatch: {name}")
    os.replace(temporary_path, target)


def _write_deterministic_archive(archive_path: Path, files: tuple[Path, ...]) -> None:
    temporary = archive_path.with_suffix(archive_path.suffix + ".tmp")
    temporary.unlink(missing_ok=True)
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_STORED) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    os.replace(temporary, archive_path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
