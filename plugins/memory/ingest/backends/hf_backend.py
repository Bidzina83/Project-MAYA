import os
import time
import random
import logging
from typing import List, Any
import importlib

# test overrides: prefer overrides module if present
try:
    _test_overrides = importlib.import_module("hermes.plugins.memory.ingest.tests.support.overrides")
except Exception:
    _test_overrides = None

# if overrides provide a requests shim, expose it into this module's globals
if _test_overrides and hasattr(_test_overrides, 'requests'):
    requests = getattr(_test_overrides, 'requests')

log = logging.getLogger(__name__)


def _backoff_sleep(attempt: int, backoff_factor: float = 0.5, max_sleep: float = 60.0):
    sleep = min(max_sleep, backoff_factor * (2 ** attempt))
    sleep = sleep * (0.5 + random.random() * 0.5)
    time.sleep(sleep)


class HFBackend:
    """Hugging Face embedding backend with retry/backoff for API calls.

    Modes (in order):
    - If HF_API_KEY set and requests available -> call HF Inference API (feature-extraction)
    - Else, try to use sentence-transformers locally (if installed)
    """

    def __init__(self, model: str | None = None, max_retries: int = 5, backoff_factor: float = 0.5):
        # default to a compact sentence-transformers model
        self.model = model or os.environ.get("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.api_key = os.environ.get("HF_API_KEY")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor

    def _resolve_requests_module(self):
        # Prefer a module-level 'requests' attribute if present (tests often monkeypatch
        # the hf_backend module's requests). Check local globals first, then try
        # importing canonical module names that tests may patch (hermes/maya_dev/plugins).
        req_mod = globals().get('requests')
        if req_mod:
            return req_mod
        for candidate in ("hermes.plugins.memory.ingest.backends.hf_backend", "maya_dev.plugins.memory.ingest.backends.hf_backend", "plugins.memory.ingest.backends.hf_backend"):
            try:
                m = importlib.import_module(candidate)
                req_mod = getattr(m, 'requests', None)
                if req_mod:
                    return req_mod
            except Exception:
                continue
        # fallback to importing requests normally
        try:
            return importlib.import_module('requests')
        except Exception:
            return None

    def _post_with_retries(self, url: str, headers: dict, json_payload: dict) -> Any:
        req_mod = self._resolve_requests_module()
        req_exceptions = getattr(req_mod, 'exceptions', None) if req_mod else None

        log.debug("_post_with_retries: using req_mod=%s (module=%s)", req_mod, getattr(req_mod, '__name__', None))

        if not req_mod:
            raise RuntimeError("requests package required for HF Inference API calls")
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                log.debug("_post_with_retries: attempt=%s url=%s", attempt + 1, url)
                r = req_mod.post(url, headers=headers, json=json_payload)
                log.debug("_post_with_retries: received status=%s headers=%s", getattr(r, 'status_code', None), getattr(r, 'headers', None))
                if r.status_code == 200:
                    return r
                # retry on common transient statuses
                if r.status_code in (429, 500, 502, 503, 504):
                    # honor Retry-After header when present
                    ra = r.headers.get("Retry-After")
                    if ra:
                        try:
                            delay = int(ra)
                            log.warning("HFBackend: received Retry-After=%s, sleeping %s seconds", ra, delay)
                            time.sleep(delay)
                        except Exception:
                            log.warning("HFBackend: invalid Retry-After header '%s', falling back to backoff", ra)
                            _backoff_sleep(attempt, self.backoff_factor)
                    else:
                        _backoff_sleep(attempt, self.backoff_factor)
                    last_exc = RuntimeError(f"status={r.status_code}")
                    log.warning("HFBackend: transient status %s on attempt %s/%s; retrying...", r.status_code, attempt + 1, self.max_retries)
                    continue
                # non-retryable
                r.raise_for_status()
                return r
            except Exception as e:
                last_exc = e
                # network error -> retry
                if req_exceptions and isinstance(e, req_exceptions.RequestException):
                    if attempt + 1 == self.max_retries:
                        raise
                    log.warning("HFBackend: network error on attempt %s/%s: %s; retrying...", attempt + 1, self.max_retries, e)
                    _backoff_sleep(attempt, self.backoff_factor)
                    continue
                # otherwise not retryable
                log.exception("HFBackend: non-retryable exception: %s", e)
                raise
        if last_exc:
            raise last_exc

    def _call_inference_api(self, texts: List[str]) -> List[List[float]]:
        req_mod = self._resolve_requests_module()
        if req_mod is None:
            raise RuntimeError("requests package required for HF Inference API calls")
        if not self.api_key:
            raise RuntimeError("HF_API_KEY not set for Hugging Face Inference API calls")
        url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        out = []
        for t in texts:
            log.debug("_call_inference_api: calling for text=%s", t)
            r = self._post_with_retries(url, headers, {"inputs": t})
            vec = r.json()
            # Some HF models return token-level vectors => average-pool
            if isinstance(vec, list) and vec and isinstance(vec[0], list):
                avg = [sum(col) / len(col) for col in zip(*vec)]
                out.append(avg)
            else:
                out.append(vec)
        return out

    def _call_sentence_transformers(self, texts: List[str]) -> List[List[float]]:
        try:
            from sentence_transformers import SentenceTransformer
        except Exception:
            raise RuntimeError("sentence-transformers not installed; cannot run local HF backend")
        model = SentenceTransformer(self.model)
        vecs = model.encode(texts, show_progress_bar=False)
        try:
            return vecs.tolist()
        except Exception:
            return [list(v) for v in vecs]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        log.debug("embed_batch: api_key=%s len(texts)=%s", bool(self.api_key), len(texts))
        if self.api_key:
            return self._call_inference_api(texts)
        # fallback to sentence-transformers local inference
        return self._call_sentence_transformers(texts)
