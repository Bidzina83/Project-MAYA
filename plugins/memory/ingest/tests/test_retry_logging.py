import types
import logging


def test_openai_retry_logs(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)
    fake = types.SimpleNamespace()
    calls = {"n": 0}

    class RateLimitError(Exception):
        pass

    fake.error = types.SimpleNamespace(RateLimitError=RateLimitError, APIError=Exception, ServiceUnavailableError=Exception)

    def create(model, input):
        calls["n"] += 1
        if calls["n"] < 2:
            raise RateLimitError("rate limited")
        return {"data": [{"embedding": [0.1, 0.2]} for _ in input]}

    fake.Embedding = types.SimpleNamespace(create=create)

    # Patch the backend module's openai reference directly
    monkeypatch.setattr('plugins.memory.ingest.backends.openai_backend.openai', fake, raising=False)
    monkeypatch.setattr('plugins.memory.ingest.backends.openai_backend.openai_error', fake.error, raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "x")

    from plugins.memory.ingest.backends.openai_backend import OpenAIBackend

    b = OpenAIBackend(model="x", max_retries=3, backoff_factor=0.01)
    with caplog.at_level(logging.WARNING):
        vecs = b.embed_batch(["a"])
    # Expect a warning about retry
    matched = [r for r in caplog.records if 'OpenAIBackend' in r.getMessage()]
    assert any('retrying' in r.getMessage().lower() for r in matched)
    assert len(vecs) == 1


def test_hf_retry_logs(monkeypatch, caplog):
    caplog.set_level(logging.WARNING)

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
        if calls["n"] < 2:
            return FakeResp(429, headers={"Retry-After": "0"})
        return FakeResp(200, json_data=[0.1, 0.2])

    fake_requests = types.SimpleNamespace(post=post, exceptions=types.SimpleNamespace(RequestException=Exception))
    # Patch hf_backend.requests directly
    monkeypatch.setattr('plugins.memory.ingest.backends.hf_backend.requests', fake_requests, raising=False)
    monkeypatch.setenv("HF_API_KEY", "x")

    from plugins.memory.ingest.backends.hf_backend import HFBackend

    b = HFBackend(model="x", max_retries=3, backoff_factor=0.01)
    with caplog.at_level(logging.WARNING):
        vecs = b.embed_batch(["hello"])
    matched = [r for r in caplog.records if 'HFBackend' in r.getMessage() or 'Retry-After' in r.getMessage()]
    assert any('retry' in r.getMessage().lower() for r in matched)
    assert len(vecs) == 1
