import os
import tempfile
from ..chunker import chunk_file


def test_chunk_file_roundtrip():
    # build a sample text containing multiple paragraphs and enough length to create multiple chunks
    paras = [
        "This is paragraph one. It has a few sentences. Still part of the first paragraph.",
        "Second paragraph here. It contains additional text to increase size.",
        "Third paragraph is a bit longer. " + ("More text. " * 50),
        "Final short paragraph."
    ]
    text = "\n\n".join(paras)

    # write to a temporary file
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    chunks = chunk_file(path, max_chars=200)
    assert len(chunks) >= 2, "Expected at least two chunks for the sample text"

    # Verify that placing chunk.text at their start offsets reproduces the original
    buf = list('\0' * len(text))
    for c in chunks:
        start = c.start
        end = c.end
        buf[start:end] = list(c.text)
    reconstructed = ''.join(buf)
    assert reconstructed == text, "Reconstructed text must match original when placed by offsets"

    # Verify provenance metadata present
    for c in chunks:
        md = c.metadata
        assert "source_path" in md and md["source_path"].endswith(os.path.basename(path))
        assert "source_hash" in md and len(md["source_hash"]) == 64
        assert "extractor_version" in md
        assert "timestamp" in md

    # cleanup
    os.remove(path)
