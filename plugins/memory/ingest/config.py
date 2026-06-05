"""Configuration loader for Project MAYA embedder and related tooling.

Priority order for settings:
 1) Environment variables (UPPERCASE names)
 2) TOML config file (path from MAYA_CONFIG_PATH or /opt/data/maya-dev/config.toml)
 3) Built-in defaults

This module avoids loading secrets from the repo by preferring env vars for API keys.
"""
from __future__ import annotations
import os
from typing import Any

try:
    import tomllib
except Exception:
    tomllib = None


DEFAULT_CONFIG_PATH = os.environ.get("MAYA_CONFIG_PATH", "/opt/data/maya-dev/config.toml")


def _load_toml(path: str) -> dict:
    if not tomllib:
        return {}
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def load_config(path: str | None = None) -> dict:
    path = path or DEFAULT_CONFIG_PATH
    return _load_toml(path)


# Cached config
_CONFIG = load_config()


def reload_config(path: str | None = None) -> dict:
    global _CONFIG
    _CONFIG = load_config(path)
    return _CONFIG


def _get_from_config(keys: list[str], default: Any = None) -> Any:
    cfg = _CONFIG
    try:
        for k in keys:
            cfg = cfg[k]
        return cfg
    except Exception:
        return default


def get(key: str, default: Any = None) -> Any:
    """Generic getter: reads from env (uppercased) then config toml under dotted key.

    Example: get('embeddings.backend') -> checks EMBEDDINGS_BACKEND env, then config['embeddings']['backend']
    """
    env_name = key.replace(".", "_").upper()
    if env_name in os.environ:
        return os.environ[env_name]
    # dotted lookup in TOML
    parts = key.split(".")
    return _get_from_config(parts, default)


# Specific helpers
def get_default_backend() -> str:
    return str(get("embeddings.backend", "openai"))


def get_default_model() -> str:
    return str(get("embeddings.model", "text-embedding-3-small"))


def get_openai_api_key() -> str | None:
    return os.environ.get("OPENAI_API_KEY") or _get_from_config(["secrets", "openai_api_key"], None)


def get_hf_api_key() -> str | None:
    return os.environ.get("HF_API_KEY") or _get_from_config(["secrets", "hf_api_key"], None)


def get_config_path() -> str:
    return os.environ.get("MAYA_CONFIG_PATH", DEFAULT_CONFIG_PATH)


# Provider capability metadata and validation
SUPPORTED_BACKENDS = {
    "openai": {
        "name": "OpenAI",
        "models": [
            "text-embedding-3",  # family
            "text-embedding-3-small",
        ],
        "model_prefixes": ["text-embedding-3"],
    },
    "hf": {
        "name": "HuggingFace",
        "models": [
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-MiniLM-L12-v2",
        ],
        "model_prefixes": ["sentence-transformers", "all-"],
    },
}


def validate_backend(backend: str) -> None:
    """Raise ValueError if backend is not supported."""
    if backend not in SUPPORTED_BACKENDS:
        raise ValueError(f"Unsupported backend: {backend}. Supported: {list(SUPPORTED_BACKENDS.keys())}")


def validate_model_for_backend(backend: str, model: str) -> None:
    """Raise ValueError if the model string is not plausibly supported by the backend.

    This is conservative — allows common prefixes and exact matches. It helps catch typos in config.
    """
    validate_backend(backend)
    meta = SUPPORTED_BACKENDS[backend]
    # exact match
    if model in meta.get("models", []):
        return
    # prefix match
    for p in meta.get("model_prefixes", []):
        if model.startswith(p):
            return
    raise ValueError(f"Model '{model}' does not look valid for backend '{backend}'.")
