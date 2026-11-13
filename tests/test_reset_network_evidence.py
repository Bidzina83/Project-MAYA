from dataclasses import replace

import pytest

from project_maya.reset_network_evidence import (
    Block, EndpointObservation, PackageDrop, Route, WindowsObservation,
    TcpDropSnapshot, admit_tcp_snapshot,
    UdpDropSnapshot, admit_attempt, admit_indirect_udp, admit_udp_snapshot, classify_network,
)


ROUTE = Route("tcp", "ipv4", "127.0.0.1", 49160)
EXPECTED = Block(123, "synthetic-package", 456, ROUTE)


@pytest.mark.parametrize(("scenario", "verdict"), [
    ("matching", "tested_route_blocked_indirect"),
    ("no_drop", "inconclusive"),
    ("duplicate", "inconclusive"),
    ("wrong_filter", "inconclusive"),
    ("at_child_stop", "inconclusive"),
    ("partial_collection", "inconclusive"),
    ("nonexclusive_package", "inconclusive"),
    ("early_listener_close", "inconclusive"),
    ("late_host_control", "inconclusive"),
    ("direct_receipt", "direct_receipt_observed"),
    ("public_route", "inconclusive"),
])
def test_private_tcp_isolation_evidence(scenario, verdict):
    route = Route("tcp", "ipv4",
                  "203.0.113.1" if scenario == "public_route" else "100.127.155.29",
                  49187)
    expected = replace(EXPECTED, route=route)
    drop = PackageDrop(30, expected.package, "python.exe", expected.filter_id, route)
    if scenario == "wrong_filter":
        drop = replace(drop, filter_id=expected.filter_id + 1)
    if scenario == "at_child_stop":
        drop = replace(drop, filetime=40)
    drops = () if scenario in {"no_drop", "direct_receipt"} else (drop,)
    if scenario == "duplicate":
        drops = (drop, drop)
    snapshot = TcpDropSnapshot("current", scenario != "partial_collection", drops)
    endpoint = EndpointObservation(
        "current", route, 21 if scenario == "late_host_control" else 10, 15,
        39 if scenario == "early_listener_close" else 45,
        int(scenario == "direct_receipt"), True,
    )
    assert admit_tcp_snapshot(
        "current", expected, executable="python.exe",
        exclusive_package_verified=scenario != "nonexclusive_package",
        clock_window_verified=True, child_start_filetime=20, child_stop_filetime=40,
        snapshot=snapshot, endpoint=endpoint,
    ) == verdict


@pytest.mark.parametrize(("changes", "verdict"), [
    ({}, "tested_route_blocked"),
    ({"observed": None}, "inconclusive"),
    ({"observed": replace(EXPECTED, pid=124)}, "inconclusive"),
    ({"observed": replace(EXPECTED, package="other")}, "inconclusive"),
    ({"observed": replace(EXPECTED, filter_id=457)}, "inconclusive"),
    ({"observed": replace(EXPECTED, route=replace(ROUTE, port=49161))}, "inconclusive"),
    ({"host_receipt_route": None}, "inconclusive"),
    ({"host_receipt_route": replace(ROUTE, family="ipv6")}, "inconclusive"),
    ({"endpoint_observation_complete": False}, "inconclusive"),
    ({"direct_receipts": None}, "inconclusive"),
    ({"direct_receipts": False}, "inconclusive"),
    ({"direct_receipts": 1, "observed": None}, "direct_receipt_observed"),
])
def test_network_evidence(changes, verdict):
    evidence = dict(observed=EXPECTED, host_receipt_route=ROUTE,
                    direct_receipts=0, endpoint_observation_complete=True)
    assert classify_network(EXPECTED, **(evidence | changes)) == verdict


@pytest.mark.parametrize(("event", "receipt", "verdict"), [
    ({}, {}, "tested_route_blocked"),
    ({"attempt": "old"}, {}, "inconclusive"),
    ({"tick": 19}, {}, "inconclusive"),
    ({"tick": 40}, {}, "inconclusive"),
    ({}, {"attempt": "other"}, "inconclusive"),
    ({}, {"opened_tick": 21}, "inconclusive"),
    ({}, {"closed_tick": 39}, "inconclusive"),
    ({}, {"host_receipt_tick": 21}, "inconclusive"),
    ({}, {"complete": False}, "inconclusive"),
    ({"attempt": "old"}, {"direct_receipts": 1}, "direct_receipt_observed"),
])
def test_attempt_binding(event, receipt, verdict):
    windows = replace(WindowsObservation("current", 30, EXPECTED), **event)
    endpoint = replace(EndpointObservation("current", ROUTE, 10, 15, 45, 0, True), **receipt)
    assert admit_attempt("current", EXPECTED, child_start=20, child_stop=40,
                         windows=windows, endpoint=endpoint) == verdict


@pytest.mark.parametrize(("changed", "verdict"), [
    ({}, "tested_route_blocked_indirect"),
    ({"exclusive_package_verified": False}, "inconclusive"),
    ({"clock_window_verified": False}, "inconclusive"),
    ({"executable": "other.exe"}, "inconclusive"),
    ({"child_start_filetime": 31}, "inconclusive"),
    ({"child_stop_filetime": 30}, "inconclusive"),
    ({"drop": None}, "inconclusive"),
])
def test_indirect_udp(changed, verdict):
    route = replace(ROUTE, protocol="udp")
    expected = replace(EXPECTED, route=route)
    endpoint = EndpointObservation("current", route, 10, 15, 45, 0, True)
    drop = PackageDrop(30, expected.package, "python.exe", expected.filter_id, route)
    args = dict(executable="python.exe", exclusive_package_verified=True, clock_window_verified=True,
                child_start_filetime=20, child_stop_filetime=40, drop=drop, endpoint=endpoint)
    assert admit_indirect_udp("current", expected, **(args | changed)) == verdict
    assert admit_indirect_udp("current", EXPECTED, **args) == "inconclusive"
    assert admit_indirect_udp("current", expected, **(args | {
        "drop": None, "endpoint": replace(endpoint, direct_receipts=1)
    })) == "direct_receipt_observed"


def test_collector_handoff():
    route = replace(ROUTE, protocol="udp")
    expected = replace(EXPECTED, route=route)
    endpoint = EndpointObservation("current", route, 10, 15, 45, 0, True)
    drop = PackageDrop(30, expected.package, "python.exe", expected.filter_id, route)
    snapshot = UdpDropSnapshot("current", True, (replace(drop, filetime=19), drop))

    def verdict(observation, receipts=endpoint):
        return admit_udp_snapshot(
            "current", expected, executable="python.exe", exclusive_package_verified=True,
            clock_window_verified=True, child_start_filetime=20, child_stop_filetime=40,
            snapshot=observation, endpoint=receipts,
        )

    assert verdict(snapshot) == "tested_route_blocked_indirect"
    for invalid in (
        None, replace(snapshot, attempt="old"), replace(snapshot, exhausted=False),
        replace(snapshot, drops=(drop, drop)), replace(snapshot, drops=(drop,) * 65),
    ):
        assert verdict(invalid) == "inconclusive"
    assert verdict(None, replace(endpoint, direct_receipts=1)) == "direct_receipt_observed"
