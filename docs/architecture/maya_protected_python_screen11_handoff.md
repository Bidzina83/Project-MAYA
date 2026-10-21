# Maya Protected Python Screen 11

## Status

UDP evidence successor to frozen Screen 10, prepared with user approval.
No native execution is included in preparation. Obtain separate VM-run approval
and fresh in-product informed consent. Use RDP on the existing customer-like
Windows 11 Pro 26300.9711 VM; do not preconfigure its security to help this pass.
Do not run the product on the development workstation.

## What Changes

Only the four UDP case definitions change: C05.4udp/6udp.connect becomes .send,
and .bind becomes .receive. The total remains 47 child cases plus cleanup.
Historical reports/contracts retain their original names and outcomes.
TCP and all non-network cases retain their existing requirements.

The child binds a loopback UDP socket, records the actual local/remote ports,
actual send count or received byte count and bind error. A bind failure alone
does not exercise packet authorization and stays inconclusive. A successful send
is not delivery proof. Any received packet, even empty or unexpected, is an effect.

For inbound traffic the child writes one bounded nonce/port request in its own
state. The existing host UDP endpoint checks the socket's loopback address,
port and child PID through a bounded owner-table query before sending one fixed
synthetic challenge. No child-selected address, arbitrary payload or connector
is accepted. The check/send sequence is not an atomic endpoint ownership proof;
port-reuse races remain unqualified. Bidirectional host controls run before and
after the child. No additional listener or independent supervisor is introduced.

Maya reads existing WFP collection state. It never enables collection or changes
event keywords, auditing, registry settings or filter definitions. If unavailable,
setup blocks before child launch and follows existing product cleanup.
The operator reported netevents=on; Maya must check this itself each attempt.

The host retains a verified numeric filter-ID to GUID/layer/package map. After
confirmed child stop, while filters are still present, it reads a retained-event
snapshot using FwpmNetEventEnum5: at most four pages of 256 events and 64 relevant
matches. It persists only attributable records, not unrelated machine traffic.
It validates event type, presence flags, UDP protocol, attempt time, both loopback
addresses, ports, package SID, exact application-ID bytes, filter ID, numeric
layer and direction. Event headers contain no PID; child identity is separate.

A UDP denial requires a matching Maya-owned drop plus the case's usable operation
details and host controls/postconditions. Inbound also requires a host-recorded
owner-checked send to that socket. Missing matches, unknown errors, partial
enumeration, limit exhaustion, unsupported APIs or ambiguous evidence stay
inconclusive. Silence never passes. Native error 10013 alone does not pass a UDP
case. The snapshot cannot prove complete event history or account for Windows'
retention losses; a positive match supports only that bounded observed denial,
never all UDP paths or whole-machine containment.

## Unchanged Protections

Ordinary AppContainer, zero capabilities, reduced same-user token, six scoped WFP
denies, job/child policy, inherited handles, launch arguments, file permissions,
30-second child deadline, 22-second internal budget, 4096-byte stdout and
65536-byte detailed-report limits remain unchanged. The setup host is elevated;
the child must still pass its independent restricted-token admission checks.
No unrestricted fallback, extra capability, loopback exemption or manual grant.

Normal cleanup/recovery remains product-owned. The known journal-less recovery
gap is not repaired. No crash/restart experiment is approved. Stop after a failed
result; do not retry, force-close, recover or change Windows settings automatically.
Retain the report and inspect exact resources separately. Screen 10's read-only
checks found no matching processes, links, package-SID file grants, filters,
sublayer or listener ports; its state root had Medium integrity. Profile and
named-mapping removal remain product-reported, not independently checked.

All qualification flags stay false. Hermes, customer stores, gateway mediation,
models, connectors, Metabase, other network routes, races and crash recovery are
not qualified by this synthetic screen. Even complete observations require
independent cleanup review and cannot activate production.

## Source References

- [Retained-event enumeration](https://learn.microsoft.com/en-us/windows/win32/api/fwpmu/nf-fwpmu-fwpmneteventenum5): only events logged before enumeration creation; free returned pages.
- [Event header and presence flags](https://learn.microsoft.com/en-us/windows/win32/api/fwpmtypes/ns-fwpmtypes-fwpm_net_event_header3).
- [Drop direction and filter/layer identity](https://learn.microsoft.com/en-us/windows/win32/api/fwpmtypes/ns-fwpmtypes-fwpm_net_event_classify_drop2).
- Native layouts are checked at compile time against the installed Microsoft
  Windows SDK 10.0.26100.0 headers; no native diagnostic runs for that check.
