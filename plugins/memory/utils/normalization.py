from __future__ import annotations
import re
import unicodedata
from typing import List
import math

_ws_re = re.compile(r"\s+")
_control_re = re.compile(r"[\x00-\x1f\x7f]+")
import string
_punct_chars = string.punctuation


def text_normalize(s: str, remove_punctuation: bool = False) -> str:
    """Normalize text for retrieval normalization.

    - Apply Unicode NFKC normalization
    - Lowercase
    - Remove control characters
    - Collapse whitespace to single spaces and strip
    - Optionally remove punctuation (disabled by default)
    """
    if s is None:
        return ""
    if not isinstance(s, str):
        s = str(s)
    # Unicode normalization
    s = unicodedata.normalize("NFKC", s)
    # replace control chars with a single space so tokens stay separated
    s = _control_re.sub(" ", s)
    # optionally remove punctuation (basic ASCII punctuation)
    if remove_punctuation:
        # simple fallback: remove ASCII punctuation characters
        s = ''.join(ch for ch in s if ch not in _punct_chars)
    # collapse whitespace
    s = _ws_re.sub(" ", s).strip()
    s = s.lower()
    return s


def vector_normalize(v: List[float]) -> List[float]:
    """L2-normalize a vector. Returns empty list for empty input or zero-vector.
    """
    if not v:
        return []
    norm = 0.0
    out = []
    for x in v:
        try:
            fx = float(x)
        except Exception:
            fx = 0.0
        out.append(fx)
        norm += fx * fx
    if norm == 0.0:
        return [0.0 for _ in out]
    inv = 1.0 / math.sqrt(norm)
    return [x * inv for x in out]
