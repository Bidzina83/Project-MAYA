"""G0 selected-provider SDK fixtures, not live or native-loop qualification."""

import json
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

import httpx
from openai import OpenAI

CONTRACT = Path(__file__).resolve().parents[1] / "docs/architecture/governance-g0-baseline.json"


class TestGovernanceProviderProfile(unittest.TestCase):
    def fixture_call(self, output):
        route = json.loads(CONTRACT.read_text())["profile"]["customer_route"]
        calls = []

        def fixture(request):
            self.assertEqual(request.method, "POST")
            self.assertEqual(str(request.url), route["base_url"] + "/responses")
            body = json.loads(request.content)
            self.assertEqual(body["model"], route["model"])
            self.assertEqual(body["reasoning"], {"effort": route["reasoning_effort"]})
            self.assertFalse(body["store"])
            self.assertEqual([t["type"] for t in body["tools"]], ["function"])
            calls.append(body)
            return httpx.Response(200, json={
                "id": "resp_g0_fixture", "object": "response", "created_at": 0,
                "status": "completed", "model": route["model"], "output": output,
                "error": None, "incomplete_details": None, "parallel_tool_calls": False,
                "tools": [], "tool_choice": "auto", "store": False,
                "usage": {"input_tokens": 1, "output_tokens": 1, "total_tokens": 2},
            })

        with patch.object(socket.socket, "connect", side_effect=AssertionError("No live provider")):
            with httpx.Client(transport=httpx.MockTransport(fixture), follow_redirects=False) as http:
                with OpenAI(api_key="g0-synthetic-fixture-only", base_url=route["base_url"],
                            http_client=http, max_retries=0) as client:
                    result = client.responses.create(
                        model=route["model"], input="synthetic business question",
                        reasoning={"effort": route["reasoning_effort"]}, store=False,
                        tools=[{"type": "function", "name": "read_file",
                                "description": "Read one synthetic fixture document",
                                "parameters": {"type": "object", "properties": {
                                    "path": {"type": "string"}}, "required": ["path"],
                                    "additionalProperties": False}, "strict": True}],
                    )
        self.assertEqual(len(calls), 1)
        return result

    def test_selected_responses_text_fixture_parses_without_network(self):
        response = self.fixture_call([{
            "id": "msg_g0", "type": "message", "role": "assistant", "status": "completed",
            "content": [{"type": "output_text", "text": "Synthetic approved answer", "annotations": []}],
        }])
        self.assertEqual(response.output_text, "Synthetic approved answer")

    def test_selected_responses_tool_fixture_is_not_a_chat_completion(self):
        response = self.fixture_call([{
            "id": "fc_g0", "type": "function_call", "call_id": "call_g0",
            "name": "read_file", "arguments": json.dumps({"path": "synthetic-approved.txt"}),
        }])
        self.assertEqual(response.output[0].type, "function_call")
        self.assertEqual(response.output[0].name, "read_file")
        self.assertEqual(json.loads(response.output[0].arguments), {"path": "synthetic-approved.txt"})


if __name__ == "__main__":
    unittest.main()
