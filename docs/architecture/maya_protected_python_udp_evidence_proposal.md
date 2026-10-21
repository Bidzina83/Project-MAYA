# Protected Python UDP Evidence Proposal

## Scope And Approval

Prepared after the operator's Screen 10 result on 2026-10-21. Approval covers
this proposal and read-only cleanup review only. No successor implementation,
native run, new tool, audit setting, tracing session or security change follows.
Screen 10's four inconclusive UDP rows and blocked result remain immutable.

## What The Current Screen Establishes

Screen 10 reports successful Python startup, verified token/filter readbacks,
natural exit zero, complete output capture and no unauthorized effect observed
by its controlled listeners. Cleanup is product-reported, not independently
verified. These observations do not establish complete containment.

The UDP send probe discards the send return count; its reported bytes=0 is a
placeholder, not measured delivery. The UDP bind probe does not exercise inbound
receipt. Receiver silence alone cannot distinguish enforcement from other causes.

## Correct Effect-Level Contract

Windows authorizes the first outbound UDP packet at ALE_AUTH_CONNECT and the
first inbound UDP packet from a unique remote tuple at ALE_AUTH_RECV_ACCEPT.
ALE_AUTH_LISTEN applies to TCP listen; bind belongs to RESOURCE_ASSIGNMENT,
which is not one of Maya's existing six filter layers. Consequently successful
UDP bind is not by itself failure of those filters. Do not add a bind-denial
filter merely to satisfy the old probe. See Microsoft's
[ALE layer definitions](https://learn.microsoft.com/en-us/windows/win32/fwp/ale-layers).

A separately reviewed successor must distinguish:

- Local socket allocation/bind: a precondition observation, not a network escape.
- Outbound IPv4 and IPv6: attempted nonce-bearing packet, actual API return/count
  or error, receiver controls and receipt, plus attributable denial evidence.
- Inbound IPv4 and IPv6: a separate controlled transmission/receive exercise;
  successful bind or outbound silence does not qualify inbound protection.

A successful send call does not establish delivery. Capture its real return
count without treating it as receiver evidence. See Microsoft's
[sendto contract](https://learn.microsoft.com/en-us/windows/win32/api/winsock2/nf-winsock2-sendto).

## Candidate Denial Evidence

First inspect existing event-collection state, without changing it. Windows
provides read-only WFP options/state/event views through
[netsh wfp show](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-wfp).
No set-options, capture-start, audit-policy or registry command is authorized.
Absence of retained historical events does not prove a drop or justify a retry.

If already available and separately approved for implementation, bounded
in-product event collection could correlate protocol 17, exact package SID,
application identity, address/port tuple and attempt time with a classify drop.
Retain the numeric filter ID returned during creation, mapped to its verified
GUID, layer and package SID while the rules are live. Screen 10 does not retain
that numeric mapping; a post-cleanup snapshot cannot reconstruct it reliably.

Check presence flags before reading event fields. The event header has no PID
field: child PID/lifetime is separate verified context, not invented event data.
See [event header](https://learn.microsoft.com/en-us/windows/win32/api/fwpmtypes/ns-fwpmtypes-fwpm_net_event_header3)
and [classify-drop fields](https://learn.microsoft.com/en-us/windows/win32/api/fwpmtypes/ns-fwpmtypes-fwpm_net_event_classify_drop2).
Subscription support and permissions must be established before selecting an
API version; see [subscription requirements](https://learn.microsoft.com/en-us/windows/win32/api/fwpmu/nf-fwpmu-fwpmneteventsubscribe0).

Missing identity fields, uncertain attribution, lost events, incomplete capture
or unavailable collection remains inconclusive. A drop by another Windows rule
is not proof that Maya's own filters enforced the boundary. Host positive
controls do not authorize an AppContainer exception or an unrestricted launch.

## Decision Gate

Before implementation, review exact cases, event support, bounded buffers and
loss reporting, inbound design, verdict predicates and any baseline impact.
Preserve zero capabilities, six existing scoped filters, reduced token, job and
child policy, launch arguments, output limits and deadlines. No global collection
enablement, loopback exemption, weaker permission or extra supervisor is implied.
Unavailable evidence requires a decision, not automatic OS conditioning.

Only then seek separate preparation approval and later artifact/run approval
with product consent. This proposal does not qualify Hermes, protected state,
connectors, Metabase, Gate A, containment or production activation.

## Subsequent Preparation Approval

The operator reports netevents=on without changing the existing VM setting.
The user subsequently approved bounded UDP implementation and separate package
preparation. Screen 11's selected retained-event design and exact case changes
are in `maya_protected_python_screen11_handoff.md`. No subscription, global
event setting, test supervisor or native run is included. Positive attributable
drops support only bounded observed denials; retained-event enumeration cannot
establish loss-free history. Missing evidence remains inconclusive.
