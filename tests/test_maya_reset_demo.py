from dataclasses import replace
import runpy
from pathlib import Path


demo = runpy.run_path(str(Path(__file__).resolve().parents[1] / "scripts/maya_reset_demo.py"))
Request, Review, FixtureEndpoint = (demo[name] for name in ("Request", "Review", "FixtureEndpoint"))


def test_approval_dispatches_exact_request_once():
    request = Request("r1", demo["DOCUMENT"], demo["QUESTION"])
    endpoint = FixtureEndpoint()
    review = Review(request, endpoint)
    result = review.resolve(True, request)
    assert result["result"]["excerpt"] == request.document
    assert review.resolve(True, request)["decision"] == "already_resolved"
    assert endpoint.received == [request]


def test_denied_and_altered_requests_never_reach_endpoint():
    request = Request("r1", "synthetic", "question")
    endpoint = FixtureEndpoint()
    for approved, candidate, decision in [
        (False, request, "denied"),
        (True, replace(request, document="changed"), "request_changed"),
        (True, replace(request, destination="changed"), "request_changed"),
    ]:
        result = Review(request, endpoint).resolve(approved, candidate)
        assert result["decision"] == decision and result["result"] is None
    assert endpoint.received == []


def test_failure_is_not_retried():
    class FailedEndpoint(FixtureEndpoint):
        def send(self, request):
            self.received.append(request)
            raise OSError

    request = Request("r1", "synthetic", "question")
    endpoint = FailedEndpoint()
    review = Review(request, endpoint)
    result = review.resolve(True, request)
    assert result["decision"] == "dispatch_failed" and result["result"] is None
    review.resolve(True, request)
    assert endpoint.received == [request]


def test_receiver_evidence_from_separate_process():
    request = demo["hermes_request"]()
    resolve = demo["resolve_offline"]
    allowed = resolve(request, True, request)
    assert allowed["decision"] == "approved"
    assert allowed["endpoint_received"] == [vars(request)]
    assert allowed["result"]["excerpt"] == request.document
    for approve, candidate, decision in (
        (False, request, "denied"),
        (True, replace(request, question="Changed"), "request_changed"),
        (True, replace(request, payload=request.payload.replace("30 days", "60 days")), "request_changed"),
        (True, replace(request, payload=request.payload + " "), "request_changed"),
    ):
        result = resolve(request, approve, candidate)
        assert result["decision"] == decision
        assert result["endpoint_received"] == []
        assert result["result"] is None


def test_same_turn_receives_only_the_approved_answer():
    resolve = demo["resolve_offline"]
    for approved, altered, expected in (
        (True, False, "approved"),
        (False, False, "denied"),
        (True, True, "request_changed"),
    ):
        report = demo["hermes_request"](
            lambda request: resolve(request, approved,
                replace(request, payload=request.payload + " ") if altered else request)
        )
        assert report["decision"] == expected
        assert len(report["endpoint_received"]) == (1 if expected == "approved" else 0)
        assert report["hermes_answer"] == (report["result"]["answer"] if expected == "approved" else None)
