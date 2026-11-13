"""Offline feasibility slice using one tool-free Hermes turn."""

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from uuid import uuid4


@dataclass(frozen=True)
class Request:
    id: str
    document: str
    question: str
    destination: str = "synthetic:local-fixture"
    payload: str = ""


DOCUMENT = "Acme purchase order 1042 specifies payment within 30 days of invoice."
QUESTION = "What are Acme's payment terms?"
SYSTEM = "Answer using only the synthetic document provided."


def validate_payload(body):
    expected = {
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": DOCUMENT + "\n\n" + QUESTION},
        ],
        "model": "maya-reset-fixture", "max_tokens": 32, "stream": False,
    }
    canonical = json.dumps(expected, ensure_ascii=False, separators=(",", ":"))
    if body != canonical:
        raise ValueError("Unexpected content in synthetic SDK request")


def hermes_request(review=None):
    with TemporaryDirectory(prefix="maya-reset-") as home:
        env = {key: os.environ[key] for key in ("SystemRoot", "WINDIR", "PATH") if key in os.environ}
        env.update(HERMES_HOME=home, HOME=home, USERPROFILE=home, TEMP=home, TMP=home,
                   HERMES_DISABLE_LAZY_INSTALLS="1")
        Path(home, "config.yaml").write_text(
            "agent:\n  environment_probe: false\ncompression:\n  enabled: false\n", encoding="ascii"
        )
        process = subprocess.Popen(
            [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--hermes-turn"],
            cwd=home, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8",
        )
        try:
            from concurrent.futures import ThreadPoolExecutor

            with ThreadPoolExecutor(max_workers=1) as reader:
                try:
                    line = reader.submit(process.stdout.readline, 16385).result(timeout=60)
                except TimeoutError:
                    process.kill()
                    raise
            request = Request(uuid4().hex, DOCUMENT, QUESTION, payload=json.loads(line))
            validate_payload(request.payload)
            report = review(request) if review is not None else None
            answer = report["result"]["answer"] if report and report["result"] else None
            stdout, _ = process.communicate(json.dumps(answer) + "\n", timeout=10)
            if process.returncode or json.loads(stdout) != answer:
                raise ValueError("Hermes did not return the broker decision")
            return request if review is None else dict(report, hermes_answer=answer)
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            process.stdin.close()
            process.stdout.close()


def hermes_turn_main(exchange=None, finish=None):
    from contextlib import redirect_stdout
    import logging
    from unittest.mock import patch

    bundle = Path(__file__).resolve().parent
    if Path(sys.executable).resolve().parent == bundle / "python":
        sys.path[:0] = [str(bundle / name) for name in ("hermes", "dependencies")]

    import httpx
    captured = []

    def capture(request):
        if captured or request.method != "POST" or str(request.url) != (
            "https://maya-reset.invalid/v1/chat/completions"
        ):
            raise ValueError("Unexpected synthetic SDK request")
        captured.append(request.content.decode("utf-8"))
        validate_payload(captured[0])
        if exchange is None:
            print(json.dumps(captured[0]), file=sys.__stdout__, flush=True)
            answer = json.loads(sys.stdin.readline(8193))
        else:
            answer = exchange(captured[0])
        if answer is None:
            # This callback runs on a Hermes worker thread. Exit the dedicated
            # process rather than let a transport error enter Hermes retry logic.
            if finish is None:
                print("null", file=sys.__stdout__, flush=True)
            else:
                finish(None)
            os._exit(0)
        return httpx.Response(200, json={
            "id": "maya-reset-local", "object": "chat.completion", "created": 0,
            "model": "maya-reset-fixture",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": answer}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    # The broker receipt, not Hermes file logs, is the demo evidence.
    with redirect_stdout(sys.stderr), patch("hermes_logging.setup_logging", lambda **_: None), httpx.Client(
        transport=httpx.MockTransport(capture), trust_env=False
    ) as client:
        from run_agent import AIAgent

        class OfflineAgent(AIAgent):
            _disable_streaming = True

            def _build_system_prompt(self, system_message=None):
                return SYSTEM

            def _create_openai_client(self, client_kwargs, *, reason, shared):
                return super()._create_openai_client(
                    dict(client_kwargs, http_client=client, max_retries=0),
                    reason=reason, shared=False,
                )

        agent = OfflineAgent(provider="custom", api_mode="chat_completions",
            base_url="https://maya-reset.invalid/v1", api_key="synthetic", model="maya-reset-fixture",
            max_tokens=32, max_iterations=1, enabled_toolsets=[], skip_memory=True,
            skip_context_files=True, load_soul_identity=False, session_db=None,
            checkpoints_enabled=False, fallback_model=None, credential_pool=None,
            quiet_mode=True, save_trajectories=False, request_overrides={"stream": False})
        if agent.tools or agent.valid_tool_names or agent._memory_enabled or agent.compression_enabled:
            raise ValueError("Unexpected Hermes capabilities in reset demo")
        turn = agent.run_conversation(DOCUMENT + "\n\n" + QUESTION)
    if len(captured) != 1:
        raise ValueError("Synthetic Hermes turn did not complete")
    answer = turn.get("final_response")
    if finish is None:
        print(json.dumps(answer))
    else:
        finish(answer)


def private_hermes_turn_main(probe=False):
    """One synthetic turn over the launcher's inherited standard handles."""
    import struct

    incoming, outgoing = sys.stdin.buffer, sys.__stdout__.buffer

    def send(record):
        body = json.dumps(record, ensure_ascii=False).encode("utf-8")
        if not 1 <= len(body) <= 8192:
            raise ValueError("Invalid private frame size")
        outgoing.write(struct.pack("<I", len(body)) + body)
        outgoing.flush()

    def exchange(payload):
        send({"kind": "request", "payload": payload})
        header = incoming.read(4)
        if len(header) != 4:
            raise EOFError("Missing private reply")
        size, = struct.unpack("<I", header)
        if not 1 <= size <= 8192:
            raise ValueError("Invalid private reply size")
        body = incoming.read(size)
        if len(body) != size:
            raise EOFError("Incomplete private reply")
        reply = json.loads(body)
        if (not isinstance(reply, dict) or set(reply) != {"kind", "answer"}
                or reply["kind"] != "decision"
                or reply["answer"] not in (None, "Payment is due within 30 days of invoice.")):
            raise ValueError("Invalid private decision")
        return reply["answer"]

    if probe:
        reset_tcp_probe()
    hermes_turn_main(exchange, lambda answer: send({"kind": "complete", "answer": answer}))


def reset_tcp_probe():
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(2.0)
        try:
            probe.connect(("100.127.155.29", 49187))
        except OSError:
            # Only trusted WFP and listener evidence can classify this attempt.
            pass


def isolated_hermes_turn_main():
    reset_tcp_probe()
    hermes_turn_main()


class FixtureEndpoint:
    def __init__(self):
        self.received = []

    def send(self, request):
        self.received.append(request)
        return {"answer": "Payment is due within 30 days of invoice.", "excerpt": DOCUMENT}


class Review:
    def __init__(self, request, endpoint):
        self.request = request
        self.endpoint = endpoint
        self.used = False

    def resolve(self, approved, candidate):
        if self.used:
            return {"request_id": self.request.id, "decision": "already_resolved"}
        self.used = True
        report = {"request_id": self.request.id, "decision": "denied", "result": None}
        if approved is not True:
            return report
        if candidate != self.request:
            report["decision"] = "request_changed"
            return report
        try:
            report["result"] = self.endpoint.send(candidate)
            report["decision"] = "approved"
        except Exception:
            report["decision"] = "dispatch_failed"
        return report


def resolve_offline(request, approved, candidate):
    """Only the trusted operator process supplies the approval decision."""
    completed = subprocess.run(
        [sys.executable, "-I", "-B", str(Path(__file__).resolve()), "--broker"],
        input=json.dumps([asdict(request), approved, asdict(candidate)]),
        capture_output=True, text=True, check=True, timeout=5,
    )
    return json.loads(completed.stdout)


def broker_main():
    request, approved, candidate = json.loads(sys.stdin.read(8193))
    request, candidate = Request(**request), Request(**candidate)
    if (request.document, request.question, request.destination) != (
        DOCUMENT, QUESTION, "synthetic:local-fixture"
    ):
        raise ValueError("Only the fixed synthetic fixture is supported")
    validate_payload(request.payload)
    endpoint = FixtureEndpoint()
    report = Review(request, endpoint).resolve(approved, candidate)
    report["endpoint_received"] = [asdict(item) for item in endpoint.received]
    print(json.dumps(report))


def operator_review(request):
    from queue import Empty, Queue
    from threading import Thread

    print(json.dumps(vars(request), indent=2), flush=True)
    print("Type y to approve or n to deny, then press Enter (60 seconds).", flush=True)
    choices = Queue(maxsize=1)

    def read_choice():
        try:
            choice = input().strip().lower()
            choices.put({"y": "approved", "n": "denied", "": "blank_input"}.get(choice, "invalid_input"))
        except EOFError:
            choices.put("end_of_input")

    Thread(target=read_choice, daemon=True).start()
    try:
        outcome = choices.get(timeout=60)
    except Empty:
        outcome = "approval_timeout"
    except KeyboardInterrupt:
        outcome = "approval_cancelled"
    try:
        report = resolve_offline(request, outcome == "approved", request)
        if report["decision"] == "denied":
            report["decision"] = outcome
    except (subprocess.SubprocessError, OSError, ValueError):
        report = {"request_id": request.id, "decision": "broker_failed",
                  "result": None, "endpoint_received": None}
    return report


def main():
    print(json.dumps(hermes_request(operator_review), indent=2))


if __name__ == "__main__":
    if sys.argv[1:] == ["--broker"]:
        broker_main()
    elif sys.argv[1:] == ["--hermes-turn"]:
        hermes_turn_main()
    elif sys.argv[1:] == ["--isolated-hermes-turn"]:
        isolated_hermes_turn_main()
    elif sys.argv[1:] == ["--private-hermes-turn"]:
        private_hermes_turn_main()
    elif sys.argv[1:] == ["--private-hermes-tcp-turn"]:
        private_hermes_turn_main(probe=True)
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("Unexpected arguments")
