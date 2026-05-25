"""
Simple deterministic chunker for persistent semantic memory ingestion (T1.0).
Produces character-anchored chunks with provenance metadata.

Public functions:
- chunk_text(text, max_chars=1000) -> list of (start, end)
- chunk_file(path, max_chars=1000, extractor_version='v0.1') -> list[Chunk]

Chunk dataclass fields:
- id: uuid4 str
- text: str
- start: int (char offset)
- end: int (char offset, exclusive)
- metadata: dict with source_path, source_hash, extractor_version, timestamp

This is intentionally small and well-tested. It is not a production-grade tokenizer/segmenter,
but it provides deterministic behavior suitable for Phase 1 unit tests and dry-run ingestion.
"""
from __future__ import annotations

import hashlib
import os
import re
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Tuple


@dataclass
class Chunk:
    id: str
    text: str
    start: int
    end: int
    metadata: dict


def _paragraph_boundaries(text: str) -> List[Tuple[int, int]]:
    """Return list of (start, end) spans for paragraphs (split on two or more newlines).

    NOTE: paragraph spans include the trailing paragraph separator (the two-or-more newlines)
    to make the spans contiguous when concatenated.
    """
    if not text:
        return []
    spans: List[Tuple[int, int]] = []
    prev = 0
    for m in re.finditer(r"\n{2,}", text):
        # include the separator in the span so concatenating spans reproduces original
        end = m.end()
        spans.append((prev, end))
        prev = m.end()
    spans.append((prev, len(text)))
    return spans


def chunk_text(text: str, max_chars: int = 1000) -> List[Tuple[int, int]]:
    """Deterministically chunk text into (start, end) spans not exceeding max_chars.

    Strategy:
    - Split into paragraph spans (so we don't break paragraphs when avoidable).
    - Accumulate consecutive paragraphs until adding the next would exceed max_chars.
    - If a single paragraph exceeds max_chars, split that paragraph by sentence boundaries
      (naive split on sentence endings) into smaller pieces.

    Returns list of (start, end) character offsets referencing the original text.
    """
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")

    spans: List[Tuple[int, int]] = []
    para_spans = _paragraph_boundaries(text)

    cur_start = None
    cur_len = 0

    for pstart, pend in para_spans:
        plen = pend - pstart
        if cur_start is None:
            # start a new chunk
            cur_start = pstart
            cur_len = plen
        elif cur_len + plen <= max_chars:
            # append paragraph to current chunk
            cur_len += plen
        else:
            # flush current chunk up to start of this paragraph
            spans.append((cur_start, pstart))
            # start new chunk with this paragraph
            cur_start = pstart
            cur_len = plen

        # If a single paragraph is longer than max_chars, split it by sentence-like breaks
        if plen > max_chars:
            # If we have an earlier chunk that doesn't include this paragraph, leave it
            if cur_start is not None and cur_start < pstart:
                # flush the chunk that includes content before this paragraph
                spans.append((cur_start, pstart))
            # split paragraph content robustly using sentence-like matches with real spans
            paragraph = text[pstart:pend]
            sentence_spans = []
            # regex to match sentences including trailing whitespace
            for m in re.finditer(r".+?(?:[.!?]+(?:\s+|$))", paragraph, flags=re.S):
                s_rel_start, s_rel_end = m.start(), m.end()
                sentence_spans.append((pstart + s_rel_start, pstart + s_rel_end))
            # if no sentence matches, fall back to fixed-size sliding windows
            if not sentence_spans:
                # emit fixed size spans across the paragraph
                offs = pstart
                while offs < pend:
                    e = min(pend, offs + max_chars)
                    spans.append((offs, e))
                    offs = e
            else:
                # combine sentences into chunks not exceeding max_chars
                buf_start = None
                buf_len = 0
                for s_abs_start, s_abs_end in sentence_spans:
                    s_len = s_abs_end - s_abs_start
                    if buf_start is None:
                        buf_start = s_abs_start
                        buf_len = s_len
                    elif buf_len + s_len <= max_chars:
                        buf_len += s_len
                    else:
                        spans.append((buf_start, buf_start + buf_len))
                        buf_start = s_abs_start
                        buf_len = s_len
                if buf_start is not None:
                    spans.append((buf_start, min(pend, buf_start + buf_len)))
            # reset current chunk state
            cur_start = None
            cur_len = 0

    if cur_start is not None:
        last_end = para_spans[-1][1]
        spans.append((cur_start, last_end))

    # Do not merge spans here; chunk boundaries must respect max_chars and sentence splits.
    return spans


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_file(path: str, max_chars: int = 1000, extractor_version: str = "v0.1") -> List[Chunk]:
    """Read file at path and produce Chunk objects with provenance metadata.

    Metadata keys:
    - source_path: absolute path
    - source_hash: sha256 of file bytes
    - extractor_version: provided string
    - timestamp: UTC ISO8601 string
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    source_hash = _sha256_text(text)
    timestamp = datetime.now(timezone.utc).isoformat()
    para_spans = chunk_text(text, max_chars=max_chars)

    chunks: List[Chunk] = []
    for start, end in para_spans:
        chunk_text_slice = text[start:end]
        c = Chunk(
            id=str(uuid.uuid4()),
            text=chunk_text_slice,
            start=start,
            end=end,
            metadata={
                "source_path": os.path.abspath(path),
                "source_hash": source_hash,
                "extractor_version": extractor_version,
                "timestamp": timestamp,
            },
        )
        chunks.append(c)
    return chunks


if __name__ == "__main__":
    import argparse
    import json

    p = argparse.ArgumentParser(description="Chunk a file and print JSON metadata")
    p.add_argument("path", help="file to chunk")
    p.add_argument("--max-chars", type=int, default=1000)
    p.add_argument("--extractor-version", default="v0.1")
    args = p.parse_args()

    chs = chunk_file(args.path, max_chars=args.max_chars, extractor_version=args.extractor_version)
    out = [asdict(c) for c in chs]
    print(json.dumps(out, indent=2))
