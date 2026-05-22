import os
import time
import random
import logging
from typing import List, Any

try:
    import requests
    from requests import exceptions as requests_exceptions
except Exception:
    requests = None
    requests_exceptions = None

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

    def _post_with_retries(self, url: str, headers: dict, json_payload: dict) -> Any:
        if not requests:
            raise RuntimeError("requests package required for HF Inference API calls")
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                r = requests.post(url, headers=headers, json=json_payload)
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
                if requests_exceptions and isinstance(e, requests_exceptions.RequestException):
                    if attempt + 1 == self.max_retries:
                        raise
                    log.warning("HFBackend: network error on attempt %s/%s: %s; retrying...", attempt + 1, self.max_retries, e)
                    _backoff_sleep(attempt, self.backoff_factor)
                    continue
                # otherwise not retryable
                raise
        if last_exc:
            raise last_exc

    def _call_inference_api(self, texts: List[str]) -> List[List[float]]:
        if not requests:
            raise RuntimeError("requests package required for HF Inference API calls")
        if not self.api_key:
            raise RuntimeError("HF_API_KEY not set for Hugging Face Inference API calls")
        url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model}"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        out = []
        for t in texts:
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
        if self.api_key and requests:
            return self._call_inference_api(texts)
        # fallback to sentence-transformers local inference
        return self._call_sentence_transformers(texts)
