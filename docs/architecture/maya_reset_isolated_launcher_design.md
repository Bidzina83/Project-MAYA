# Offline Reset Launcher Integration

Design only. Preserve ZIP 3 as the working workflow baseline. The purpose
of the successor is to verify the Windows network boundary for the actual
Hermes process, not to qualify production containment.

## Process Ownership

- The trusted launcher owns approval, the synthetic broker, and reporting.
  Hermes runs as the verified AppContainer child. Reuse the existing
  package-scoped WFP policy, job ownership, and private pipe allowlist.
  Do not put the operator or broker in the child's AppContainer.
- Keep the fixed synthetic document and exact SDK body check. The child
  sends one request over the private channel and waits. The coordinator
  binds approval to the exact body and destination. Approval yields one
  synthetic broker dispatch and returns its answer to that same turn.
  Denial, alteration, or timeout produces no dispatch and no answer.
- The network observation must come from the process that executes the
  Hermes turn, not a sibling probe or another launcher profile. Keep
  the controlled endpoint separate from the synthetic broker receipt
  counter so a broker dispatch cannot be mistaken for direct egress.

## Evidence Contract

### Integration Boundary

The offline demo's `hermes_request()` starts `--hermes-turn` via
`subprocess.Popen`. Do not call that wrapper from the protected child:
the process that runs `hermes_turn_main()` must itself be the verified
AppContainer process owned by the launcher's job. Keep ZIP 3 unchanged.

The integrated candidate needs three trusted inputs: the launcher's
retained child identity and lifetime, the bounded outbound TCP connect
snapshot from `UdpEvidence.CollectResetTcp`, and the separate listener's
host-control receipt and observation window. Do not compare timestamps
from the laptop and VM directly. Bracket listener coverage with host-side
start/stop acknowledgements around the child lifetime; keep WFP event and
process lifetime timestamps in the VM's FILETIME domain.

The one-shot baseline listener is not sufficient for this run: it exits
after the first receipt. The integrated listener must continue observing
the same address and port through confirmed child termination and report
any additional receipts separately from the host control. Absent that
coverage, the network verdict remains inconclusive.

Before accepting a blocked-route result, require an independent host
positive control against the same endpoint and route. Require an observed
Windows block attributable to the retained child, its package, and the
expected filter, plus zero direct receipts at the controlled endpoint.
Record route, protocol and address family; do not generalize beyond them.
An unavailable endpoint, missing or ambiguous attribution, or a timeout
without a Windows block event is inconclusive. Any direct endpoint receipt
attributable to the child fails the tested boundary.

For the workflow, require one receipt and one same-turn answer on approval,
and zero receipts and no answer on denial. Keep these results separate
from the network verdict. Confirm owned jobs have stopped before removing
grants or filters; require independent cleanup checks. No real endpoints,
credentials, business data, Telegram, or journal work.

## Decision

Next step: separately approved source preparation and inert tests for
channel binding, approval, receipt separation, attribution and cleanup.
Assembly and Windows execution require their own review. If the existing
event evidence cannot reliably identify the actual reset child, keep the
network gate open and revisit the design. Apply the reset plan's stop
rule; do not substitute earlier containment-screen results or start
another open-ended diagnostics loop.

## Collector Reuse Check

The existing `UdpEvidence` collector is UDP-loopback-specific. Its drop
matching uses package SID, executable identity, filter and layer, route
fields, and a FILETIME window. It does not return a PID in the admitted
drop record. The screen's child PID binding for socket ownership is not
a PID on the WFP event. Do not populate the Python evidence model's PID
from the expected child or use enumeration time as the drop time.

Before wiring an adapter, review whether a fresh per-attempt package and
filter set, exclusive ownership of the only child launched with that
package, verified executable identity, and a matching route and lifetime
are sufficient for indirect attribution. Keep that attribution distinct
from event-reported PID. If any exclusivity or time check is missing, the
result is inconclusive. The existing UDP collector cannot substantiate
a TCP or non-loopback verdict as written.

Keep event occurrence and process lifetime comparisons in a common clock
domain. Independently bracket the endpoint observation around the child
lifetime; do not coerce a FILETIME into a monotonic tick. Resolve this
evidence contract before connecting the collector to the gate. No live
collector, filter change, network test or build is authorized here.

## Controlled TCP Decision

Supersede UDP loopback as the next milestone. The existing package-scoped
ALE authorization policy can cover TCP connect without a second firewall
policy. The current UDP collector cannot verify it: its admission checks
require UDP and loopback. The Windows event header can provide package,
application, protocol, route and event time, but not a process ID.

Review one isolated IPv4 TCP route to a controlled non-loopback endpoint
on a private test network with no public route. Non-loopback matters:
an AppContainer loopback restriction could otherwise explain the result.
No public endpoint, credentials, TLS claim, firewall exception or policy
change. If that topology is unavailable, stop rather than substitute UDP
or a public host.

Use one integrated candidate. The trusted host proves that the exact
listener accepts a connection. The listener distinguishes that control
from any subsequent accepted connection and observes the full child
lifetime. The actual isolated Hermes process makes one fixed, bounded
connection check, separate from its synthetic broker exchange. Require
an outbound TCP connect-layer drop from the expected filter, package,
executable, route and lifetime. Attribute it indirectly only when the
launcher verifies that exactly one child owned that fresh package during
the window. No invented PID, timestamp conversion by relabeling, or
substitution of a child-reported error for an observed drop.

A direct connection fails the boundary. Missing host control, incomplete
listener observation, a drop from another filter, or ambiguous attribution
is inconclusive. Confirm same-turn approval and denial and verify cleanup
on the same candidate. A pass proves only the tested IPv4 TCP route, not
universal HTTPS isolation. No further standalone classifier milestone.

References: [ALE layers](https://learn.microsoft.com/en-us/windows/win32/fwp/ale-layers)
and [WFP event header](https://learn.microsoft.com/en-us/windows/win32/api/fwpmtypes/ns-fwpmtypes-fwpm_net_event_header3).
