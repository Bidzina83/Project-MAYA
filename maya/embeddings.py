from typing import List


def embed_text(text: str) -> List[float]:
    """Deterministic lightweight embedding used for CI/tests.
    Returns fixed-length 8-d vector derived from character codes.
    """
    if text is None:
        text = ""
    vec = [0.0] * 8
    for i, ch in enumerate(text):
        vec[i % 8] += (ord(ch) % 97) / 97.0
    return [float(round(x % 1.0, 6)) for x in vec]
