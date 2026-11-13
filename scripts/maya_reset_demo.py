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


def hermes_turn_main():
    from contextlib import redirect_stdout

    import httpx
    captured = []

    def capture(request):
        if captured or request.method != "POST" or str(request.url) != (
            "https://maya-reset.invalid/v1/chat/completions"
        ):
            raise ValueError("Unexpected synthetic SDK request")
        captured.append(request.content.decode("utf-8"))
        print(json.dumps(captured[0]), file=sys.__stdout__, flush=True)
        answer = json.loads(sys.stdin.readline(8193))
        if answer is None:
            # This callback runs on a Hermes worker thread. Exit the dedicated
            # process rather than let a transport error enter Hermes retry logic.
            print("null", file=sys.__stdout__, flush=True)
            os._exit(0)
        return httpx.Response(200, json={
            "id": "maya-reset-local", "object": "chat.completion", "created": 0,
            "model": "maya-reset-fixture",
            "choices": [{"index": 0, "finish_reason": "stop",
                         "message": {"role": "assistant", "content": answer}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        })

    with redirect_stdout(sys.stderr), httpx.Client(
        transport=httpx.MockTransport(capture), trust_env=False
    ) as client:
        from run_agent import AIAgent

        class OfflineAgent(AIAgent):
            _disable_streaming = True

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
    print(json.dumps(turn.get("final_response")))


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
    endpoint = FixtureEndpoint()
    report = Review(request, endpoint).resolve(approved, candidate)
    report["endpoint_received"] = [asdict(item) for item in endpoint.received]
    print(json.dumps(report))


def operator_review(request):
    from queue import Empty, Queue
    from threading import Thread

    print(json.dumps(vars(request), indent=2))
    choices = Queue(maxsize=1)

    def read_choice():
        try:
            choices.put(input("Approve this synthetic request within 60 seconds? [y/N] ").strip().lower())
        except EOFError:
            choices.put("")

    Thread(target=read_choice, daemon=True).start()
    try:
        choice = choices.get(timeout=60)
    except Empty:
        return dict(resolve_offline(request, False, request), decision="approval_timeout")
    except KeyboardInterrupt:
        choice = ""
    try:
        report = resolve_offline(request, choice == "y", request)
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
    elif len(sys.argv) == 1:
        main()
    else:
        raise SystemExit("Unexpected arguments")
