from plugins.memory.utils.normalization import text_normalize, vector_normalize


def test_text_normalize_basic():
    s = "  Héllo\tWORLD!  "
    out = text_normalize(s)
    assert "héllo world!" in out
    assert "  " not in out


def test_vector_normalize_unit_length():
    v = [3.0, 4.0]
    n = vector_normalize(v)
    # length should be 1.0 (within tolerance)
    import math

    norm = math.sqrt(sum(x * x for x in n))
    assert abs(norm - 1.0) < 1e-6


def test_vector_normalize_empty():
    assert vector_normalize([]) == []
