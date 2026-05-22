import types


def test_openai_nonretryable_raises(monkeypatch):
    # fake openai that raises a non-retryable error (ValueError)
    fake = types.SimpleNamespace()

    def create(model, input):
        raise ValueError("bad request")

    fake.Embedding = types.SimpleNamespace(create=create)
    fake.error = types.SimpleNamespace()  # no retry classes

    # patch backend module directly
    monkeypatch.setattr('hermes.plugins.memory.ingest.backends.openai_backend.openai', fake, raising=False)
    monkeypatch.setattr('hermes.plugins.memory.ingest.backends.openai_backend.openai_error', fake.error, raising=False)

    from hermes.plugins.memory.ingest.backends.openai_backend import OpenAIBackend

    monkeypatch.setenv("OPENAI_API_KEY", "x")
    b = OpenAIBackend(model="x", max_retries=3, backoff_factor=0.01)

    try:
        import pytest
        with pytest.raises(ValueError):
            b.embed_batch(["a"])
    finally:
        pass


def test_hf_retry_retryafter_nonint(monkeypatch):
    # Simulate requests.post returning 429 with non-integer Retry-After, then 200
    class FakeResp:
        def __init__(self, status, json_data=None, headers=None):
            self.status_code = status
            self._json = json_data or [0.1, 0.2]
            self.headers = headers or {}

        def json(self):
            return self._json

        def raise_for_status(self):
            if self.status_code != 200:
                raise Exception(f"http {self.status_code}")

    calls = {"n": 0}

    def post(url, headers, json):
        calls["n"] += 1
        if calls["n"] == 1:
            return FakeResp(429, headers={"Retry-After": "invalid"})
        return FakeResp(200, json_data=[0.3, 0.4])

    fake_requests = types.SimpleNamespace(post=post, exceptions=types.SimpleNamespace(RequestException=Exception))
    monkeypatch.setattr('hermes.plugins.memory.ingest.backends.hf_backend.requests', fake_requests, raising=False)

    from hermes.plugins.memory.ingest.backends.hf_backend import HFBackend

    monkeypatch.setenv("HF_API_KEY", "x")
    b = HFBackend(model="x", max_retries=3, backoff_factor=0.01)
    vecs = b.embed_batch(["hello"])
    assert len(vecs) == 1
    assert vecs[0] == [0.3, 0.4]
