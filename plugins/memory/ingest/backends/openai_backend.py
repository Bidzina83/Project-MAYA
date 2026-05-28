import os
import time
import random
import logging
from typing import Callable, Any, List, Optional

# Try to import both the classic openai module and the new OpenAI client
try:
    import openai
    from openai import error as openai_error
except Exception:
    openai = None
    openai_error = None

try:
    # New-style client class available in openai>=1.x
    from openai import OpenAI as OpenAIClient
except Exception:
    OpenAIClient = None

log = logging.getLogger(__name__)


def _backoff_sleep(attempt: int, backoff_factor: float = 0.5, max_sleep: float = 60.0):
    # Exponential backoff with jitter
    sleep = min(max_sleep, backoff_factor * (2 ** attempt))
    # add jitter
    sleep = sleep * (0.5 + random.random() * 0.5)
    time.sleep(sleep)


class OpenAIBackend:
    """OpenAI embeddings backend wrapper with retry/backoff logic.

    Supports both the legacy openai package usage (openai.Embedding.create(...))
    and the new openai>=1.x client (from openai import OpenAI; client = OpenAI(); client.embeddings.create(...)).

    Expects OPENAI_API_KEY in env for real calls. If openai package is not
    installed or API key missing, calls will raise with a helpful message.
    """

    def __init__(self, model: Optional[str] = None, max_retries: int = 5, backoff_factor: float = 0.5):
        self.model = model or os.environ.get("OPENAI_EMBED_MODEL", "text-embedding-3-small")
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self._client = None

        if self.api_key:
            # Prefer new-style OpenAI client when available
            if OpenAIClient is not None:
                try:
                    self._client = OpenAIClient(api_key=self.api_key)
                except Exception:
                    # fall back to setting module-level api_key
                    self._client = None
            if self._client is None and openai is not None:
                try:
                    # legacy binding
                    openai.api_key = self.api_key
                    self._client = openai
                except Exception:
                    self._client = None

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
                try:
                    if status and int(status) in (429, 500, 502, 503, 504):
                        retryable = True
                except Exception:
                    pass
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
        if self._client is None:
            raise RuntimeError("OpenAI client is not configured: ensure OPENAI_API_KEY is set and openai package is installed")

        def do_request():
            # New client (openai>=1.x): client.embeddings.create(model=..., input=[...])
            if OpenAIClient is not None and hasattr(self._client, 'embeddings'):
                return self._client.embeddings.create(model=self.model, input=texts)
            # Legacy module: openai.Embedding.create(...)
            if openai is not None and hasattr(openai, 'Embedding'):
                return openai.Embedding.create(model=self.model, input=texts)
            # Fallback: try attribute access (best-effort)
            if hasattr(self._client, 'Embedding'):
                return getattr(self._client, 'Embedding').create(model=self.model, input=texts)
            raise RuntimeError('No compatible OpenAI embedding client available')

        resp = self._call_with_retries(do_request)

        # Normalize response: resp.data may be a list of dicts or objects with .embedding
        data = None
        if isinstance(resp, dict):
            data = resp.get('data')
        else:
            data = getattr(resp, 'data', None)

        if data is None:
            raise RuntimeError('Unexpected OpenAI response shape')

        def _extract_embedding(item: Any) -> List[float]:
            if isinstance(item, dict):
                emb = item.get('embedding')
            else:
                emb = getattr(item, 'embedding', None)
            if emb is None:
                raise RuntimeError('Missing embedding in OpenAI response item')
            return emb

        return [_extract_embedding(d) for d in data]