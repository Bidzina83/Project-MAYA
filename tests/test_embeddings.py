def test_embed_returns_vector():
    from maya.embeddings import embed_text

    vec = embed_text("hello world")

    assert isinstance(vec, list)
    assert len(vec) > 0
    assert all(isinstance(x, float) for x in vec)
