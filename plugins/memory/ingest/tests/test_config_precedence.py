import os
import tomllib
import textwrap

import pytest

from .. import config


def write_toml(path, content):
    with open(path, "wb") as f:
        f.write(content.encode())


def test_env_overrides_toml(monkeypatch, tmp_path):
    # TOML sets backend to hf, env should override to openai
    toml_path = tmp_path / "test_config.toml"
    toml_content = textwrap.dedent('''
        [embeddings]
        backend = "hf"
        model = "sentence-transformers/all-MiniLM-L6-v2"

        [secrets]
        openai_api_key = "from_toml"
    ''')
    write_toml(toml_path, toml_content)

    # ensure env overrides
    monkeypatch.setenv("EMBEDDINGS_BACKEND", "openai")
    monkeypatch.setenv("OPENAI_API_KEY", "from_env")

    config.reload_config(str(toml_path))
    assert config.get_default_backend() == "openai"
    assert config.get_openai_api_key() == "from_env"


def test_toml_used_when_no_env(monkeypatch, tmp_path):
    toml_path = tmp_path / "test_config2.toml"
    toml_content = textwrap.dedent('''
        [embeddings]
        backend = "hf"
        model = "sentence-transformers/all-MiniLM-L6-v2"

        [secrets]
        openai_api_key = "from_toml"
    ''')
    write_toml(toml_path, toml_content)

    # ensure env vars not set
    monkeypatch.delenv("EMBEDDINGS_BACKEND", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    config.reload_config(str(toml_path))
    assert config.get_default_backend() == "hf"
    assert config.get_default_model() == "sentence-transformers/all-MiniLM-L6-v2"
    # get_openai_api_key falls back to toml secrets
    assert config.get_openai_api_key() == "from_toml"


def test_env_precedence_for_keys(monkeypatch, tmp_path):
    toml_path = tmp_path / "test_config3.toml"
    toml_content = textwrap.dedent('''
        [embeddings]
        backend = "hf"
    ''')
    write_toml(toml_path, toml_content)

    monkeypatch.setenv("MAYA_CONFIG_PATH", str(toml_path))
    # env should override when present
    monkeypatch.setenv("EMBEDDINGS_BACKEND", "openai")
    config.reload_config()  # use default path from env
    assert config.get("embeddings.backend") == "openai"
