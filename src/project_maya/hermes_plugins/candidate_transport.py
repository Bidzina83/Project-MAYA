"""Synthetic HTTP responses for offline real-SDK candidate qualification only."""

from __future__ import annotations

import json


def completion_response(request, *, tool: bool, tool_path: str = "denied.txt"):
    import httpx

    if request.method != "POST" or request.url.path != "/v1/chat/completions":
        raise RuntimeError("candidate.unexpected_transport_route")
    body = json.loads(request.content)
    if body.get("model") != "synthetic-model":
        raise RuntimeError("candidate.unexpected_transport_model")
    message = {"role": "assistant", "content": "Synthetic approved response"}
    finish = "stop"
    if tool:
        message = {"role": "assistant", "content": None, "tool_calls": [
            {"id": "candidate-read", "type": "function", "function": {
                "name": "read_file", "arguments": json.dumps({"path": tool_path, "offset": 1, "limit": 1})}}
        ]}
        finish = "tool_calls"
    base = {"id": "candidate-completion", "created": 0, "model": "synthetic-model"}
    if not body.get("stream"):
        return httpx.Response(200, json=dict(base, object="chat.completion", choices=[
            {"index": 0, "message": message, "finish_reason": finish}]))
    delta = dict(message)
    if tool:
        delta["tool_calls"][0]["index"] = 0
    chunks = [dict(base, object="chat.completion.chunk", choices=[
        {"index": 0, "delta": delta, "finish_reason": None}]),
        dict(base, object="chat.completion.chunk", choices=[
            {"index": 0, "delta": {}, "finish_reason": finish}])]
    content = "".join("data: " + json.dumps(chunk) + "\n\n" for chunk in chunks) + "data: [DONE]\n\n"
    return httpx.Response(200, headers={"content-type": "text/event-stream"}, content=content)
