# Governance V2 Gate A - Step 2 Architecture Assessment

## Result And Approval Boundary

2026-10-14: the user approved candidate 1, LPAC plus scoped Windows Filtering
Platform (WFP), and this architecture/test map. Step 2 is closed; Step 3's one
prototype is next under the evaluation budget and stop conditions. Privileged
provisioning requires separate impact disclosure and permission. No containment
has been demonstrated, and Gate A remains open.

The user-created branch `Maya-Governance-Integration-V2` was verified locally and
was clean before assessment. It replaces the suggested evaluation branch name.
No native patch, runtime profile, network exemption, Windows feature, credential,
dependency or installer was changed. Active references:
[evaluation contract](governance_v2_gate_a_evaluation_contract.md),
[restricted execution](restricted_hermes_execution_contract.md) and
[plan revision 2](maya_governance_integration_plan_v2.md).

## Host And Exact Source Evidence

Read-only registry: EditionID `Professional`, DisplayVersion `25H2`, CurrentBuild
`26200`, UBR `9457`. ProductName says `Windows 10 Pro`; do not infer OS version
solely from that label. CIM access was unavailable. Step 3 must record actual OS
API version/capabilities. Elevation and virtualization availability are unverified.

Inspected committed Git objects, not mutable checkout files, in the separate
Hermes clone at `b13e2fd6948a59eeb59fe618914147d97a2ee90a`:

| Native file | Git blob identity | Finding |
| --- | --- | --- |
| `run_agent.py` | `63050980934b2fe6421018b09fda950f708c5609` | Constructor accepts configured base URL, key and api_mode |
| `agent/agent_init.py` | `e7f2ed9eac33dba131e8ff6b1e0d97ffaa99dc10` | Explicit codex_responses is honored; automatic upgrade applies only without override |
| `agent/transports/codex.py` | `1ce449eeaa749e79d2184d7de2381f6a7bd3fc53` | Responses transport exists, with configured base-URL handling |

Use explicit `api_mode="codex_responses"`, intended `gpt-6-luna`, a local
Responses-compatible gateway and a scoped admission token, not an OpenAI key in
Hermes. This is a source-supported configuration, not a routing patch. No API/model
substitution or reasoning disablement. Actual URL selection, SDK parsing and loop
compatibility still need tests. No live-provider call or model availability check
was made; synthetic tests cannot qualify live provider behavior.

Reuse Maya `LocalAPI` identity ingress, `ActionAuthorizationGateway` /
`PolicyAuthorizationGateway`, existing audit and SMB services. The current
`HermesRuntimeAdapter._build_runtime` constructs in-process, not inside isolation.
The non-candidate Local API path permits caller classification; it cannot be used
unchanged for trusted V2 admission. Source inspection does not qualify these
interfaces. Host wrappers must authorize SMB methods before access. Introduce
transport/launcher adapters, not a duplicate policy engine or fake runtime.

## Two Candidates

| Factor | 1. Win32 LPAC + WFP + Maya broker | 2. Windows Sandbox + mediated host exchange |
| --- | --- | --- |
| Isolation | Restricted token and explicit resource grants; shared trusted kernel | Separate kernel, hypervisor isolation |
| Native runtime | Prepared managed Windows Python and unchanged Hermes | Same runtime staged inside guest |
| Persistence | Dedicated private local area with validated grants | State disappears on close; needs limited persistence mapping |
| Network | SID-scoped filters and gateway-only access must be proved | Network toggle alone does not express gateway-only access |
| Integration | Local SDK gateway and bounded service methods | Additional host/guest communication and persistence protocol |
| Provisioning | Native launcher/profile/ACLs; likely elevated filters/exemption setup | Supported edition, virtualization and feature enablement |
| Product fit | Potential managed Inno/local lifecycle path | Useful test environment; less direct persistent unattended product |
| Main uncertainty | Filter arbitration, Python compatibility and ambient grants | Mount/channel exposure and feature/platform constraints |

Microsoft documents LPAC's reduced implicit access and programmatic launch with
security capabilities and all-application-packages opt-out. This supports the
mechanism, not Python/Hermes compatibility.
[Launch documentation](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer).
Unpackaged apps can use AppContainer; ordinary child creation typically inherits
its token. Alternate process creation still requires testing.
[Legacy apps](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-for-legacy-applications-).

Windows Sandbox uses a separate kernel, discards state on close and enables
networking by default. Home is not supported; mapped-folder controls do not supply
Maya authorization. It is not recommended for this one prototype.
[Overview](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/),
[configuration](https://learn.microsoft.com/en-us/windows/security/application-security/application-isolation/windows-sandbox/windows-sandbox-configure-using-wsb-file).

The recommendation is an engineering inference, not measured reliability. No
third candidate is assessed; candidate 2 is not an automatic fallback.

## Recommended Topology

```text
Authenticated Local API -> trusted Maya host -> LPAC launcher/job
                                                  |
                                                  v
                            native AIAgent + private Hermes state
                                      | SDK/tool proposals
                                      v
                          dedicated loopback Maya broker
                         model / document / SMB read methods
                                      |
                         existing local policy and audit
                                      |
                         provider fixture / protected stores

Native final result -> dedicated process IPC -> host validation -> user
```

Hermes and its messages are untrusted proposals. Do not import execution code into
the trusted host. A concrete process-backed AgentRuntime adapter still uses Hermes's
native loop and lifecycle; it is not a replacement agent architecture.

### Files, Processes And IPC

Launch managed Python suspended with LPAC security attributes. Grant prepared
runtime/dependency read/execute access and private Hermes/temp read/write only.
Review system/DLL grants and effective ACLs. No broad All Application Packages
grant, customer-root access or downgrade to normal AppContainer to solve imports.

Inherit only dedicated input/result IPC and private stdout/stderr capture handles;
no host file/process/token/credential handles. Assign a job with kill-on-close,
resource limits and no breakaway before resume. Verify child tokens. Jobs provide
lifecycle control, not filesystem/network containment; indirect creation paths
must be tested.
[Job objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects),
[handle inheritance](https://learn.microsoft.com/en-us/windows/win32/procthread/inheritance).

No UI/clipboard/camera capability or unrestricted host-launch/COM broker. Test
named pipes, RPC and other local services with endpoint ACLs: TCP filters do not
secure non-network IPC. Unavoidable dangerous ambient IPC is a stop condition.

### Network, Identity And Policy

Use one unique evaluation AppContainer SID. WFP IPv4/IPv6 ALE connect and
receive/listen enforcement must deny runtime traffic except TCP to a fixed literal
loopback address and reserved Maya broker port. Deny DNS/UDP, public/LAN access,
other loopback services and arbitrary listeners. Bind package SID and appropriate
user scope, not only python.exe, to cover different child executables.

WFP documents package SID, address, protocol and port conditions at relevant
layers. Correct precedence, capability-policy interaction and loopback handling
remain proof obligations; documentation does not establish a passing filter set.
[Filtering layers](https://learn.microsoft.com/en-us/windows/win32/fwp/filtering-conditions-available-at-each-filtering-layer).

AppContainer may require scoped loopback exemption/capability. This is not port
isolation. Provision only after deny enforcement exists, with explicit consent.
The proposed capability ceiling is `privateNetworkClientServer` plus a
profile-specific loopback exemption; no `internetClient` grant. Whether that
combination permits the fixed broker connection on this build is untested. If
it does not, stop rather than automatically change the capability ceiling.
If minimal grants cannot reach the broker, stop, not unrestricted-network fallback.
Keep durable deny enforcement independent of broker/helper death; revoking allow
must not remove deny. Validate profile/filters/broker/ACLs before resume.
Exact filter weights, sublayer ordering and permitted capability must be verified
in the prototype. Do not alter generic machine firewall defaults.
[Connectivity](https://learn.microsoft.com/en-us/windows/security/operating-system-security/network-security/windows-firewall/troubleshooting-uwp-firewall).

Host binds the broker before launching Hermes. A fresh revocable admission token
maps to host principal, classification, targets, expiry and budgets; it grants
proposals, never blanket ALLOW/provider/admin access. Caller fields/session IDs
cannot supply authority. Authorize every effective model payload; host selects
route. No arbitrary URL forwarding, CONNECT proxy or redirects. Clear inherited
secrets, proxy variables and customer profiles. Regex redaction alone is not policy.

Proposed new broker methods: `/v1/responses`, `/maya/document/read`,
`/maya/memory/search`. They are not existing qualified endpoints. Required policy
and audit succeed before transport/read. Unsupported routes and attempts to lower
classification deny. Local network credentials are bounded admission only.

### Tools, Native Memory And Disclosure

One allowlisted native extension tool proposes document read; an external-memory
adapter proposes SMB retrieval through the broker. Neither directly accesses host
files/DBs. Reuse native registration, not a replacement registry. In-container
plugins/adapters are integration code, not enforcement authorities.

Host buffers/validates final output. Raw native prints, callbacks, progress and
exceptions go to private capture, never launcher console or raw API bodies.
Only approved fixed diagnostics persist outside the sensitive private area. Treat
IPC/result data as hostile; bounded messages, no pickle or host-side execution.

Native conversations/MEMORY.md/USER.md remain sensitive permitted private state,
not trusted business records or authority. No automatic SMB copy. Revoke broker
admission before cancellation cleanup; fresh requests receive fresh authority.

## Boundary And Executable Test Map

All rows are planned, not passing. Entrypoints describe Step 3 harness work, not
new tests already present. Freeze executable names/counts/hashes before launch.
Observe sinks from the trusted host. Retain all approved scenario families.

| ID | Entrypoint and negative variants | Allowed control / observed boundary |
| --- | --- | --- |
| A01 | LocalAPI run -> process adapter -> AIAgent.run_conversation | Approved question, actual broker/read/delivery evidence |
| A02 | Native registered document tool; tampered target/result | Approved tool read and separately gated follow-up inference |
| A03 | Native session/memory tools; foreign root attempt | Private session resume and MEMORY.md/USER.md read/write; no SMB copy |
| A04 | Broker document/memory request; denied target/classification | Approved counterpart; protected-read counter zero on deny |
| A05 | LPAC open/sqlite3/registry reads and writes to document/SMB/policy/audit/credential roots | Private read/write and prepared-runtime read allowed; protected reads denied and bytes unchanged |
| A06 | Traversal, actual link/junction and path-replacement race | Private canonical access works; broker handle/root checks deny before read |
| A07 | Direct SDK, alternate URL and raw socket to controlled external listener | Fixed broker allowed; external listener observes zero denied connections |
| A08 | Proxy, redirect, host alias, IPv6, UDP/DNS variants | Literal broker control works; alternate listeners observe zero access |
| A09 | Native summary/compressor, SDK retry, malformed-response retry and fallback trigger | Each supported gateway request gated; unsupported paths deny before transport |
| A10 | Child Python/cmd, breakaway/indirect process probes | Child private action works; token/job evidence and no escape |
| A11 | Explicitly loaded native test plugin/tool calls SDK/file/process probes | Approved broker tool works; no new capabilities acquired |
| A12 | Unauthorized TCP, named pipe/RPC and broker route/verb probes | Dedicated IPC and approved broker method work; other services deny |
| A13 | Missing/wrong/stale/replayed/revoked token and altered authority/target/method/classification | Fresh host-bound admission works; negatives have no protected effect |
| A14 | Runtime business-write/policy proposals with body/session authority | Approved read works; no authoritative mutation |
| A15 | Native result/callback/stream contains denied marker or malformed content | Valid buffered result delivered once; no prohibited public content |
| A16 | Secret markers in provider header/body, native stderr/progress/error/result | Fixed safe diagnostic control; scan all prohibited public/persistent sinks |
| A17 | Missing profile/filter, broken gateway/policy/required audit | Intact control works; no unsafe launch or subsequent protected effect |
| A18 | Cancel/timeout then late broker/tool/result callback; borrow fresh token scope | Timely control works; revoked effect/delivery stays zero |
| A19 | Kill runtime/host broker, restart and replay old admission | Fresh restricted start works; old authority denied, no ordinary fallback |
| A20 | Native construction/session/memory/tool/Responses controls and hash verification | Unmodified pin and prepared dependencies; no replacement runtime or required skips |

Use controlled real sockets as well as synthetic SDK responses; MockTransport
alone cannot establish containment. Failed setup is not a passing denial. Record
paired allowed controls and actual protected sink evidence. Missing privileges or
dependencies block tests, not waive them. Private approved conversation retention
is not itself prohibited disclosure; public diagnostics remain protected.

## Dependencies And Product Consequences

Prepared pinned Python/Hermes artifacts and existing Maya code; no Docker, VM
image or third-party isolation framework for candidate 1. Required new components
are a small Maya-owned native launcher and trusted WFP provisioning helper, neither
a general privileged execution service. OS API use is not bundling a third-party
runtime; Python artifacts still need license/provenance review. No final shipping
license conclusion follows this assessment.

Inno can later deploy helpers and disclose profile/ACL/filter provisioning with
required consent/elevation. No installer built now. Clean setup/uninstall/exemption
cleanup/update/rollback remain Gate E. No Windows Home or additional-platform claim.

## Fixed Risks And Decision

Five explicit obligations: LPAC dependency compatibility, gateway-only networking,
no ambient file/IPC escape, native memory/tool/Responses functionality, and trusted
failure/disclosure handling. These are within the matrix, not new unbounded WPs.

Stop if minimal grants/filter policy cannot work, dangerous access remains, native
functionality breaks, or a Hermes patch/pin change is needed. No downgrade, patched
fallback or candidate 2 implementation without a decision. Any correction uses
the one specifically approved correction budget. No delivery estimate is claimed.

User decision on 2026-10-14: candidate 1 topology and test map approved for Step 3's
one prototype, retaining all proof obligations/stops. Privileged provisioning requires separate
impact disclosure and permission before execution. Result acceptance is not Gate A
acceptance. Baseline sources, historical tests, wheels and production guards stay.
