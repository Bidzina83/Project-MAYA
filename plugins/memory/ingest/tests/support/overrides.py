"""Test support overrides imported by backends when present.
Provides openai and requests shims to make CI/test runs deterministic when
monkeypatch ordering is unreliable.

This file is intentionally test-only and small. It should be safe to remove
or replace with a CI fixture once import-order issues are fixed.
"""
from types import SimpleNamespace

# OpenAI shim: simulate a first-call RateLimitError then success
_calls = {"openai_n": 0}

class RateLimitError(Exception):
    pass

class APIError(Exception):
    pass

class ServiceUnavailableError(Exception):
    pass

def _embedding_create(model, input):
    _calls["openai_n"] += 1
    if _calls["openai_n"] < 2:
        raise RateLimitError("rate limited (test shim)")
    return {"data": [{"embedding": [0.1, 0.2]} for _ in input]}

openai = SimpleNamespace(Embedding=SimpleNamespace(create=_embedding_create))
openai_error = SimpleNamespace(RateLimitError=RateLimitError, APIError=APIError, ServiceUnavailableError=ServiceUnavailableError)

# Requests shim: simulate first-call 429 with invalid Retry-After header, then 200
_req_state = {"n": 0}

class FakeResponse:
    def __init__(self, status_code, headers=None, json_data=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._json = json_data

    def json(self):
        return self._json

def _post(url, headers=None, json=None):
    _req_state["n"] += 1
    if _req_state["n"] == 1:
        return FakeResponse(429, headers={"Retry-After": "not-an-int"}, json_data=None)
    # success: return simple vector response used by HF backend tests
    return FakeResponse(200, headers={}, json_data=[[0.1, 0.2]])

requests = SimpleNamespace(post=_post, exceptions=SimpleNamespace(RequestException=Exception))
