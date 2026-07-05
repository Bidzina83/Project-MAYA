import logging
import sys
import types
from pathlib import Path


def _load_hindsight_plugin(monkeypatch):
    agent_module = types.ModuleType("agent")
    memory_provider_module = types.ModuleType("agent.memory_provider")
    memory_provider_module.MemoryProvider = object
    hermes_constants_module = types.ModuleType("hermes_constants")
    hermes_constants_module.get_hermes_home = lambda: Path(".")
    tools_module = types.ModuleType("tools")
    registry_module = types.ModuleType("tools.registry")
    registry_module.tool_error = lambda message: message

    monkeypatch.setitem(sys.modules, "agent", agent_module)
    monkeypatch.setitem(sys.modules, "agent.memory_provider", memory_provider_module)
    monkeypatch.setitem(sys.modules, "hermes_constants", hermes_constants_module)
    monkeypatch.setitem(sys.modules, "tools", tools_module)
    monkeypatch.setitem(sys.modules, "tools.registry", registry_module)

    import plugins.memory.hindsight as hindsight

    return hindsight


def test_parse_int_setting_does_not_log_invalid_value(monkeypatch, caplog):
    hindsight = _load_hindsight_plugin(monkeypatch)
    secret_like_value = "bad-token-value"

    with caplog.at_level(logging.WARNING, logger=hindsight.logger.name):
        assert hindsight._parse_int_setting(secret_like_value, 120) == 120

    log_text = "\n".join(record.getMessage() for record in caplog.records)
    assert "Invalid integer Hindsight setting" in log_text
    assert secret_like_value not in log_text


def test_embedded_profile_env_filters_secret_shaped_names(monkeypatch):
    hindsight = _load_hindsight_plugin(monkeypatch)
    env_values = hindsight._non_secret_env_values(
        {
            "HINDSIGHT_API_LLM_PROVIDER": "openai",
            "HINDSIGHT_API_KEY": "raw-api-key",
            "HINDSIGHT_LLM_TOKEN": "raw-token",
            "HINDSIGHT_PASSWORD": "raw-password",
            "HINDSIGHT_CREDENTIAL_REF": "raw-credential",
        }
    )

    assert env_values == {"HINDSIGHT_API_LLM_PROVIDER": "openai"}


def test_env_merge_writes_only_allowed_non_secret_settings(monkeypatch):
    hindsight = _load_hindsight_plugin(monkeypatch)

    merged = hindsight._merge_non_secret_env_lines(
        [
            "# existing comment",
            "HINDSIGHT_API_KEY=old-secret",
            "HINDSIGHT_TIMEOUT=60",
        ],
        {
            "HINDSIGHT_TIMEOUT": "120",
            "HINDSIGHT_LLM_TOKEN": "new-token",
            "HINDSIGHT_IDLE_TIMEOUT": "300",
            "HINDSIGHT_API_LLM_PROVIDER": "openai",
        },
    )

    assert merged == [
        "HINDSIGHT_TIMEOUT=120",
        "HINDSIGHT_IDLE_TIMEOUT=300",
    ]


def test_materialized_profile_env_never_writes_secret_shaped_names(monkeypatch, tmp_path):
    hindsight = _load_hindsight_plugin(monkeypatch)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        hindsight,
        "_build_embedded_profile_env",
        lambda config, *, llm_api_key=None: {
            "HINDSIGHT_API_LLM_PROVIDER": "openai",
            "HINDSIGHT_API_KEY": "raw-api-key",
            "HINDSIGHT_LLM_TOKEN": "raw-token",
        },
    )

    hindsight._materialize_embedded_profile_env({"llm_provider": "openai"})

    profile_env = tmp_path / ".hindsight" / "profiles" / "hermes.env"
    contents = profile_env.read_text(encoding="utf-8")
    assert "HINDSIGHT_API_LLM_PROVIDER=openai" in contents
    assert "raw-api-key" not in contents
    assert "raw-token" not in contents
    assert "HINDSIGHT_API_KEY" not in contents
    assert "HINDSIGHT_LLM_TOKEN" not in contents


def test_hindsight_debug_log_does_not_emit_retain_context_value(monkeypatch):
    hindsight = _load_hindsight_plugin(monkeypatch)
    source = Path(hindsight.__file__).read_text(encoding="utf-8")

    assert "retain_context=%s" not in source
    assert "api_url=%s" not in source
