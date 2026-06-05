import os
import time
import random
import logging
from typing import Callable, Any, List
import importlib
import importlib.util

# Attempt to load a canonical provider adapter if present (per consolidation plan)
_provider_module = None
_provider = None
try:
    # Try package-style import first
    _provider_module = importlib.import_module('src.maya.adapters.openai_provider')
except Exception:
    try:
        _provider_module = importlib.import_module('maya.adapters.openai_provider')
    except Exception:
        # Fallback: try to load from the expected file path directly
        provider_path = '/opt/hermes/src/maya/adapters/openai_provider.py'
        try:
            spec = importlib.util.spec_from_file_location('openai_provider', provider_path)
            if spec and spec.loader:
                _pm = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(_pm)
                _provider_module = _pm
        except Exception:
            _provider_module = None

if _provider_module is not None:
    try:
        # provider exposes a Provider instance at `provider` and a minimal `openai`-like object
        _provider = getattr(_provider_module, 'provider', None)
        _provider_openai = getattr(_provider_module, 'openai', None)
        _provider_error = getattr(_provider_module, 'openai_error', None)
    except Exception:
        _provider = None
        _provider_openai = None
        _provider_error = None
else:
    _provider = None
    _provider_openai = None
    _provider_error = None

# try to import the openai SDK as a fallback
try:
    import openai
    from openai import error as openai_error
except Exception:
    openai = None
    openai_error = None

# If a provider adapter exists, prefer its minimal objects for downstream calls
if _provider_openai is not None:
    openai = _provider_openai
if _provider_error is not None:
    openai_error = _provider_error

# test overrides: prefer overrides module if present
try:
    _test_overrides = importlib.import_module("hermes.plugins.memory.ingest.tests.support.overrides")
except Exception:
    _test_overrides = None

if _test_overrides:
    openai = getattr(_test_overrides, "openai", openai)
    openai_error = getattr(_test_overrides, "openai_error", openai_error)

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
        self._client = None

        if self.api_key:
            # If module-level openai was monkeypatched (tests), prefer that when it exposes expected interface
            if openai is not None and getattr(openai, 'Embedding', None) is not None:
                try:
                    # attach api_key if supported
                    try:
                        openai.api_key = self.api_key
                    except Exception:
                        pass
                    self._client = openai
                except Exception:
                    self._client = None
            else:
                # Prefer new-style OpenAI client when available
                try:
                    from openai import OpenAI as OpenAIClient
                except Exception:
                    OpenAIClient = None
                if OpenAIClient is not None:
                    try:
                        self._client = OpenAIClient(api_key=self.api_key)
                    except Exception:
                        self._client = None
                if self._client is None and openai is not None:
                    try:
                        openai.api_key = self.api_key
                        self._client = openai
                    except Exception:
                        self._client = None

    def _call_with_retries(self, fn: Callable[[], Any]) -> Any:
        last_exc = None
        for attempt in range(self.max_retries):
            try:
                log.debug("OpenAIBackend: calling attempt %s/%s using openai=%s (module=%s)", attempt+1, self.max_retries, openai, getattr(openai, '__name__', None))
                return fn()
            except Exception as e:
                last_exc = e
                # Resolve openai_error from the backend module if tests monkeypatched it
                try:
                    backend_mod = importlib.import_module('plugins.memory.ingest.backends.openai_backend')
                    mod_openai_error = getattr(backend_mod, 'openai_error', openai_error)
                except Exception:
                    mod_openai_error = openai_error
                # Decide whether this is retryable
                retryable = False
                # openai-specific error types
                if mod_openai_error:
                    try:
                        if isinstance(e, getattr(mod_openai_error, 'RateLimitError', ())) or isinstance(e, getattr(mod_openai_error, 'ServiceUnavailableError', ())) or isinstance(e, getattr(mod_openai_error, 'APIError', ())):
                            retryable = True
                    except Exception:
                        pass
                # Network/HTTP-like errors may have status_code attribute
                status = getattr(e, 'http_status', None) or getattr(e, 'status_code', None)
                if status and int(status) in (429, 500, 502, 503, 504):
                    retryable = True
                # Heuristic: treat common exception class names as retryable even if
                # openai_error namespace isn't available or wasn't monkeypatched.
                if not retryable:
                    ename = getattr(e, '__class__', type(e)).__name__
                    if 'RateLimit' in ename or 'Rate' in ename or 'ServiceUnavailable' in ename or 'APIError' in ename:
                        retryable = True

                # supplemental heuristic based on message contents
                msg = str(e).lower()
                if not retryable and ('rate' in msg or 'retry' in msg):
                    retryable = True

                should_log_retry = retryable and (attempt + 1 < self.max_retries)
                if should_log_retry:
                    print("DEBUG_OPENAI_RETRY: attempt=", attempt+1, "exc=", repr(e))
                    log.warning("OpenAIBackend: transient error on attempt %s/%s: %s; retrying...", attempt + 1, self.max_retries, e)
                if not retryable or attempt + 1 == self.max_retries:
                    # no more retries
                    log.debug("OpenAIBackend: not retrying (attempt=%s): %s", attempt, e)
                    raise
                # otherwise backoff and retry
                _backoff_sleep(attempt, self.backoff_factor)
        # if we exit the loop, re-raise last exception
        if last_exc:
            raise last_exc

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        log.debug("OpenAIBackend.embed_batch: openai=%s openai_error=%s api_key=%s provider=%s", openai, openai_error, bool(self.api_key), _provider)
        # Decision logic: prefer module-level openai override when present (tests monkeypatch it).
        # If the module-level openai appears to be a test shim (has Embedding.create), use it.
        openai_has_embedding = bool(getattr(openai, 'Embedding', None) and getattr(openai.Embedding, 'create', None))

        if openai_has_embedding:
            # Use module-level openai client (this honors test monkeypatches)
            def do_request():
                try:
                    backend_mod = importlib.import_module('plugins.memory.ingest.backends.openai_backend')
                    openai_client = getattr(backend_mod, 'openai', openai)
                except Exception:
                    openai_client = openai
                log.debug("OpenAIBackend: do_request calling Embedding.create with model=%s texts_len=%s using client=%s (module-level override)", self.model, len(texts), openai_client)
                return openai_client.Embedding.create(model=self.model, input=texts)
            resp = self._call_with_retries(do_request)
            return [d["embedding"] for d in resp["data"]]

        # If a canonical provider exists, delegate to it (preferred)
        if _provider is not None:
            # provider.embed_batch returns List[List[float]]
            def do_request():
                return _provider.embed_batch(texts, model=self.model)
            resp = self._call_with_retries(do_request)
            return resp

        # Fallback behaviour: use openai-like object present in this module
        if not openai:
            raise RuntimeError("openai package/provider is not available in the environment")
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment")

        def do_request():
            # resolve the backend module to pick up any test monkeypatches
            try:
                backend_mod = importlib.import_module('plugins.memory.ingest.backends.openai_backend')
                openai_client = getattr(backend_mod, 'openai', openai)
            except Exception:
                openai_client = openai
            # OpenAI client expects a single request with list input
            log.debug("OpenAIBackend: do_request calling Embedding.create with model=%s texts_len=%s using client=%s (fallback)", self.model, len(texts), openai_client)
            return openai_client.Embedding.create(model=self.model, input=texts)

        resp = self._call_with_retries(do_request)
        # resp['data'] is list of { 'embedding': [...] }
        log.debug("OpenAIBackend.embed_batch: resp=%s", resp)
        return [d["embedding"] for d in resp["data"]]
