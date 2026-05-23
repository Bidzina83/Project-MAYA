import os
import time
import random
import logging
from typing import Callable, Any, List

# Try importing openai robustly; if a transient import error occurs when this
# module is loaded via importlib, attempt to import via importlib.import_module
# so we can still use the installed package when available.
try:
    import openai
    from openai import error as openai_error
except Exception:
    try:
        import importlib
        openai = importlib.import_module('openai')
        openai_error = getattr(openai, 'error', None)
    except Exception:
        openai = None
        openai_error = None

log = logging.getLogger(__name__)


def _backoff_sleep(attempt: int, backoff_factor: float = 0.5, max_sleep: float = 60.0):
    # Exponential backoff with jitter
    sleep = min(max_sleep, backoff_factor * (2 ** attempt))
    # add jitter
    sleep = sleep * (0.5 + random.random() * 0.5)
    time.sleep(sleep)


class OpenAIBackend:
    """OpenAI embeddings backend wrapper with retry/backoff logic.

    Expects OPENAI_API_KEY in env for real calls. If openai package is not
    installed or API key missing, calls will raise with a helpful message.

    Retry behaviour (configurable via constructor):
      - max_retries: number of total attempts (default 5)
      - backoff_factor: base backoff factor in seconds (default 0.5)
    """

    def __init__(self, model: str | None = None, max_retries: int = 5, backoff_factor: float = 0.5):
        self.model = model or os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        if openai and self.api_key:
            try:
                # openai library v2 uses client-based usage; keep a best-effort
                # compatibility: set api_key on module if attribute exists.
                setattr(openai, 'api_key', self.api_key)
            except Exception:
                pass

    def _call_with_retries(self, fn: Callable[[], Any]) -> Any:
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                return fn()
            except Exception as e:
                last_exc = e
                # Decide whether this is retryable
                retryable = False
                # openai-specific error types
                if openai_error:
                    try:
                        if isinstance(e, getattr(openai_error, 'RateLimitError', ())) or isinstance(e, getattr(openai_error, 'ServiceUnavailableError', ())) or isinstance(e, getattr(openai_error, 'APIError', ())):
                            retryable = True
                    except Exception:
                        pass
                # Network/HTTP-like errors may have status_code attribute
                status = getattr(e, 'http_status', None) or getattr(e, 'status_code', None)
                if status and int(status) in (429, 500, 502, 503, 504):
                    retryable = True
                if not retryable or attempt + 1 == self.max_retries:
                    # no more retries
                    log.debug("Not retrying (attempt=%s): %s", attempt, e)
                    raise
                # Log retry
                log.warning("OpenAIBackend: transient error on attempt %s/%s: %s; retrying...", attempt + 1, self.max_retries, e)
                # otherwise backoff and retry
                _backoff_sleep(attempt, self.backoff_factor)
        # if we exit the loop, re-raise last exception
        if last_exc:
            raise last_exc

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        if not openai:
            raise RuntimeError("openai package is not installed in the environment")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment")

        def do_request():
            # Support both openai.Embedding.create (v1 style) and client-based
            # patterns used by newer wrappers. Try the common v1 call first.
            try:
                return openai.Embedding.create(model=self.model, input=texts)
            except Exception:
                # Fallback: if openai provides a Client class or client module,
                # attempt a client-based call.
                client = getattr(openai, 'OpenAI', None) or getattr(openai, 'Client', None)
                if client:
                    c = client(api_key=self.api_key) if callable(client) else client
                    # prefer .embeddings.create if available
                    if hasattr(c, 'embeddings') and hasattr(c.embeddings, 'create'):
                        return c.embeddings.create(model=self.model, input=texts)
                raise

        resp = self._call_with_retries(do_request)
        # Support multiple response shapes: dict-like (legacy) or object with .data
        items = None
        if isinstance(resp, dict) and "data" in resp:
            items = resp["data"]
        else:
            items = getattr(resp, "data", resp)

        out = []
        for d in items:
            if isinstance(d, dict):
                out.append(d.get("embedding"))
            else:
                # object-style response: attribute access
                out.append(getattr(d, "embedding", None))
        return out
