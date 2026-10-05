"""Native optional-cache ordinary controls, run on patched and unpatched source."""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from agent import conversation_loop
from hermes_cli import middleware


@pytest.mark.parametrize("history,stored", [([], None), ([{"role": "user", "content": "fixture"}], "fixture snapshot")])
def test_ordinary_snapshot_behavior(monkeypatch, history, stored):
    if hasattr(middleware, "mandatory_middleware_enabled"):
        monkeypatch.setattr(middleware, "mandatory_middleware_enabled", lambda: False)
    db = SimpleNamespace(get_session=Mock(return_value={"system_prompt": stored}), update_system_prompt=Mock())
    agent = SimpleNamespace(_session_db=db, session_id="fixture-session", _cached_system_prompt=None,
                            _build_system_prompt=Mock(return_value="fresh fixture prompt"), model="fixture")
    monkeypatch.setattr(conversation_loop, "_stored_prompt_matches_runtime", lambda *args: True)
    import agent.credits_tracker as credits
    import hermes_cli.plugins as plugins
    monkeypatch.setattr(credits, "seed_credits_at_session_start", lambda *args: None)
    monkeypatch.setattr(plugins, "invoke_hook", lambda *args, **kwargs: None)
    conversation_loop._restore_or_build_system_prompt(agent, "", history)
    if stored:
        assert agent._cached_system_prompt == stored
        agent._build_system_prompt.assert_not_called()
        db.update_system_prompt.assert_not_called()
    else:
        assert agent._cached_system_prompt == "fresh fixture prompt"
        db.update_system_prompt.assert_called_once_with("fixture-session", "fresh fixture prompt")
