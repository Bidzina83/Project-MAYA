"""Offline checkpoint probes imported against the complete staged native runtime.

This is sink/routing/search regression evidence, not G1 or product qualification.
"""

import ast
from datetime import datetime
import logging
from pathlib import Path
from unittest.mock import patch

import httpx
import pytest

from utils import base_url_host_matches, endpoint_log_label
from agent import anthropic_adapter as aa
from agent import auxiliary_client as aux
from hermes_state import SessionDB
from run_agent import AIAgent

MARKER = "secZ9Q8R-candidate-private-value-P4N7"


@pytest.mark.parametrize("domain", ["azure.com", "openai.azure.com", "anthropic.com",
    "api.githubcopilot.com", "integrate.api.nvidia.com", "api.kimi.com", "xiaomimimo.com"])
def test_hostname_controls_reject_path_query_and_lookalike_hosts(domain):
    assert base_url_host_matches("https://" + domain + "/v1", domain)
    assert base_url_host_matches("https://resource." + domain.upper() + ".:443/v1", domain)
    for url in ["https://evil.test/" + domain, "https://evil.test/?host=" + domain,
                "https://" + domain + ".evil.test/v1", "https://fake-" + domain,
                "https://" + domain + "@evil.test/v1",
                "https://evil.test\\@" + domain + "/v1",
                "https://" + domain + ":bad/v1", "https://[broken"]:
        assert not base_url_host_matches(url, domain), url


def test_native_anthropic_auth_header_selection_uses_actual_host():
    credential = "sk-ant-oat01-" + MARKER
    for url in ["https://anthropic.com.evil.test/v1", "https://evil.test/anthropic.com",
                "https://evil.test/?route=azure.com"]:
        with patch.object(aa, "_anthropic_sdk") as sdk:
            aa.build_anthropic_client(credential, base_url=url)
            kwargs = sdk.Anthropic.call_args.kwargs
            assert kwargs["api_key"] == credential
            assert "auth_token" not in kwargs
            assert "Authorization" not in kwargs.get("default_headers", {})
    with patch.object(aa, "_anthropic_sdk") as sdk:
        aa.build_anthropic_client(credential, base_url="https://api.anthropic.com")
        assert sdk.Anthropic.call_args.kwargs["auth_token"] == credential
    assert aa._requires_bearer_auth("https://resource.services.ai.azure.com/anthropic")
    assert aa._requires_bearer_auth("https://api.minimax.io/anthropic")
    assert not aa._requires_bearer_auth("https://evil.test/azure.com")


def test_kimi_route_is_path_bounded_and_rewrite_is_host_bounded():
    assert aa._is_kimi_coding_endpoint("https://api.kimi.com/coding/v1")
    assert not aa._is_kimi_coding_endpoint("https://api.kimi.com/codingevil")
    assert not aux._endpoint_speaks_anthropic_messages("https://api.kimi.com/?route=/coding")
    assert aux._to_openai_base_url("https://api.kimi.com/coding") == "https://api.kimi.com/coding/v1"
    hostile = "https://evil.test/api.kimi.com/coding"
    assert aux._to_openai_base_url(hostile) == hostile
    assert aux._to_openai_base_url("https://open.bigmodel.cn/api/anthropic") == "https://open.bigmodel.cn/api/paas/v4"


def test_native_auxiliary_logs_omit_every_url_component(caplog):
    url = "https://" + MARKER + ":password@example.test/" + MARKER + "/anthropic"
    with caplog.at_level(logging.DEBUG):
        assert aux._to_openai_base_url(url).endswith("/v1")
        with patch.object(aa, "build_anthropic_client", side_effect=RuntimeError(MARKER)):
            aux._maybe_wrap_anthropic(object(), "synthetic-model", "synthetic-key", url, "anthropic_messages")
    assert MARKER not in caplog.text
    assert "<configured-endpoint>" in caplog.text


def test_log_labels_and_masker_never_return_credential_fragments():
    class Unformattable:
        def __str__(self):
            raise AssertionError("diagnostics must not format endpoint objects")
    assert endpoint_log_label(Unformattable()) == "<configured-endpoint>"
    agent = AIAgent.__new__(AIAgent)
    assert agent._mask_api_key_for_logs(MARKER) == "<configured-credential>"
    assert agent._mask_api_key_for_logs("short") == "<configured-credential>"
    assert agent._mask_api_key_for_logs(None) is None
    assert agent._mask_api_key_for_logs(lambda: pytest.fail("credential callback invoked")) == "<entra-id-bearer>"
    agent.provider, agent.model = "openai", "synthetic-model"
    agent.base_url = "https://example.test/" + MARKER + "?token=" + MARKER
    assert MARKER not in agent._client_log_context()


def test_complete_native_startup_banner_does_not_print_key_or_endpoint(capsys):
    transport = httpx.MockTransport(lambda request: pytest.fail("startup attempted inference"))
    from openai import OpenAI
    client = OpenAI(api_key=MARKER, base_url="https://example.test/v1",
                    http_client=httpx.Client(transport=transport), max_retries=0)
    with patch.object(AIAgent, "_create_openai_client", return_value=client), \
            patch("run_agent.get_tool_definitions", return_value=[]), \
            patch("run_agent.check_toolset_requirements", return_value={}):
        agent = AIAgent(model="synthetic-model", provider="openai", api_key=MARKER,
                        base_url="https://example.test/" + MARKER,
                        enabled_toolsets=[], skip_memory=True, skip_context_files=True,
                        quiet_mode=False, max_iterations=1)
    assert agent.model == "synthetic-model"
    output = capsys.readouterr().out
    assert MARKER not in output
    assert MARKER[:8] not in output and MARKER[-4:] not in output
    assert "configured (hidden)" in output
    client.close()


def test_complete_native_cli_config_display_omits_key(capsys):
    from cli import HermesCLI
    cli = HermesCLI.__new__(HermesCLI)
    cli.api_key, cli.base_url, cli.model = MARKER, "https://example.test/" + MARKER, "synthetic-model"
    cli.max_turns, cli.enabled_toolsets, cli.verbose = 1, [], False
    cli.session_start = datetime(2026, 1, 1)
    cli.show_config()
    output = capsys.readouterr().out
    assert MARKER not in output
    assert MARKER[:8] not in output and MARKER[-4:] not in output
    assert "Configured (hidden)" in output
    assert "synthetic-model" in output


def test_no_credential_slice_survives_in_native_diagnostic_modules():
    for name in ["run_agent.py", "cli.py", "agent/agent_init.py", "agent/conversation_loop.py"]:
        tree = ast.parse(Path(name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Slice):
                assert ast.unparse(node.value) not in {"key", "key_used", "effective_key", "self.api_key"}


def test_native_anthropic_startup_banner_omits_alias_fragments(capsys):
    with patch.object(aa, "build_anthropic_client"), \
            patch("run_agent.get_tool_definitions", return_value=[]), \
            patch("run_agent.check_toolset_requirements", return_value={}):
        AIAgent(model="synthetic-model", provider="anthropic", api_mode="anthropic_messages",
                api_key=MARKER, base_url="https://api.anthropic.com", enabled_toolsets=[],
                skip_memory=True, skip_context_files=True, quiet_mode=False, max_iterations=1)
    output = capsys.readouterr().out
    assert MARKER[:8] not in output and MARKER[-4:] not in output
    assert "configured (hidden)" in output


def test_native_endpoint_heuristic_does_not_select_key_for_unrelated_tld(monkeypatch):
    from hermes_cli import runtime_provider as rp
    monkeypatch.setattr(rp, "_getenv", lambda name, default="": MARKER)
    assert rp._host_derived_api_key("https://api.anthropic.test/v1") == ""
    assert rp._host_derived_api_key("https://api.deepseek.test/v1") == ""
    assert rp._host_derived_api_key("https://api.groq.com/openai/v1") == MARKER
    assert rp._host_derived_api_key("https://api.mistral.ai/v1") == MARKER
    monkeypatch.setattr(rp, "_try_resolve_from_custom_pool", lambda *args: None)
    result = rp._resolve_named_custom_runtime(requested_provider="custom", explicit_api_key=None,
                                            explicit_base_url="https://api.anthropic.test/v1")
    assert result["api_key"] == "no-key-required"
    assert result["base_url"] == "https://api.anthropic.test/v1"


def test_adjacent_ollama_and_discovery_diagnostics_omit_endpoint(caplog, monkeypatch):
    from types import SimpleNamespace
    from agent.conversation_loop import _ollama_context_limit_error
    from hermes_cli import runtime_provider as rp
    endpoint = "http://127.0.0.1:1234/" + MARKER
    agent = SimpleNamespace(_ollama_num_ctx=1, model="synthetic-model", provider="ollama",
                            base_url=endpoint, tools=[{"name": "synthetic-tool"}], session_id="synthetic-session")
    with caplog.at_level(logging.DEBUG):
        assert _ollama_context_limit_error(agent, 10)
        with patch("requests.get", side_effect=RuntimeError(MARKER)):
            assert rp._auto_detect_local_model(endpoint) == ""
    assert MARKER not in caplog.text


@pytest.mark.parametrize("url", ["https://api.minimax.io:443/anthropic", "https://api.minimax.io./anthropic",
                                "https://api.minimaxi.com/anthropic/v1"])
def test_minimax_auth_preserves_equivalent_endpoint_forms(url):
    assert aa._requires_bearer_auth(url)
    assert aa._is_minimax_anthropic_endpoint(url)
    assert not aa._is_minimax_anthropic_endpoint(url.replace("/anthropic", "/anthropicevil"))


@pytest.mark.parametrize("query, expected", [
    ("chat-send", '"chat-send"'), ("my.app_config.ts", '"my.app_config.ts"'),
    ("a_b_c", '"a_b_c"'), ("deploy*", "deploy*"),
    ('"exact phrase" OR chat-send', '"exact phrase" OR "chat-send"'),
    ("OR world", "world"), ("hello AND", "hello"), ("ქართული", "ქართული")])
def test_search_legitimate_semantics(query, expected):
    assert SessionDB._sanitize_fts5_query(query) == expected


def test_search_adversarial_shape_and_limit_use_real_sqlite(tmp_path):
    db = SessionDB(tmp_path / "native-search.db")
    db.create_session("checkpoint-session", source="cli", model="synthetic-model")
    db.append_message("checkpoint-session", role="user", content="approved chat-send information")
    assert db.search_messages("chat-send")
    for query in ["0_" * 1024 + "!", "foo" + " " * 2000 + "bar", '"q" ' * 500]:
        assert isinstance(SessionDB._sanitize_fts5_query(query), str)
        assert isinstance(db.search_messages(query), list)
    with pytest.raises(ValueError, match="^session.search_query_invalid$"):
        db.search_messages("0_" * 3000)
    db.close()
