import pytest

from maya_dev.plugins.memory.ingest import config


def test_validate_backend_ok():
    config.validate_backend("openai")
    config.validate_backend("hf")


def test_validate_backend_bad():
    with pytest.raises(ValueError):
        config.validate_backend("unknown-backend")


def test_validate_model_ok():
    # exact
    config.validate_model_for_backend("openai", "text-embedding-3-small")
    # prefix
    config.validate_model_for_backend("openai", "text-embedding-3-large")
    config.validate_model_for_backend("hf", "sentence-transformers/all-MiniLM-L6-v2")


def test_validate_model_bad():
    with pytest.raises(ValueError):
        config.validate_model_for_backend("openai", "sentence-transformers/all-MiniLM-L6-v2")
    with pytest.raises(ValueError):
        config.validate_model_for_backend("hf", "text-embedding-3-small")
