"""Safely migrate legacy ``memory_kv`` records into Project MAYA storage."""

from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
import json
import math
import os
import shutil
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


TARGET_SCHEMAS = {"registry", "memory_entries"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_registry_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS embeddings (
            chunk_id TEXT PRIMARY KEY,
            embedding_path TEXT,
            source_path TEXT,
            source_hash TEXT,
            model TEXT,
            extractor_version TEXT,
            embedding_timestamp TEXT,
            updated_at TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER PRIMARY KEY,
            embedding_id TEXT UNIQUE,
            chunk_id TEXT,
            vector TEXT,
            vector_dim INTEGER,
            created_at TEXT,
            source_path TEXT,
            score_meta TEXT,
            normalized_vector TEXT,
            normalized_vector_dim INTEGER,
            normalized_vector_algo TEXT,
            normalized_at TEXT,
            normalized_version INTEGER
        )
        """
    )


def _ensure_memory_entries_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS memory_entries (
            key TEXT PRIMARY KEY,
            value TEXT,
            migrated_from TEXT
        )
        """
    )


def _decode_legacy(value: Any) -> tuple[Any, str]:
    if isinstance(value, bytes):
        raw = value
        decoded: Any = value.decode("utf-8", errors="replace")
    elif value is None:
        raw = b""
        decoded = None
    else:
        decoded = value
        raw = str(value).encode("utf-8")
    return decoded, hashlib.sha256(raw).hexdigest()


def _numeric_vector(value: Any) -> Optional[list[int | float]]:
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(parsed, list):
        return None
    if not all(
        type(item) in (int, float)
        and (not isinstance(item, float) or math.isfinite(item))
        for item in parsed
    ):
        return None
    return parsed


def _insert_registry_row(
    conn: sqlite3.Connection,
    key: str,
    value: Any,
    migrated_from: str,
    *,
    overwrite: bool,
) -> tuple[bool, dict[str, Any]]:
    existing = conn.execute(
        "SELECT 1 FROM entries WHERE embedding_id = ?", (str(key),)
    ).fetchone()
    if existing and not overwrite:
        return False, {"key": str(key), "status": "skipped_conflict"}

    decoded, original_hash = _decode_legacy(value)
    vector = _numeric_vector(decoded)
    created_at = _utc_now()
    provenance: dict[str, Any] = {
        "migrated_from": migrated_from,
        "original_sha256": original_hash,
            "migration": "project_maya.migration:v1",
    }
    chunk_id: str | None = None
    vector_json: str | None = None
    vector_dim: int | None = None

    if vector is not None:
        chunk_id = str(key)
        vector_json = json.dumps(vector, separators=(",", ":"))
        vector_dim = len(vector)
    else:
        try:
            provenance["legacy_value"] = json.loads(decoded)
        except (TypeError, ValueError, json.JSONDecodeError):
            provenance["legacy_value"] = decoded

    statement = "INSERT OR REPLACE" if overwrite else "INSERT"
    conn.execute(
        f"""
        {statement} INTO entries(
            embedding_id, chunk_id, vector, vector_dim,
            created_at, source_path, score_meta
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            str(key),
            chunk_id,
            vector_json,
            vector_dim,
            created_at,
            "legacy_kv",
            json.dumps(provenance, ensure_ascii=False),
        ),
    )

    if vector is not None:
        embedding_statement = "INSERT OR REPLACE" if overwrite else "INSERT OR IGNORE"
        conn.execute(
            f"""
            {embedding_statement} INTO embeddings(
                chunk_id, source_path, source_hash, extractor_version,
                embedding_timestamp, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                str(key),
                "legacy_kv",
                original_hash,
                "legacy-migration",
                created_at,
                created_at,
            ),
        )

    return True, {
        "key": str(key),
        "status": "overwritten" if existing else "migrated",
        "vector_dim": vector_dim,
    }


def _insert_memory_entry(
    conn: sqlite3.Connection,
    key: str,
    value: Any,
    migrated_from: str,
    *,
    overwrite: bool,
) -> tuple[bool, dict[str, Any]]:
    existing = conn.execute(
        "SELECT 1 FROM memory_entries WHERE key = ?", (str(key),)
    ).fetchone()
    if existing and not overwrite:
        return False, {"key": str(key), "status": "skipped_conflict"}
    statement = "INSERT OR REPLACE" if overwrite else "INSERT"
    conn.execute(
        f"{statement} INTO memory_entries(key, value, migrated_from) VALUES (?, ?, ?)",
        (str(key), value, migrated_from),
    )
    return True, {
        "key": str(key),
        "status": "overwritten" if existing else "migrated",
    }


def _validate_registry(
    conn: sqlite3.Connection,
    migrated_keys: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    samples: list[dict[str, Any]] = []
    errors: list[str] = []
    for key in migrated_keys[:5]:
        row = conn.execute(
            "SELECT vector, vector_dim, score_meta FROM entries WHERE embedding_id = ?",
            (key,),
        ).fetchone()
        if row is None:
            errors.append(f"missing migrated entry: {key}")
            continue
        vector_json, vector_dim, score_meta_json = row
        try:
            score_meta = json.loads(score_meta_json)
        except (TypeError, ValueError, json.JSONDecodeError):
            errors.append(f"invalid score_meta JSON: {key}")
            continue
        if "migrated_from" not in score_meta or "original_sha256" not in score_meta:
            errors.append(f"missing provenance: {key}")
        if vector_json is not None:
            try:
                vector = json.loads(vector_json)
            except (TypeError, ValueError, json.JSONDecodeError):
                errors.append(f"invalid vector JSON: {key}")
            else:
                if not isinstance(vector, list) or vector_dim != len(vector):
                    errors.append(f"vector_dim mismatch: {key}")
        samples.append({"key": key, "vector_dim": vector_dim})
    return samples, errors


def _backup_database(source: Path, backup: Path) -> None:
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, backup)
    if source.stat().st_size != backup.stat().st_size:
        raise RuntimeError("database backup size verification failed")
    with closing(sqlite3.connect(backup)) as conn:
        result = conn.execute("PRAGMA quick_check").fetchone()
    if not result or result[0] != "ok":
        raise RuntimeError("database backup integrity verification failed")


def _write_report(path: Path, report: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def migrate(
    from_src: str,
    to_dest: str,
    dry_run: bool = True,
    target_schema: str = "registry",
    *,
    allow_modify: bool = False,
    overwrite: bool = False,
    backup_path: str | None = None,
    report_path: str | None = None,
) -> dict[str, Any]:
    """Migrate legacy rows, defaulting to a non-mutating dry run."""
    started = time.monotonic()
    if target_schema not in TARGET_SCHEMAS:
        raise ValueError(f"unsupported target_schema: {target_schema}")
    if not dry_run and not allow_modify:
        raise PermissionError("apply requires allow_modify=True")

    source_path = Path(from_src).resolve()
    destination_path = Path(to_dest).resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"legacy source DB not found: {source_path}")

    with closing(sqlite3.connect(source_path)) as source:
        table = source.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='memory_kv'"
        ).fetchone()
        if not table:
            raise RuntimeError("legacy table 'memory_kv' not found in source DB")
        rows = source.execute("SELECT key, value FROM memory_kv").fetchall()

    summary: dict[str, Any] = {
        "source_rows": len(rows),
        "migrated": 0,
        "skipped_keys": [],
        "samples": [],
        "validation_errors": [],
        "to_path": str(destination_path),
        "target_schema": target_schema,
        "dry_run": dry_run,
        "overwrite": overwrite,
    }
    if dry_run:
        summary["duration_seconds"] = round(time.monotonic() - started, 6)
        return summary

    destination_existed = destination_path.exists()
    if destination_existed:
        if not backup_path:
            raise PermissionError("an existing destination requires backup_path")
        _backup_database(destination_path, Path(backup_path).resolve())

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    migrated_keys: list[str] = []
    with closing(sqlite3.connect(destination_path)) as destination:
        if target_schema == "registry":
            _ensure_registry_schema(destination)
        else:
            _ensure_memory_entries_schema(destination)

        try:
            destination.execute("BEGIN")
            for key, value in rows:
                if target_schema == "registry":
                    inserted, sample = _insert_registry_row(
                        destination,
                        str(key),
                        value,
                        str(source_path),
                        overwrite=overwrite,
                    )
                else:
                    inserted, sample = _insert_memory_entry(
                        destination,
                        str(key),
                        value,
                        str(source_path),
                        overwrite=overwrite,
                    )
                if inserted:
                    migrated_keys.append(str(key))
                    summary["migrated"] += 1
                    if len(summary["samples"]) < 5:
                        summary["samples"].append(sample)
                else:
                    summary["skipped_keys"].append(str(key))

            if target_schema == "registry":
                validation_samples, errors = _validate_registry(
                    destination, migrated_keys
                )
                summary["samples"] = validation_samples
                summary["validation_errors"] = errors
                if errors:
                    raise RuntimeError("migration validation failed")
            destination.commit()
        except Exception:
            destination.rollback()
            raise

    summary["duration_seconds"] = round(time.monotonic() - started, 6)
    final_report_path = Path(
        report_path or f"{destination_path}.migration.report.json"
    ).resolve()
    summary["report_path"] = str(final_report_path)
    if destination_existed and backup_path:
        summary["backup_path"] = str(Path(backup_path).resolve())
    _write_report(final_report_path, summary)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from", dest="from_src", required=True)
    parser.add_argument("--to", dest="to_dest", required=True)
    parser.add_argument(
        "--target-schema", choices=sorted(TARGET_SCHEMAS), default="registry"
    )
    migration_mode = parser.add_mutually_exclusive_group()
    migration_mode.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate migration without writing. This is the default.",
    )
    migration_mode.add_argument(
        "--apply", action="store_true", help="Apply migration; default is dry-run"
    )
    parser.add_argument(
        "--allow-modify",
        action="store_true",
        help="Required with --apply to acknowledge destination writes",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--backup", dest="backup_path")
    parser.add_argument("--report", dest="report_path")
    args = parser.parse_args()
    result = migrate(
        args.from_src,
        args.to_dest,
        dry_run=args.dry_run or not args.apply,
        target_schema=args.target_schema,
        allow_modify=args.allow_modify,
        overwrite=args.overwrite,
        backup_path=args.backup_path,
        report_path=args.report_path,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
