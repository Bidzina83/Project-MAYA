import os
import pytest
from maya import embed_text


pytestmark = pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="No OPENAI_API_KEY")


def test_openai_embed_returns_vector():
    v = embed_text("testing openai integration")
    assert isinstance(v, list)
    assert len(v) > 0
    assert all(isinstance(x, float) for x in v)
