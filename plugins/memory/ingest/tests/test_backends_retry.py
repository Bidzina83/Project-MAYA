import types


def test_openai_retry(monkeypatch):
    # Build a fake openai module with error classes
    fake = types.SimpleNamespace()
    calls = {"n": 0}

    class RateLimitError(Exception):
        pass

    fake.error = types.SimpleNamespace(RateLimitError=RateLimitError, APIError=Exception, ServiceUnavailableError=Exception)

    def create(model, input):
        calls["n"] += 1
        if calls["n"] < 3:
            raise RateLimitError("rate limited")
        return {"data": [{"embedding": [0.1, 0.2]} for _ in input]}

    fake.Embedding = types.SimpleNamespace(create=create)

    # Patch the backend module's openai reference directly
    monkeypatch.setattr('hermes.plugins.memory.ingest.backends.openai_backend.openai', fake, raising=False)
    # also patch openai_error if the module references it
    monkeypatch.setattr('hermes.plugins.memory.ingest.backends.openai_backend.openai_error', fake.error, raising=False)

    import os
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    from hermes.plugins.memory.ingest.backends.openai_backend import OpenAIBackend

    b = OpenAIBackend(model="x", max_retries=5, backoff_factor=0.01)
    vecs = b.embed_batch(["a", "b"])
    assert len(vecs) == 2
    assert vecs[0] == [0.1, 0.2]


def test_hf_retry(monkeypatch):
    # Fake requests.post that returns 429 twice then 200
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
        if calls["n"] < 3:
            return FakeResp(429, headers={"Retry-After": "0"})
        return FakeResp(200, json_data=[0.1, 0.2])

    fake_requests = types.SimpleNamespace(post=post, exceptions=types.SimpleNamespace(RequestException=Exception))
    # Patch the hf_backend.requests reference directly
    monkeypatch.setattr('hermes.plugins.memory.ingest.backends.hf_backend.requests', fake_requests, raising=False)

    import os
    monkeypatch.setenv("HF_API_KEY", "x")
    from hermes.plugins.memory.ingest.backends.hf_backend import HFBackend

    b = HFBackend(model="x", max_retries=5, backoff_factor=0.01)
    vecs = b.embed_batch(["hello"])
    assert len(vecs) == 1
    assert vecs[0] == [0.1, 0.2]
