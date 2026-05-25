"""maya shim package for CI — expose embed_text symbol for tests
This is a temporary shim to unblock CI. Replace with proper packaging / implementation later.
"""
from typing import List


def embed_text(text: str) -> List[float]:
    """Return a deterministic small embedding for testing.
    Produces a fixed-length vector (8 floats) derived from input characters.
    """
    if text is None:
        text = ""
    # simple deterministic hash-like vector: ascii codes folded
    vec = [0.0] * 8
    for i, ch in enumerate(text):
        vec[i % 8] += (ord(ch) % 97) / 97.0
    # normalize to [0,1)
    return [float(round(x % 1.0, 6)) for x in vec]

# make available at package top-level
__all__ = ["embed_text"]
