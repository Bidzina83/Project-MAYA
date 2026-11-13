"""Evidence admission for the offline reset demo; performs no network I/O."""

from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Network


@dataclass(frozen=True)
class Route:
    protocol: str
    family: str
    address: str
    port: int


@dataclass(frozen=True)
class Block:
    pid: int
    package: str
    filter_id: int
    route: Route


@dataclass(frozen=True)
class WindowsObservation:
    attempt: str
    tick: int
    block: Block


@dataclass(frozen=True)
class EndpointObservation:
    attempt: str
    route: Route
    host_receipt_tick: int
    opened_tick: int
    closed_tick: int
    direct_receipts: int
    complete: bool


@dataclass(frozen=True)
class PackageDrop:
    filetime: int
    package: str
    executable: str
    filter_id: int
    route: Route


@dataclass(frozen=True)
class UdpDropSnapshot:
    """Records from one trusted Windows enumeration, not from the child."""

    attempt: str
    exhausted: bool
    drops: tuple[PackageDrop, ...]


_PRIVATE_TCP_NETWORKS = tuple(map(IPv4Network, (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "100.64.0.0/10",
)))


@dataclass(frozen=True)
class TcpDropSnapshot:
    """Bounded outbound connect-layer records from the trusted collector."""

    attempt: str
    exhausted: bool
    drops: tuple[PackageDrop, ...]


@dataclass(frozen=True)
class SecurityConnectionBlock:
    """Normalized event 5157 data from the trusted Windows Security log."""

    filetime: int
    pid: int
    executable: str
    filter_id: int
    route: Route
    outbound: bool


def corroborate_tcp_block(
    verdict: str,
    expected: Block,
    *,
    executable: str,
    child_start_filetime: int,
    child_stop_filetime: int,
    events: tuple[SecurityConnectionBlock, ...],
) -> bool:
    """Report optional PID corroboration without changing the network verdict."""
    if (verdict != "tested_route_blocked_indirect" or expected.route.protocol != "tcp"
            or expected.pid <= 0 or expected.filter_id <= 0 or not executable
            or not 0 < child_start_filetime < child_stop_filetime):
        return False
    return any(
        event.outbound is True
        and type(event.pid) is int and event.pid == expected.pid
        and event.executable == executable
        and event.filter_id == expected.filter_id
        and event.route == expected.route
        and type(event.filetime) is int
        and child_start_filetime <= event.filetime < child_stop_filetime
        for event in events
    )


def tcp_listener_receipts(attempt: str, records: list[dict]) -> int | None:
    """Validate a complete transcript from the trusted listener."""
    if not attempt or not 2 <= len(records) <= 66:
        return None
    common = {"schema": "maya.reset.tcp.listener.v1", "attempt": attempt}
    if records[0] != {**common, "event": "ready"}:
        return None
    for ordinal, record in enumerate(records[1:-1], 1):
        if (not isinstance(record, dict) or type(record.get("ordinal")) is not int
                or record != {**common, "event": "receipt", "ordinal": ordinal}):
            return None
    count = len(records) - 2
    last = records[-1]
    if (not isinstance(last, dict) or type(last.get("peer_receipts")) is not int
            or last != {**common, "event": "window_closed", "peer_receipts": count}):
        return None
    return count


def admit_tcp_listener_transcript(
    attempt: str,
    route: Route,
    records: list[dict],
    *,
    host_receipt_filetime: int,
    observation_open_filetime: int,
    observation_close_filetime: int,
    host_control_is_first_verified: bool,
    coverage_verified: bool,
) -> EndpointObservation | None:
    """Convert trusted coordinator evidence, not remote clock samples."""
    count = tcp_listener_receipts(attempt, records)
    if (count is None or count < 1 or host_control_is_first_verified is not True
            or coverage_verified is not True):
        return None
    times = (host_receipt_filetime, observation_open_filetime,
             observation_close_filetime)
    if any(type(value) is not int or value <= 0 for value in times):
        return None
    if not host_receipt_filetime <= observation_open_filetime < observation_close_filetime:
        return None
    return EndpointObservation(attempt, route, *times, count - 1, True)


def admit_tcp_snapshot(
    attempt: str,
    expected: Block,
    *,
    executable: str,
    exclusive_package_verified: bool,
    clock_window_verified: bool,
    child_start_filetime: int,
    child_stop_filetime: int,
    snapshot: TcpDropSnapshot | None,
    endpoint: EndpointObservation | None,
) -> str:
    """Admit a single private IPv4 TCP drop, without inventing an event PID."""
    route = expected.route
    if (not attempt or route.protocol != "tcp" or route.family != "ipv4"
            or type(route.port) is not int or not 0 < route.port <= 65535
            or endpoint is None or endpoint.attempt != attempt or endpoint.route != route):
        return "inconclusive"
    try:
        address = IPv4Address(route.address)
    except ValueError:
        return "inconclusive"
    if not any(address in network for network in _PRIVATE_TCP_NETWORKS):
        return "inconclusive"
    if type(endpoint.direct_receipts) is int and endpoint.direct_receipts > 0:
        return "direct_receipt_observed"
    if (endpoint.complete is not True or type(endpoint.direct_receipts) is not int
            or endpoint.direct_receipts != 0 or exclusive_package_verified is not True
            or clock_window_verified is not True or not executable or not expected.package
            or expected.pid <= 0 or expected.filter_id <= 0 or snapshot is None
            or snapshot.attempt != attempt or snapshot.exhausted is not True
            or len(snapshot.drops) > 64):
        return "inconclusive"
    times = (endpoint.host_receipt_tick, endpoint.opened_tick, child_start_filetime,
             child_stop_filetime, endpoint.closed_tick)
    if any(type(value) is not int or value <= 0 for value in times):
        return "inconclusive"
    host, opened, started, stopped, closed = times
    if not host <= opened <= started < stopped <= closed:
        return "inconclusive"
    matches = sum(drop.package == expected.package and drop.executable == executable
                  and drop.filter_id == expected.filter_id and drop.route == route
                  and type(drop.filetime) is int and started <= drop.filetime < stopped
                  for drop in snapshot.drops)
    return "tested_route_blocked_indirect" if matches == 1 else "inconclusive"


def admit_udp_snapshot(
    attempt: str,
    expected: Block,
    *,
    executable: str,
    exclusive_package_verified: bool,
    clock_window_verified: bool,
    child_start_filetime: int,
    child_stop_filetime: int,
    snapshot: UdpDropSnapshot | None,
    endpoint: EndpointObservation | None,
) -> str:
    """Join the endpoint report to eligible Windows drops from this attempt."""
    matching = ()
    if (snapshot is not None and snapshot.attempt == attempt
            and snapshot.exhausted is True and len(snapshot.drops) <= 64):
        matching = tuple(drop for drop in snapshot.drops
                         if drop.package == expected.package
                         and drop.executable == executable
                         and drop.filter_id == expected.filter_id
                         and drop.route == expected.route
                         and type(drop.filetime) is int
                         and child_start_filetime <= drop.filetime < child_stop_filetime)
    return admit_indirect_udp(
        attempt, expected, executable=executable,
        exclusive_package_verified=exclusive_package_verified,
        clock_window_verified=clock_window_verified,
        child_start_filetime=child_start_filetime,
        child_stop_filetime=child_stop_filetime,
        drop=matching[0] if len(matching) == 1 else None, endpoint=endpoint,
    )


def admit_indirect_udp(
    attempt: str,
    expected: Block,
    *,
    executable: str,
    exclusive_package_verified: bool,
    clock_window_verified: bool,
    child_start_filetime: int,
    child_stop_filetime: int,
    drop: PackageDrop | None,
    endpoint: EndpointObservation | None,
) -> str:
    """Use only trusted records; endpoint ticks must be verified FILETIMEs here."""
    route = expected.route
    if (not attempt or route.protocol != "udp"
            or (route.family, route.address) not in {("ipv4", "127.0.0.1"), ("ipv6", "::1")}
            or not 0 < route.port <= 65535
            or endpoint is None or endpoint.attempt != attempt or endpoint.route != route):
        return "inconclusive"
    if type(endpoint.direct_receipts) is int and endpoint.direct_receipts > 0:
        return "direct_receipt_observed"
    if (exclusive_package_verified is not True or clock_window_verified is not True
            or not executable or not expected.package or expected.pid <= 0 or expected.filter_id <= 0
            or drop is None or drop.package != expected.package or drop.executable != executable
            or drop.filter_id != expected.filter_id or drop.route != route
            or endpoint.complete is not True or type(endpoint.direct_receipts) is not int
            or endpoint.direct_receipts != 0):
        return "inconclusive"
    times = (endpoint.host_receipt_tick, endpoint.opened_tick, child_start_filetime,
             drop.filetime, child_stop_filetime, endpoint.closed_tick)
    if any(type(value) is not int or value <= 0 for value in times):
        return "inconclusive"
    host, opened, started, blocked, stopped, closed = times
    if host <= opened <= started <= blocked < stopped <= closed:
        return "tested_route_blocked_indirect"
    return "inconclusive"


def admit_attempt(
    attempt: str,
    expected: Block,
    *,
    child_start: int,
    child_stop: int,
    windows: WindowsObservation | None,
    endpoint: EndpointObservation | None,
) -> str:
    """Join trusted records in a shared monotonic clock domain, not child output."""
    if (not attempt or endpoint is None or endpoint.attempt != attempt
            or endpoint.route != expected.route):
        return "inconclusive"
    if type(endpoint.direct_receipts) is int and endpoint.direct_receipts > 0:
        return "direct_receipt_observed"
    ticks = (endpoint.host_receipt_tick, endpoint.opened_tick, child_start,
             child_stop, endpoint.closed_tick)
    if (any(type(tick) is not int or tick < 0 for tick in ticks)
            or not ticks[0] <= ticks[1] <= child_start < child_stop <= ticks[-1]):
        return "inconclusive"
    observed = None
    if (windows is not None and windows.attempt == attempt
            and type(windows.tick) is int and child_start <= windows.tick < child_stop):
        observed = windows.block
    return classify_network(
        expected, observed, host_receipt_route=endpoint.route,
        direct_receipts=endpoint.direct_receipts, endpoint_observation_complete=endpoint.complete,
    )


def classify_network(
    expected: Block,
    observed: Block | None,
    *,
    host_receipt_route: Route | None,
    direct_receipts: int | None,
    endpoint_observation_complete: bool,
) -> str:
    """Inputs must come from trusted collectors scoped to one attempt."""
    if type(direct_receipts) is int and direct_receipts > 0:
        return "direct_receipt_observed"
    if (
        endpoint_observation_complete is True
        and type(direct_receipts) is int
        and direct_receipts == 0
        and host_receipt_route == expected.route
        and observed == expected
        and expected.pid > 0
        and expected.filter_id > 0
        and expected.package
    ):
        return "tested_route_blocked"
    return "inconclusive"
