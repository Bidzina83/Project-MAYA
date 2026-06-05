import os
import tempfile
from hermes.plugins.memory.ingest.chunker import chunk_file, chunk_text


def reconstruct_from_chunks(text, chunks):
    buf = list('\0' * len(text))
    for c in chunks:
        start = c.start
        end = c.end
        buf[start:end] = list(c.text)
    return ''.join(buf)


def test_unicode_and_combining_chars():
    # include emojis, CJK, and combining characters
    paras = [
        "Hello 👋 world!",
        "汉字测试 — 中文字符和标点。",
        "Combining: a\u0301 e\u0301 o\u0301 (á é ó).",
    ]
    text = "\n\n".join(paras)
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    chunks = chunk_file(path, max_chars=50)
    assert len(chunks) >= 2
    rec = reconstruct_from_chunks(text, chunks)
    assert rec == text
    os.remove(path)


def test_long_single_paragraph_splits_by_sentence():
    # single paragraph with many sentences; should split into sentence-like chunks
    sentences = [f"Sentence {i}." for i in range(200)]
    paragraph = " ".join(sentences)
    text = paragraph
    spans = chunk_text(text, max_chars=200)
    # ensure spans cover text and don't overlap/gap
    assert spans
    covered = ''.join([text[s:e] for s, e in spans])
    assert covered == text


def test_long_url_and_hyphenation_like_pdf_noise():
    # long URL to stress chunk boundaries
    long_url = "https://example.com/" + ("path/" * 100) + "resource"
    pdf_noise = "This is a hyphenated word at line break: hyphen-\nation should be joined.\nAnother line."
    paras = [long_url, pdf_noise, "Normal paragraph after noise."]
    text = "\n\n".join(paras)
    fd, path = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

    chunks = chunk_file(path, max_chars=300)
    # reconstruct
    rec = reconstruct_from_chunks(text, chunks)
    assert rec == text
    # ensure hyphenation fragment exists in chunk text (chunker shouldn't mangle content)
    assert "hyphen-\nation" in text
    os.remove(path)
