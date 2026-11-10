// Product-owned startup candidate. No Hermes execution or containment acceptance.
#if HERMES_JOURNAL_ACCESS && (!HERMES_BRIDGE || !HERMES_CONSTRUCTION || !HERMES_IMPORT || HERMES_MODEL || HERMES_MODEL_FINAL || HERMES_MODEL_ALLOWLIST || HERMES_MODEL_OVERSIZED || HERMES_MODEL_VALIDATION || HERMES_MODEL_MALFORMED || HERMES_MODEL_OUTPUT_DENY || HERMES_MODEL_DENY || HERMES_MODEL_RECREATE || HERMES_MODEL_BUDGET || HERMES_MODEL_REPLAY || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT || HERMES_STATE || HERMES_MEMORY || MAYA_FINAL_OUTPUT_INERT_FIXTURE || MAYA_JOURNAL_NATIVE_BASELINE || MAYA_JOURNAL_TOKEN_ACCESS_FIXTURE || MAYA_JOURNAL_TOKEN_ACCESS_NATIVE_FIXTURE)
#error HERMES_JOURNAL_ACCESS requires the private bridge topology and excludes other cases and fixture profiles.
#endif
#if HERMES_MODEL_FINAL && (HERMES_MODEL_ALLOWLIST || HERMES_MODEL_OVERSIZED || !HERMES_MODEL_VALIDATION || HERMES_MODEL_MALFORMED || HERMES_MODEL_OUTPUT_DENY || HERMES_MODEL_DENY || HERMES_MODEL_RECREATE || HERMES_MODEL_BUDGET || HERMES_MODEL_REPLAY || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_FINAL requires VALIDATION and excludes all other fixed cases.
#endif
#if HERMES_MODEL_ALLOWLIST && (HERMES_MODEL_OVERSIZED || !HERMES_MODEL_VALIDATION || HERMES_MODEL_MALFORMED || HERMES_MODEL_OUTPUT_DENY || HERMES_MODEL_DENY || HERMES_MODEL_RECREATE || HERMES_MODEL_BUDGET || HERMES_MODEL_REPLAY || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_ALLOWLIST requires VALIDATION and excludes all other fixed cases.
#endif
#if HERMES_MODEL_OVERSIZED && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_MALFORMED || HERMES_MODEL_OUTPUT_DENY || HERMES_MODEL_DENY || HERMES_MODEL_RECREATE || HERMES_MODEL_BUDGET || HERMES_MODEL_REPLAY || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_OVERSIZED requires VALIDATION and excludes all other fixed cases.
#endif
#if HERMES_MODEL_MALFORMED && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_OUTPUT_DENY || HERMES_MODEL_DENY || HERMES_MODEL_RECREATE || HERMES_MODEL_BUDGET || HERMES_MODEL_REPLAY || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_MALFORMED requires VALIDATION and excludes all other fixed cases.
#endif
#if HERMES_MODEL_OUTPUT_DENY && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_DENY || HERMES_MODEL_RECREATE || HERMES_MODEL_BUDGET || HERMES_MODEL_REPLAY || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_OUTPUT_DENY requires VALIDATION and excludes all other fixed model cases.
#endif
#if HERMES_MODEL_RECREATE && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_BUDGET || HERMES_MODEL_REPLAY || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_RECREATE requires VALIDATION and excludes all other fixed model cases.
#endif
#if HERMES_MODEL_BUDGET && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_REPLAY || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_BUDGET requires VALIDATION and excludes all other fixed model cases.
#endif
#if HERMES_MODEL_REPLAY && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_REVOKE || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_REPLAY requires VALIDATION and excludes REVOKE/EXPIRY/BODY/ROUTE/ATTEMPT.
#endif
#if HERMES_MODEL_REVOKE && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_EXPIRY || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_REVOKE requires VALIDATION and excludes EXPIRY/BODY/ROUTE/ATTEMPT.
#endif
#if HERMES_MODEL_EXPIRY && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_BODY || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_EXPIRY requires VALIDATION and excludes BODY/ROUTE/ATTEMPT.
#endif
#if HERMES_MODEL_BODY && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_ROUTE || HERMES_MODEL_ATTEMPT)
#error HERMES_MODEL_BODY requires VALIDATION and excludes ROUTE/ATTEMPT.
#endif
#if HERMES_MODEL_ATTEMPT && (!HERMES_MODEL_VALIDATION || HERMES_MODEL_ROUTE)
#error HERMES_MODEL_ATTEMPT requires HERMES_MODEL_VALIDATION and excludes HERMES_MODEL_ROUTE.
#endif
#if HERMES_MODEL_ROUTE && !HERMES_MODEL_VALIDATION
#error HERMES_MODEL_ROUTE requires HERMES_MODEL_VALIDATION.
#endif
#if HERMES_MODEL_VALIDATION && (!HERMES_MODEL || HERMES_MODEL_DENY)
#error HERMES_MODEL_VALIDATION requires HERMES_MODEL and excludes HERMES_MODEL_DENY.
#endif
#if HERMES_MODEL_DENY && !HERMES_MODEL
#error HERMES_MODEL_DENY requires HERMES_MODEL.
#endif
#if HERMES_MODEL && !HERMES_BRIDGE
#error HERMES_MODEL requires the private HERMES_BRIDGE topology.
#endif
#if HERMES_BRIDGE && (!HERMES_CONSTRUCTION || !HERMES_IMPORT || HERMES_STATE || HERMES_MEMORY)
#error HERMES_BRIDGE requires CONSTRUCTION/IMPORT and excludes STATE/MEMORY.
#endif
#if HERMES_MEMORY && (!HERMES_CONSTRUCTION || HERMES_STATE)
#error HERMES_MEMORY requires HERMES_CONSTRUCTION and excludes HERMES_STATE.
#endif
#if HERMES_STATE && !HERMES_CONSTRUCTION
#error HERMES_STATE requires the HERMES_CONSTRUCTION profile.
#endif
#if HERMES_CONSTRUCTION && !HERMES_IMPORT
#error HERMES_CONSTRUCTION requires the HERMES_IMPORT payload and no-fixture profile.
#endif
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Security.Principal;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;

[assembly: AssemblyTitle("Maya protected Python startup candidate")]
[assembly: AssemblyVersion("0.1.0.0")]
#if HERMES_JOURNAL_ACCESS
[assembly: AssemblyFileVersion("0.2.2.1")]
[assembly: AssemblyInformationalVersion("0.2.2-journal-access.1")]
#elif HERMES_MODEL_FINAL
[assembly: AssemblyFileVersion("0.2.1.21")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-final.3")]
#elif HERMES_MODEL_ALLOWLIST
[assembly: AssemblyFileVersion("0.2.1.18")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-allowlist.1")]
#elif HERMES_MODEL_OVERSIZED
[assembly: AssemblyFileVersion("0.2.1.17")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-oversized.1")]
#elif HERMES_MODEL_MALFORMED
[assembly: AssemblyFileVersion("0.2.1.16")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-malformed.1")]
#elif HERMES_MODEL_OUTPUT_DENY
[assembly: AssemblyFileVersion("0.2.1.15")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-output-denial.1")]
#elif HERMES_MODEL_RECREATE
[assembly: AssemblyFileVersion("0.2.1.14")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-recreate.1")]
#elif HERMES_MODEL_BUDGET
[assembly: AssemblyFileVersion("0.2.1.13")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-budget.3")]
#elif HERMES_MODEL_REPLAY
[assembly: AssemblyFileVersion("0.2.1.10")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-replay.1")]
#elif HERMES_MODEL_REVOKE
[assembly: AssemblyFileVersion("0.2.1.9")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-revocation.1")]
#elif HERMES_MODEL_EXPIRY
[assembly: AssemblyFileVersion("0.2.1.8")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-expiry.1")]
#elif HERMES_MODEL_BODY
[assembly: AssemblyFileVersion("0.2.1.7")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-body.1")]
#elif HERMES_MODEL_ATTEMPT
[assembly: AssemblyFileVersion("0.2.1.6")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-attempt.1")]
#elif HERMES_MODEL_ROUTE
[assembly: AssemblyFileVersion("0.2.1.5")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-route.1")]
#elif HERMES_MODEL_VALIDATION
[assembly: AssemblyFileVersion("0.2.1.4")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-validation.2")]
#elif HERMES_MODEL_DENY
[assembly: AssemblyFileVersion("0.2.1.2")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-denial.1")]
#elif HERMES_MODEL
[assembly: AssemblyFileVersion("0.2.1.1")]
[assembly: AssemblyInformationalVersion("0.2.1-offline-model.1")]
#elif HERMES_BRIDGE
[assembly: AssemblyFileVersion("0.2.0.2")]
[assembly: AssemblyInformationalVersion("0.2.0-bridge-document.2")]
#elif HERMES_MEMORY
[assembly: AssemblyFileVersion("0.1.4.1")]
[assembly: AssemblyInformationalVersion("0.1.4-hermes-memory.1")]
#elif HERMES_STATE
[assembly: AssemblyFileVersion("0.1.3.1")]
[assembly: AssemblyInformationalVersion("0.1.3-hermes-state.1")]
#elif HERMES_CONSTRUCTION
[assembly: AssemblyFileVersion("0.1.2.2")]
[assembly: AssemblyInformationalVersion("0.1.2-hermes-construction.2")]
#elif HERMES_IMPORT
[assembly: AssemblyFileVersion("0.1.1.1")]
[assembly: AssemblyInformationalVersion("0.1.1-hermes-import.1")]
#else
[assembly: AssemblyFileVersion("0.1.0.11")]
[assembly: AssemblyInformationalVersion("0.1.0-screen.11")]
#endif

namespace ProjectMaya.WindowsRuntime
{
    internal static class ProtectedPython
    {
#if HERMES_JOURNAL_ACCESS
        internal const string Version = "0.2.2-journal-access.1";
        internal const string Scope = "offline-journal-access-matrix-v1";
        internal const string Consent =
            "Maya journal access diagnostic " + Version + "\r\n\r\n" +
            "One offline test with synthetic files. The reduced worker and AppContainer child test access " +
            "to a journal and its directory without modifying either. No Hermes conversation, inference, credentials, " +
            "network traffic or publication. Synthetic evidence remains for independent cleanup checks. " +
            "This does not qualify containment or production use.";
#elif HERMES_MODEL_FINAL
        internal const string Version = "0.2.1-offline-final.3";
        internal const string Scope = "offline-hermes-final-text-rejection-v1";
        internal const string Consent =
            "Maya M08 fixed final-text diagnostic " + Version + "\r\n\r\n" +
            "Unsigned development candidate. One real pinned Hermes synthetic conversation, no inference, credentials or customer data. " +
            "A valid response is delivered once to Hermes. After genuine final text and report pass the original launcher checks, " +
            "the trusted coordinator changes one copied canary digit. The original worker text check must reject before operator authorization. " +
            "Both policy rules and original guards remain; no final text is published. This is not an operator-only policy denial or hostile-child bypass proof. " +
            "One dispatch, one runtime delivery, zero operator effects, two gateway calls, exactly five audit records, original uncertainty true, " +
            "positive native conversation/SDK closure and natural exits required. Generic failure never passes.\r\n\r\n" +
            "Product copies embedded Python3.13.14 and pinned dependencies to a fresh private ProgramData attempt. Same AppContainer, " +
            "zero capabilities, reduced tokens, one-process jobs, child-process block and six scoped WFP denies. Shared All Application Packages " +
            "remains a limitation; trusted medium worker is outside child containment. No networking, listener, account, service, registry change " +
            "or loopback exception. Protected host files retained for SYSTEM, Administrators and this operator. No manual OS setup. " +
            "TTL2000ms, ready/RPC/partial5000/2000/1000ms, child22/30s, frame8192, channel/audit128KiB, request/response/stderr4KiB, " +
            "report64KiB, output1024-byte bounds unchanged. No new grant or deadline extension. Hash/count reports only. " +
            "Bounded original guard diagnostics preserve clock calls and authorization. Wrong-stage failures remain blocked. " +
            "Separate matching-artifact ONE-run approval and fresh consent required. No retry/fallback/recovery, inference or later cases. " +
            "Independent cleanup required; all qualification flags false and Gate A open.";
#elif HERMES_MODEL_ALLOWLIST
        internal const string Version = "0.2.1-offline-allowlist.1";
        internal const string Scope = "offline-hermes-response-allowlist-rejection-v1";
        internal const string Consent =
            "Maya M07c allowlist-response candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. Real pinned Hermes sends one fixed synthetic request, not inference. " +
            "No credentials, customer content or charge. Both policy rules remain. A fixed construction-time synthetic " +
            "provider changes one fixture content byte; the original exact-byte guard must reject it after JSON decoding. " +
            "No model response or final text is delivered; UI stays blank. A denial control is not model output. " +
            "Original dispatch uncertainty remains true. One egress gateway decision, one attempted dispatch, zero releases, " +
            "exactly two audit records and natural child/worker exit are required. Generic failure never passes. " +
            "Child observations remain untrusted; this is not hostile-child bypass qualification.\r\n\r\n" +
            "Setup copies embedded Python3.13.14 and pinned Hermes/dependencies to a fresh private ProgramData attempt. " +
            "Same AppContainer, zero capabilities, reduced tokens, one-process jobs, child-process block and six " +
            "scoped WFP network denies. Shared All Application Packages remains a limitation. Trusted medium worker " +
            "is outside child containment and implements no networking. Protected host files are retained for " +
            "SYSTEM, Administrators and this operator. No listener, account, service, registry change or loopback " +
            "exception. No tools, memory, database workload or manual OS setup. Private UTC does not change Windows timezone.\r\n\r\n" +
            "TTL2000ms, ready/RPC/partial5000/2000/1000ms, child22/30s, frame8192 bytes, channel/audit128 KiB, " +
            "request/response/stderr4 KiB, report64 KiB and output1024-byte bounds stay unchanged. No new grant or " +
            "deadline extension. Reports contain hashes/counts, not raw response, lease or exception text. " +
            "One M07c attempt only, with fresh consent and separate matching-artifact run approval. No retry/recovery, " +
            "fallback, inference or later cases. Cleanup needs independent checks. Production, containment and Gate A remain unqualified.";
#elif HERMES_MODEL_OVERSIZED
        internal const string Version = "0.2.1-offline-oversized.1";
        internal const string Scope = "offline-hermes-response-size-rejection-v1";
        internal const string Consent =
            "Maya M07b oversized-response candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. Real pinned Hermes sends one fixed synthetic request, not inference. " +
            "No credentials, customer content or charge. Both policy rules remain. A fixed construction-time synthetic " +
            "provider consumes one original dispatch and returns fixed valid JSON of4097 bytes; the original4096-byte guard must reject it before parsing. " +
            "No model response or final text is delivered; UI stays blank. A denial control is not model output. " +
            "Original dispatch uncertainty remains true. One egress gateway decision, one attempted dispatch, zero releases, " +
            "exactly two audit records and natural child/worker exit are required. Generic failure never passes. " +
            "Child observations remain untrusted; this is not hostile-child bypass qualification.\r\n\r\n" +
            "Setup copies embedded Python3.13.14 and pinned Hermes/dependencies to a fresh private ProgramData attempt. " +
            "Same AppContainer, zero capabilities, reduced tokens, one-process jobs, child-process block and six " +
            "scoped WFP network denies. Shared All Application Packages remains a limitation. Trusted medium worker " +
            "is outside child containment and implements no networking. Protected host files are retained for " +
            "SYSTEM, Administrators and this operator. No listener, account, service, registry change or loopback " +
            "exception. No tools, memory, database workload or manual OS setup. Private UTC does not change Windows timezone.\r\n\r\n" +
            "TTL2000ms, ready/RPC/partial5000/2000/1000ms, child22/30s, frame8192 bytes, channel/audit128 KiB, " +
            "request/response/stderr4 KiB, report64 KiB and output1024-byte bounds stay unchanged. No new grant or " +
            "deadline extension. Only an exact4097-byte rejection has a bounded hash/count diagnostic; acceptance stays4096. Reports contain hashes/counts, not raw response, lease or exception text. " +
            "One M07b attempt only, with fresh consent and separate matching-artifact run approval. M07c is not enabled. No retry/recovery, " +
            "fallback, inference or later cases. Cleanup needs independent checks. Production, containment and Gate A remain unqualified.";
#elif HERMES_MODEL_MALFORMED
        internal const string Version = "0.2.1-offline-malformed.1";
        internal const string Scope = "offline-hermes-response-json-rejection-v1";
        internal const string Consent =
            "Maya M07a malformed-response candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. Real pinned Hermes sends one fixed synthetic request, not inference. " +
            "No credentials, customer content or charge. Both policy rules remain. A fixed construction-time synthetic " +
            "provider consumes one original dispatch and returns one malformed byte; the original JSON guard must reject it. " +
            "No model response or final text is delivered; UI stays blank. A denial control is not model output. " +
            "Original dispatch uncertainty remains true. One egress gateway decision, one attempted dispatch, zero releases, " +
            "exactly two audit records and natural child/worker exit are required. Generic failure never passes. " +
            "Child observations remain untrusted; this is not hostile-child bypass qualification.\r\n\r\n" +
            "Setup copies embedded Python3.13.14 and pinned Hermes/dependencies to a fresh private ProgramData attempt. " +
            "Same AppContainer, zero capabilities, reduced tokens, one-process jobs, child-process block and six " +
            "scoped WFP network denies. Shared All Application Packages remains a limitation. Trusted medium worker " +
            "is outside child containment and implements no networking. Protected host files are retained for " +
            "SYSTEM, Administrators and this operator. No listener, account, service, registry change or loopback " +
            "exception. No tools, memory, database workload or manual OS setup. Private UTC does not change Windows timezone.\r\n\r\n" +
            "TTL2000ms, ready/RPC/partial5000/2000/1000ms, child22/30s, frame8192 bytes, channel/audit128 KiB, " +
            "request/response/stderr4 KiB, report64 KiB and output1024-byte bounds stay unchanged. No new grant or " +
            "deadline extension. Reports contain hashes/counts, not raw response, lease or exception text. " +
            "One M07a attempt only, with fresh consent and separate matching-artifact run approval. M07b/M07c are not enabled. No retry/recovery, " +
            "fallback, inference or later cases. Cleanup needs independent checks. Production, containment and Gate A remain unqualified.";
#elif HERMES_MODEL_OUTPUT_DENY
        internal const string Version = "0.2.1-offline-output-denial.1";
        internal const string Scope = "offline-hermes-runtime-output-denial-v1";
        internal const string Consent =
            "Maya M06 runtime-output authorization candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. Real pinned Hermes sends one fixed synthetic request, not inference. " +
            "No credentials, customer content or charge. The host permits one synthetic dispatch, then omits only " +
            "the model.output allow so the original gateway denies releasing its validated response to Hermes. " +
            "No model response or final text is delivered; UI stays blank. A denial control is not model output. " +
            "Original dispatch uncertainty remains true. Two gateway decisions, one dispatch, zero releases, " +
            "exactly three audit records and natural child/worker exit are required. Generic failure never passes. " +
            "Child observations remain untrusted; this is not hostile-child bypass qualification.\r\n\r\n" +
            "Setup copies embedded Python3.13.14 and pinned Hermes/dependencies to a fresh private ProgramData attempt. " +
            "Same AppContainer, zero capabilities, reduced tokens, one-process jobs, child-process block and six " +
            "scoped WFP network denies. Shared All Application Packages remains a limitation. Trusted medium worker " +
            "is outside child containment and implements no networking. Protected host files are retained for " +
            "SYSTEM, Administrators and this operator. No listener, account, service, registry change or loopback " +
            "exception. No tools, memory, database workload or manual OS setup. Private UTC does not change Windows timezone.\r\n\r\n" +
            "TTL2000ms, ready/RPC/partial5000/2000/1000ms, child22/30s, frame8192 bytes, channel/audit128 KiB, " +
            "request/response/stderr4 KiB, report64 KiB and output1024-byte bounds stay unchanged. No new grant or " +
            "deadline extension. Reports contain hashes/counts, not raw response, lease or exception text. " +
            "One M06 attempt only, with fresh consent and separate matching-artifact run approval. No retry/recovery, " +
            "fallback, inference or later cases. Cleanup needs independent checks. Production, containment and Gate A remain unqualified.";
#elif HERMES_MODEL_RECREATE
        internal const string Version = "0.2.1-offline-recreate.1";
        internal const string Scope = "offline-hermes-recreated-client-budget-v1";
        internal const string Consent =
            "Maya M05b recreated-client budget candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. One real pinned Hermes conversation uses a synthetic offline response, " +
            "not inference. No credentials, customer content or charge. After one verified runtime delivery, the fixed " +
            "probe runs on the request owning thread AFTER original native client close and before its hook returns. " +
            "Original close always delegates exactly once. The existing factory creates one distinct SDK/HTTP/transport " +
            "triple using the original validated settings and SAME consumed adapter. One explicit copied valid HTTP " +
            "request must hit the original budget rejection locally before pipe send. No new adapter, grant or rebind. " +
            "No automatic SDK retry, fallback or second conversation. New clients must close normally. " +
            "Private-channel reads use one explicitly scheduled I/O worker with unchanged deadlines; failure reports add " +
            "bounded read stages/counts, not message contents. Two first gateway checks, one dispatch/delivery and exactly " +
            "four audit records remain counted. No operator publication: output and UI stay blank. Child observations " +
            "are untrusted; host checks no extra pipe request or effects. Generic errors/timeouts do not pass. " +
            "This does not prove hostile-child bypass resistance.\r\n\r\n" +
            "Setup copies embedded Python3.13.14, pinned Hermes/dependencies and reviewed sources into a fresh private " +
            "ProgramData attempt. Same AppContainer, zero capabilities, reduced tokens, one-process jobs, child-process " +
            "block and six scoped deny-all WFP filters. Shared All Application Packages remains a limitation. Trusted " +
            "medium worker is outside child containment and implements no networking. Four protected host files remain " +
            "accessible to SYSTEM, Administrators and this operator. No manual OS preparation is authorized. No listener, " +
            "account, service, registry change or loopback exception. No tools, memory or database workload. " +
            "Private UTC does not change Windows timezone.\r\n\r\n" +
            "Original TTL2000ms and ready/RPC/partial5000/2000/1000ms, child22/30s, frame8192 bytes, channel/audit128 KiB, " +
            "request/response/stderr4 KiB, report64 KiB and output1024-byte limits stay. No new grant or deadline extension. " +
            "Second local rejection makes no service-expiry claim. Retained evidence reports contain bounded hashes/counters, " +
            "not raw lease/body/output or exception text. Natural child/worker closure is required before security cleanup. " +
            "Cleanup can fail and needs independent checks. No automatic recovery/retry. Consent covers one M05b attempt " +
            "and this setup only, with separate matching-artifact one-run approval and fresh consent required. " +
            "Later cases, inference, containment, Gate A and production remain unqualified.";
#elif HERMES_MODEL_BUDGET
        internal const string Version = "0.2.1-offline-budget.3";
        internal const string Scope = "offline-hermes-same-client-budget-v1";
        internal const string Consent =
            "Maya M05a same-client request-budget candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. One real pinned Hermes conversation uses a synthetic offline response, " +
            "not inference. No credentials, customer content or charge. After one verified runtime delivery, Maya " +
            "explicitly attempts a second valid HTTP transport request on the SAME used client. The fixed probe runs " +
            "in the request owning thread BEFORE native client cleanup, which always delegates its original close. " +
            "The original adapter budget must reject it locally before pipe send. No automatic SDK retry, fallback or second conversation. " +
            "Private-channel reads use one explicitly scheduled I/O worker with unchanged deadlines; failure reports add bounded read stages/counts, not message contents. " +
            "Two first gateway checks, one dispatch/delivery and exactly four audit records remain counted. " +
            "No operator publication: output stays blank. Child observations are untrusted; host checks no extra pipe " +
            "request or effects. Generic errors/timeouts do not pass. This does not prove hostile-child bypass resistance.\r\n\r\n" +
            "Setup copies embedded Python3.13.14, pinned Hermes/dependencies and reviewed sources into a fresh private " +
            "ProgramData attempt. Same AppContainer, zero capabilities, reduced tokens, one-process jobs, child-process " +
            "block and six scoped deny-all WFP filters. Shared All Application Packages remains a limitation. Trusted " +
            "medium worker is outside child containment and implements no networking. Four protected host files remain " +
            "accessible to SYSTEM, Administrators and this operator. No listener, account, service, registry change " +
            "or loopback exception. No tools, memory or database workload. Private UTC does not change Windows timezone.\r\n\r\n" +
            "Original TTL2000ms and ready/RPC/partial5000/2000/1000ms, child22/30s, frame8192 bytes, channel/audit128 KiB, " +
            "request/response/stderr4 KiB, report64 KiB and output1024-byte limits stay. No new grant or deadline extension. " +
            "Second local rejection makes no service-expiry claim. Reports contain bounded hashes/counters, not raw " +
            "lease/body/output or exception text. Natural child/worker closure is required before security cleanup. " +
            "Cleanup can fail and needs independent checks. No automatic recovery/retry. Consent covers one M05a attempt " +
            "and this setup only; M05b/later cases, inference, containment, Gate A and production remain unqualified.";
#elif HERMES_MODEL_REPLAY
        internal const string Version = "0.2.1-offline-replay.1";
        internal const string Scope = "offline-hermes-consumed-lease-v1";
        internal const string Consent =
            "Maya M04c consumed-grant replay candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. No external inference, credentials, customer content or charge. " +
            "Real pinned Hermes/SDK make ONE normal synthetic exchange. Two original gateway checks, ONE synthetic " +
            "dispatch and ONE verified runtime delivery must remain counted. Maya then replays the exact saved request " +
            "under a NEW trusted command ID. The original guard must reject the consumed, still-unexpired/unrevoked " +
            "grant with no additional effects. Four positive audit events plus one exact rejection are required. " +
            "The child keeps its one-request guard and genuine POSITIVE conversation/closure report. No child denial " +
            "is fabricated. Operator preparation/publication is withheld: output stays blank. Generic denial, expiry, " +
            "audit failure or timeout is NOT success. Prior effects are never reset.\r\n\r\n" +
            "Setup copies embedded Python3.13.14, pinned Hermes/dependencies and reviewed sources into a fresh private " +
            "ProgramData attempt. Same AppContainer/zero capabilities/reduced tokens/one-process jobs/child-process " +
            "block/six child-scoped deny-all WFP filters. Shared All Application Packages remains a limitation. One " +
            "trusted medium worker is OUTSIDE child containment and implements no networking. No listener, account, " +
            "service, registry or loopback exception. Protected host request.json, policy.json, worker.json and audit.jsonl " +
            "remain accessible to SYSTEM, Administrators and this operator. No tools/memory/database workload.\r\n\r\n" +
            "Synthetic data only; private UTC does not change Windows timezone. Reports/audit contain bounded hashes, " +
            "ages and effect evidence, not raw lease/body/output/exception messages. Original TTL2000ms covers the " +
            "positive prefix AND replay. No deliberate wait, renewal, TTL/deadline extension or fake native clock. " +
            "Ready/RPC/partial5000/2000/1000ms, child22/30s, frame8192 bytes, channel/audit128 KiB, request/response/" +
            "stderr4 KiB, report64 KiB, output1024 bytes. Slow disk/scheduling blocks, never retries automatically.\r\n\r\n" +
            "Natural child/worker closure is required. Both jobs stop before temporary security removal/label restoration. " +
            "Cleanup may fail and needs independent checks. No fallback/retry/automatic recovery. Other cases, inference, " +
            "containment, Gate A and production remain unqualified. Consent covers one M04c attempt and this setup only.";
#elif HERMES_MODEL_REVOKE
        internal const string Version = "0.2.1-offline-revocation.1";
        internal const string Scope = "offline-hermes-lease-revocation-v1";
        internal const string Consent =
            "Maya M04b unused unexpired-grant revocation candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. No external inference, credential, customer content or charge. " +
            "Real pinned Hermes/SDK send the original valid synthetic request. Maya issues its ordinary 2000-ms " +
            "grant, calls the original revoke method and verifies a durable acknowledgement BEFORE model_begin. " +
            "The original guard must reject that same unused, revoked but UNEXPIRED grant. Two exact audit records " +
            "and zero gateway calls/dispatches/model-response releases/publications are required. Blank output is " +
            "expected; expiry, timeout or generic denial is NOT success. No deliberate wait, TTL change, reissue, " +
            "replay, child-guard bypass or fake native clock.\r\n\r\n" +
            "Setup copies embedded Python 3.13.14, pinned Hermes/dependencies and reviewed sources to a fresh " +
            "ProgramData attempt. Same ordinary AppContainer, zero capabilities, reduced tokens, one-process jobs, " +
            "child-process block and six child-scoped deny-all WFP filters. Shared All Application Packages access " +
            "remains a limitation. One trusted medium worker is OUTSIDE child containment and implements no networking. " +
            "No listener/account/service/registry/loopback exception. Host request.json, policy.json, worker.json and " +
            "audit.jsonl remain accessible to SYSTEM, Administrators and this operator.\r\n\r\n" +
            "Synthetic data only, no tools/memory/database workload. Private UTC does not change Windows timezone. " +
            "Reports contain bounded hashes, ages and evidence, not raw lease/body/output/exception messages. " +
            "Required audit failure or expiry during revoke/guard/audit blocks acceptance; startup diagnostics are " +
            "failure-only. Ready/RPC/partial limits 5000/2000/1000 ms, child 22/30 seconds, frame8192 bytes, " +
            "channel/audit128 KiB, request/response/stderr4 KiB, report64 KiB, output1024 bytes. All operations " +
            "consume existing budgets, with no extension. Natural child/worker closure is required.\r\n\r\n" +
            "Both jobs stop before temporary security removal and label restoration. Cleanup may fail and needs " +
            "independent checks. No fallback/retry/automatic recovery. Other cases, inference, containment, Gate A " +
            "and production remain unqualified. Consent covers one M04b attempt and this disclosed setup only.";
#elif HERMES_MODEL_EXPIRY
        internal const string Version = "0.2.1-offline-expiry.1";
        internal const string Scope = "offline-hermes-lease-expiry-v1";
        internal const string Consent =
            "Maya M04a unused-grant expiry candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. NO external inference, credential, customer content or charge. " +
            "Real pinned Hermes/SDK send their original valid synthetic request. Maya issues its normal 2000-ms grant, " +
            "waits at least 2100 real monotonic ms AFTER the reply and BEFORE model_begin, outside any worker RPC, " +
            "then submits the unchanged request. Grant, body, model, route, identity and child guards are unchanged. " +
            "The worker must observe its actual expiry guard rejecting an UNUSED, UNREVOKED grant with exact " +
            "request preflight and zero gateway calls/dispatches/model-response releases/publications. Blank output " +
            "is expected; timeout or generic denial is NOT success. No revocation/replay, reissue or fake native clock.\r\n\r\n" +
            "Maya copies embedded Python 3.13.14, pinned Hermes/dependencies and reviewed sources into a fresh private " +
            "ProgramData attempt. Same ordinary AppContainer, zero capabilities, reduced tokens, one-process jobs, " +
            "child-process block and six child-scoped deny-all WFP filters. Shared All Application Packages access " +
            "remains a limitation. One trusted medium worker is OUTSIDE child containment and implements no networking. " +
            "No listener, account, service, registry or loopback exception. Protected host request.json, policy.json, " +
            "worker.json and audit.jsonl stay accessible to SYSTEM, Administrators and this operator.\r\n\r\n" +
            "Synthetic data only; private UTC does not change Windows timezone. No tools/memory/database workload. " +
            "Reports/audit contain bounded hashes, elapsed ages and fixed evidence, never raw lease/body/output or " +
            "exception messages. Required audit failure blocks acceptance. Startup diagnostics remain failure-only. " +
            "Ready/RPC/partial-frame limits 5000/2000/1000 ms; child 22/30 seconds. The deliberate wait CONSUMES " +
            "existing budgets; exhaustion blocks, with no timeout/TTL extension. Frame 8192 bytes, channel/audit " +
            "128 KiB, request/response/stderr 4 KiB, report 64 KiB, output 1024 bytes. No fallback/retry.\r\n\r\n" +
            "Both jobs stop before temporary security removal/label restoration. Cleanup may fail and needs " +
            "independent checks. No automatic recovery. Other cases, real inference, containment, Gate A and " +
            "production remain unqualified. Consent covers one M04a attempt and disclosed setup only.";
#elif HERMES_MODEL_BODY
        internal const string Version = "0.2.1-offline-body.1";
        internal const string Scope = "offline-hermes-body-validation-v1";
        internal const string Consent =
            "Maya M03d fixed wrong-body validation candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. NO external inference, credential, customer content or charge. " +
            "Real pinned Hermes/SDK send their original valid synthetic request. The trusted coordinator verifies " +
            "the native body and envelope against the host-issued grant, then changes ONLY the last hex digit of the synthetic user-message canary. " +
            "The digit becomes 1 if originally 0; otherwise 0. Actual host identity, attempt, route, grant and model stay unchanged. " +
            "This tests WORKER validation, not hostile-child bypass. Positive gateway policy remains present. " +
            "Expected: exact-body rejection before body admission or any gateway call/dispatch, zero model-response " +
            "releases/publications and blank model output. Generic failure is NOT success.\r\n\r\n" +
            "Maya copies embedded Python 3.13.14, pinned Hermes/dependencies and reviewed product sources into a fresh " +
            "private ProgramData attempt. Setup uses ordinary AppContainer, zero capabilities, reduced tokens, " +
            "one-process jobs, child-process block and six child-scoped deny-all WFP filters. Shared All Application " +
            "Packages access remains a limitation. One trusted medium worker is OUTSIDE AppContainer and its network " +
            "filters; it implements no networking. No listener, account, service, registry or loopback exception.\r\n\r\n" +
            "Protected host request.json, policy.json, worker.json and audit.jsonl remain accessible to SYSTEM, " +
            "Administrators and this operator. The request contains only synthetic canary/private state path and UTC day; " +
            "Windows timezone is unchanged. No tools, memory/database workload, fallback or retries. Reports/audit " +
            "contain hashes and fixed metadata, not raw request, grant lease, model output or exception messages. " +
            "Exact body hashes bind original/mutant request bytes without publishing the body or lease. " +
            "Audit failure blocks acceptance.\r\n\r\n" +
            "Child deadlines remain 22/30 seconds; frames 8192 bytes; request/response/stderr 4 KiB; channel/audit " +
            "128 KiB; report 64 KiB; output 1024 bytes. Startup failure reports may include allowlisted stage/error " +
            "codes, channel category, stderr byte counts and available exit snapshots. Diagnostics never qualify a failure. " +
            "Both jobs stop before temporary security removal/label restoration. Cleanup may fail and needs independent checks. " +
            "No automatic recovery/retry. Later variants, real inference, containment, Gate A and production remain unqualified. " +
            "Consent covers one M03d attempt and its disclosed setup only.";
#elif HERMES_MODEL_ATTEMPT
        internal const string Version = "0.2.1-offline-attempt.1";
        internal const string Scope = "offline-hermes-attempt-validation-v1";
        internal const string Consent =
            "Maya M03c fixed wrong-attempt validation candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. NO external inference, credential, customer content or charge. " +
            "Real pinned Hermes/SDK send their original valid synthetic request. The trusted coordinator verifies " +
            "the native body and envelope against the host-issued grant, then changes ONLY the first hex digit of the request attempt ID. " +
            "The digit becomes 1 if originally 0; otherwise 0. Actual host identity, route and body stay unchanged. " +
            "This tests WORKER validation, not hostile-child bypass. Positive gateway policy remains present. " +
            "Expected: attempt-binding rejection before body admission or any gateway call/dispatch, zero model-response " +
            "releases/publications and blank model output. Generic failure is NOT success.\r\n\r\n" +
            "Maya copies embedded Python 3.13.14, pinned Hermes/dependencies and reviewed product sources into a fresh " +
            "private ProgramData attempt. Setup uses ordinary AppContainer, zero capabilities, reduced tokens, " +
            "one-process jobs, child-process block and six child-scoped deny-all WFP filters. Shared All Application " +
            "Packages access remains a limitation. One trusted medium worker is OUTSIDE AppContainer and its network " +
            "filters; it implements no networking. No listener, account, service, registry or loopback exception.\r\n\r\n" +
            "Protected host request.json, policy.json, worker.json and audit.jsonl remain accessible to SYSTEM, " +
            "Administrators and this operator. The request contains only synthetic canary/private state path and UTC day; " +
            "Windows timezone is unchanged. No tools, memory/database workload, fallback or retries. Reports/audit " +
            "contain hashes and fixed metadata, not raw request, grant lease, model output or exception messages. " +
            "Versioned envelope projections bind original/mutated request attempt IDs and unchanged body without publishing the lease. " +
            "Audit failure blocks acceptance.\r\n\r\n" +
            "Child deadlines remain 22/30 seconds; frames 8192 bytes; request/response/stderr 4 KiB; channel/audit " +
            "128 KiB; report 64 KiB; output 1024 bytes. Startup failure reports may include allowlisted stage/error " +
            "codes, channel category, stderr byte counts and available exit snapshots. Diagnostics never qualify a failure. " +
            "Both jobs stop before temporary security removal/label restoration. Cleanup may fail and needs independent checks. " +
            "No automatic recovery/retry. Later variants, real inference, containment, Gate A and production remain unqualified. " +
            "Consent covers one M03c attempt and its disclosed setup only.";
#elif HERMES_MODEL_ROUTE
        internal const string Version = "0.2.1-offline-route.1";
        internal const string Scope = "offline-hermes-route-validation-v1";
        internal const string Consent =
            "Maya M03b fixed wrong-route validation candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. NO external inference, credential, customer content or charge. " +
            "Real pinned Hermes/SDK send their original valid synthetic request. The trusted coordinator verifies " +
            "the native body and envelope against the host-issued grant, then changes ONLY route " +
            "maya.offline.model.v1 to maya.offline.model.v0. The body bytes remain identical. " +
            "This tests WORKER validation, not hostile-child bypass. Positive gateway policy remains present. " +
            "Expected: route rejection before body admission or any gateway call/dispatch, zero model-response " +
            "releases/publications and blank model output. Generic failure is NOT success.\r\n\r\n" +
            "Maya copies embedded Python 3.13.14, pinned Hermes/dependencies and reviewed product sources into a fresh " +
            "private ProgramData attempt. Setup uses ordinary AppContainer, zero capabilities, reduced tokens, " +
            "one-process jobs, child-process block and six child-scoped deny-all WFP filters. Shared All Application " +
            "Packages access remains a limitation. One trusted medium worker is OUTSIDE AppContainer and its network " +
            "filters; it implements no networking. No listener, account, service, registry or loopback exception.\r\n\r\n" +
            "Protected host request.json, policy.json, worker.json and audit.jsonl remain accessible to SYSTEM, " +
            "Administrators and this operator. The request contains only synthetic canary/private state path and UTC day; " +
            "Windows timezone is unchanged. No tools, memory/database workload, fallback or retries. Reports/audit " +
            "contain hashes and fixed metadata, not raw request, grant lease, model output or exception messages. " +
            "Versioned envelope projections bind original/mutated routes and unchanged body without publishing the lease. " +
            "Audit failure blocks acceptance.\r\n\r\n" +
            "Child deadlines remain 22/30 seconds; frames 8192 bytes; request/response/stderr 4 KiB; channel/audit " +
            "128 KiB; report 64 KiB; output 1024 bytes. Startup failure reports may include allowlisted stage/error " +
            "codes, channel category, stderr byte counts and available exit snapshots. Diagnostics never qualify a failure. " +
            "Both jobs stop before temporary security removal/label restoration. Cleanup may fail and needs independent checks. " +
            "No automatic recovery/retry. Later variants, real inference, containment, Gate A and production remain unqualified. " +
            "Consent covers one M03b attempt and its disclosed setup only.";
#elif HERMES_MODEL_VALIDATION
        internal const string Version = "0.2.1-offline-validation.2";
        internal const string Scope = "offline-hermes-model-validation-v1";
        internal const string Consent =
            "Maya M03a fixed wrong-model validation candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. NO external inference, credential, customer content or charge. " +
            "Real pinned Hermes/SDK send their original valid synthetic request. The trusted coordinator verifies " +
            "its exact bytes, then derives one separate worker request changing only maya-offline-wire-v1 to " +
            "maya-offline-wire-v0. Existing child guards stay enabled. This tests WORKER validation, not hostile-child " +
            "bypass. Positive gateway policy stays present. Expected: rejection BEFORE any gateway call or dispatch, " +
            "zero model-response releases/publications and a blank model-output field. Generic failure is NOT success.\r\n\r\n" +
            "Maya copies embedded Python 3.13.14, pinned Hermes/dependencies and reviewed product sources into a fresh " +
            "private ProgramData attempt. Setup uses ordinary AppContainer, zero capabilities, reduced tokens, " +
            "one-process jobs, child-process block and six child-scoped deny-all WFP filters. Shared All Application " +
            "Packages access remains a limitation. One trusted medium worker is OUTSIDE AppContainer and its network " +
            "filters; it implements no networking. No listener, account, service, registry or loopback exception.\r\n\r\n" +
            "Protected host request.json, policy.json, worker.json and audit.jsonl remain accessible to SYSTEM, " +
            "Administrators and this operator. The request includes synthetic canary/private state path and UTC day; " +
            "Windows timezone is unchanged. No tools, memory/database workload, fallback or retries. Reports/audit " +
            "contain bounded hashes and evidence, not raw request or model output. Audit failure blocks acceptance.\r\n\r\n" +
            "Child deadlines remain 22/30 seconds; frames 8192 bytes; request/response/stderr 4 KiB; channel/audit " +
            "128 KiB; report 64 KiB; output 1024 bytes. Startup failure reports may include allowlisted stage/error " +
            "codes, channel category, observed stderr byte counts and available process exit snapshots; no raw " +
            "stderr, paths or exception messages are released. Diagnostics never qualify a failed test. " +
            "Both jobs stop before removing temporary security resources " +
            "and restoring labels. Cleanup may fail and needs independent checks. No automatic recovery/retry. " +
            "Other M03 variants, later cases, real inference, containment, Gate A and production remain unqualified. " +
            "Consent covers one M03a attempt and its disclosed setup only.";
#elif HERMES_MODEL_DENY
        internal const string Version = "0.2.1-offline-denial.1";
        internal const string Scope = "offline-hermes-model-denial-v1";
        internal const string Consent =
            "Maya offline M02 authorization-denial candidate " + Version + "\r\n\r\n" +
            "Unsigned development candidate. NO external inference, provider connection, credential, customer content or charge. " +
            "Real pinned Hermes and its SDK send one valid synthetic request through private inherited pipes. " +
            "The existing gateway's fixed policy omits model.egress permission. Expected result: deny before dispatch, " +
            "zero synthetic provider dispatches, zero runtime response releases and zero operator publications. " +
            "The blank output field is expected; a setup failure, timeout or missing audit is NOT a passed denial.\r\n\r\n" +
            "Maya copies verified embedded Python 3.13.14, pinned Hermes, dependencies and product code into a fresh " +
            "private ProgramData attempt. It provisions ordinary AppContainer, zero capabilities, reduced tokens, " +
            "one-process jobs, child-process block and six child-scoped deny-all WFP filters. Shared All Application " +
            "Packages access remains a limitation. One trusted medium worker is OUTSIDE AppContainer and its network " +
            "filters; this profile implements no worker networking. No listener, loopback exemption or OS registry change.\r\n\r\n" +
            "Protected host request.json, policy.json, worker.json and audit.jsonl remain as evidence, accessible only " +
            "to SYSTEM, Administrators and this operator. Request includes synthetic canary, private state path and UTC " +
            "day; Windows timezone is unchanged. No tools, memory/database workload, real response, fallback or retry. " +
            "A bounded denial control is not model output. Required audit failure blocks acceptance.\r\n\r\n" +
            "Child deadlines remain 22/30 seconds, frames 8192 bytes, request/response/stderr 4 KiB, report 64 KiB, " +
            "channel/audit 128 KiB and output 1024 bytes. Maya stops both jobs before removing its temporary security " +
            "resources and restoring labels. Cleanup can fail and needs independent checks. No automatic recovery or " +
            "retry. M03-M09, real inference, containment, Gate A and production are not qualified.\r\n\r\n" +
            "Consent authorizes this single M02 attempt and its disclosed temporary setup only.";
#elif HERMES_MODEL
        internal const string Version = "0.2.1-offline-model.1";
        internal const string Scope = "offline-hermes-model-wire-v1";
        internal const string Consent =
            "Maya offline model bridge " + Version + "\r\n\r\n" +
            "Unsigned development candidate, not production or containment qualified. One real pinned Hermes " +
            "conversation uses its genuine SDK with a private-pipe transport and an explicitly synthetic response. " +
            "There is NO external inference, network provider, credential, customer content or charge.\r\n\r\n" +
            "Maya copies verified Python 3.13.14, pinned Hermes, unchanged dependencies and canonical Maya code " +
            "into a fresh private ProgramData attempt. It provisions ordinary AppContainer with zero capabilities, " +
            "reduced tokens, one-process jobs, child-process block and six child-scoped deny-all WFP filters. " +
            "Shared All Application Packages access remains an isolation limitation.\r\n\r\n" +
            "One additional trusted medium-integrity Python gateway worker remains OUTSIDE AppContainer. " +
            "Child filters do not contain the worker. This profile implements no worker networking or live model " +
            "operation. Private inherited pipes, not HTTP/listeners or loopback exemptions, carry bounded messages.\r\n\r\n" +
            "A protected host folder retains request.json, exact policy, worker setup and durable audit. " +
            "Only SYSTEM, Administrators and this operator have access. Expected request text comes from reviewed " +
            "native literals and trusted setup, not the child's first request. The synthetic request includes " +
            "the private attempt's state path and UTC day; UTC is a private Hermes config, not an OS change.\r\n\r\n" +
            "A version-bound Maya subclass selects Hermes' native non-streaming path and delegates client creation " +
            "with fresh private HTTP transports. No wheel patch, fake runtime, credentials, tools, memory/database " +
            "workload, fallback or retries. One synthetic dispatch is allowed. Runtime output and final operator " +
            "output require separate existing-gateway decisions and exact synthetic-content validation. " +
            "The approved synthetic final text is displayed in this Maya window; reports contain only evidence.\r\n\r\n" +
            "This first positive compatibility slice does not qualify the pending model bypass/negative matrix. " +
            "Required audit faults have local fixtures only. Audit failure blocks further effects; possible sends " +
            "or display are reported uncertain, never recalled or retried. The poisoned ledger is not reopened.\r\n\r\n" +
            "Bounds stay 8192-byte frames, 128 KiB per channel direction/audit, 4 KiB request/response/stderr, " +
            "1 KiB final output and 64 KiB report. Child 22-second cooperative/30-second host budget; worker " +
            "readiness 5 seconds, RPC/display up to 2 seconds, incomplete frames 1 second. Output cap 32 tokens. " +
            "Payload ceilings stay 8192 files/4 MiB index, 32 MiB per file/256 MiB expanded.\r\n\r\n" +
            "No new OS account/service, network permit, registry/loopback grant, system Python/PATH, antivirus, " +
            "boot/encryption or test supervisor. Both jobs must stop before cleanup; automatic bridge recovery " +
            "is disabled. Files/reports remain for review. Independent cleanup is required. Stop after one result; " +
            "no automatic retry. Gate A, full containment and production remain unqualified.";
#elif HERMES_BRIDGE
        internal const string Version = "0.2.0-bridge-document.2";
        internal const string Scope = "offline-authorized-document-bridge-v1";
        internal const string Consent =
            "Maya authorization bridge " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. Copies verified bundled Python 3.13.14, " +
            "pinned Hermes, the same dependency set and canonical Maya code into a fresh private ProgramData attempt.\r\n\r\n" +
            "Maya creates its ordinary zero-capability AppContainer, read/execute runtime and low-integrity " +
            "private state, reduced token, one-process job, child-process block and six deny-all network filters. " +
            "All Application Packages access remains a limitation, not full customer-data isolation.\r\n\r\n" +
            "NEW: Maya starts one additional trusted medium-integrity Python gateway worker outside AppContainer, " +
            "with a separate one-process kill-on-close job. This worker is trusted product code; the child's " +
            "network filters do not sandbox it. It has no model/network operation. Private inherited pipes " +
            "carry framed requests, not HTTP or listening sockets. No child can choose actor, path or policy.\r\n\r\n" +
            "NEW: a protected host folder contains an unpredictable synthetic document, exact local policy, " +
            "worker configuration and required audit. Only SYSTEM, Administrators and this operator have access; " +
            "there is no child package grant. These files and private reports remain after cleanup. No customer " +
            "file, provider credential, model call, business write, connector or Metabase is used.\r\n\r\n" +
            "Ten fixed native cases test one authorized document release and denied policy, direct file access, " +
            "wrong identity/target/action, replay, expiry, cancellation and disclosure. Both audit-failure cases " +
            "remain mandatory local tests, not native-qualified. A failed audit is never reopened to continue. " +
            "The real Hermes tool registry is used; there is no conversation/model selection test.\r\n\r\n" +
            "Required audit is flushed and fsynced before read and disclosure. Cancellation cannot recall " +
            "already committed bytes; uncertain outcomes stop without retry. NEW framing bounds: 8192 bytes " +
            "per frame, 128 KiB each channel direction, 1 KiB document, 128 KiB audit, 4 KiB stderr and 64 KiB " +
            "report. Child budgets stay 22 seconds cooperative/30 seconds host. Worker readiness 5 seconds, " +
            "processing 2 seconds and incomplete frames 1 second. Payload caps remain 8192 files/4 MiB index, " +
            "32 MiB per file/256 MiB expanded. No new capability, network permit, loopback or registry grant.\r\n\r\n" +
            "No system Python/PATH, account/service, Windows policy, antivirus, boot/encryption change or test " +
            "supervisor. Maya must confirm both jobs stopped before revoking permissions/profile/filters. " +
            "Forced closure or uncertain cleanup requires review; bridge automatic recovery is not qualified. " +
            "Independent cleanup remains necessary. Stop after one result. No weakened protection or retry; " +
            "Gate A, containment and production remain unqualified.";
#elif HERMES_MEMORY
        internal const string Version = "0.1.4-hermes-memory.1";
        internal const string Scope = "offline-hermes-native-memory-v1";
        internal const string Consent =
            "Maya protected Hermes native memory " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. Maya copies verified Python 3.13.14, " +
            "the same pinned Hermes and 63 dependencies into a fresh private ProgramData attempt. Limits " +
            "remain 8192 files, 4 MiB inventory, 32 MiB per file and 256 MiB expanded.\r\n\r\n" +
            "With consent Maya creates one ordinary AppContainer, runtime read/execute and low-integrity " +
            "private-state read/write grants, six package-scoped WFP network denies, a reduced same-user token, " +
            "one-process job, child-process block and three inherited pipes. Existing All Application Packages " +
            "access is not complete customer-data isolation.\r\n\r\n" +
            "One real agent enables its native MemoryStore with 2200/1375-character limits and no external " +
            "memory provider. For each of MEMORY.md and USER.md it adds two fixed synthetic entries, replaces " +
            "the first and removes the second: eight native mutations. A fresh store reloads both files in " +
            "the same process; snapshots, exact readbacks, hashes and residue are checked. This is not " +
            "authoritative memory, tool authorization, crash/restart durability or atomic-write qualification.\r\n\r\n" +
            "Private state/memories holds MEMORY.md, USER.md and their .lock files; native .mem_*.tmp files " +
            "are transient, and unexpected backups cause failure. One nonblocking acquire/release probe per " +
            "lock file follows native calls, not a concurrent-writer test. A 64 KiB aggregate acceptance " +
            "ceiling is checked at stages, not enforced as a disk quota. Config/cache/logs/sessions and bounded " +
            "reports remain. Native setup may create an empty memories directory before construction.\r\n\r\n" +
            "No conversation, model request, tool, connector, customer data or real credential is supplied. " +
            "The SDK uses the same public non-secret placeholder, synthetic model and .invalid URL. All network " +
            "including localhost stays denied. SQLite is not exercised. Context files, checkpoints, compression, " +
            "environment probing, tool search and lazy installs stay disabled. No new permissions, registry " +
            "grant, loopback exemption, Windows policy, antivirus, boot/encryption, system Python/PATH or supervisor.\r\n\r\n" +
            "The 22-second cooperative budget, 30-second host deadline and output/report bounds remain. Maya " +
            "stops the job before revoking grants and removing profile/filters; synthetic files/reports remain. " +
            "Administrator consent and child-token verification are required. Shutdown may suppress errors; " +
            "independent cleanup is still necessary. Forced closure may leave cleanup pending. Stop on failure; " +
            "no retry or weakened protections. Containment, Gate A and production remain unqualified.";
#elif HERMES_STATE
        internal const string Version = "0.1.3-hermes-state.1";
        internal const string Scope = "offline-hermes-session-state-v1";
        internal const string Consent =
            "Maya protected Hermes session storage " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. Maya copies the same verified Python " +
            "3.13.14, pinned Hermes and 63 dependencies into a fresh private ProgramData attempt. Limits " +
            "remain 8192 files, 4 MiB inventory, 32 MiB per file and 256 MiB expanded.\r\n\r\n" +
            "With your consent Maya creates one ordinary AppContainer, runtime read/execute and low-integrity " +
            "private-state read/write grants, and six package-scoped WFP network denies. Reduced same-user " +
            "token, one-process job, child-process block and three inherited pipes remain. Existing All " +
            "Application Packages access is not complete customer-data isolation.\r\n\r\n" +
            "Python creates Hermes' real state.db with its native schema and possible SQLite WAL/SHM/journal " +
            "sidecars. It creates one synthetic session, attaches the DB to one real agent, and stores exactly " +
            "two small fixed fixture messages, not model output. It verifies records, ends the agent session, " +
            "closes the DB, reopens it read-only in the same process, verifies persistence and closes again. " +
            "This is not crash recovery, restart durability, full search or memory-file qualification.\r\n\r\n" +
            "No model request, conversation, tool, connector, MEMORY.md/USER.md or customer-data operation is " +
            "invoked. Memory providers remain disabled. The real SDK/TLS client uses the same public non-secret " +
            "placeholder, synthetic model and .invalid URL. All network access stays denied, including localhost. " +
            "No real credentials, existing home/.env or authoritative business store is supplied.\r\n\r\n" +
            "Private config/cache/logs/sessions and bounded reports remain. SQLite files must stay within a " +
            "32 MiB acceptance ceiling at checked stages; this is not a disk quota. WAL must be observed; " +
            "no forced journal setting or fallback is accepted as success. No new permissions, registry grants, " +
            "loopback exemption, Windows policy, antivirus, boot/encryption, global Python/PATH or supervisor.\r\n\r\n" +
            "The 22-second cooperative budget, 30-second host deadline and output/report bounds remain. " +
            "Maya stops the job before revoking grants and removing profile/filters; files and reports remain. " +
            "Administrator consent is required; child token checks must pass. Shutdown may suppress errors, " +
            "so independent cleanup remains necessary. Forced closure may leave cleanup pending. Stop after " +
            "failure: no retry or weakened protections. No containment, governance or production qualification.";
#elif HERMES_CONSTRUCTION
        internal const string Version = "0.1.2-hermes-construction.2";
        internal const string Scope = "offline-hermes-construction-v1";
        internal const string Consent =
            "Maya protected Hermes construction " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. With your consent Maya copies " +
            "verified Python 3.13.14, pinned Hermes and the same 63 dependencies into a new private " +
            "ProgramData attempt. Limits remain 8192 files, 4 MiB inventory, 32 MiB per file and 256 MiB expanded.\r\n\r\n" +
            "Maya creates one ordinary AppContainer, runtime read/execute and low-integrity private-state " +
            "read/write grants, and six package-scoped WFP network denies. A reduced same-user token, " +
            "one-process job and child-process block remain. Existing All Application Packages access " +
            "means this is not complete customer-data isolation.\r\n\r\n" +
            "Python imports and constructs one real Hermes agent with tools, memory providers, context " +
            "files, checkpoints and conversations disabled, then calls context shutdown and close. " +
            "The real SDK/TLS client initializes using a fixed public non-secret placeholder key, " +
            "synthetic model and https://maya-construction.invalid/v1. No server or model request is invoked. " +
            "All network access remains denied. No customer data, real credentials or existing home is supplied.\r\n\r\n" +
            "A fixed private config.yaml disables compression and the environment probe and sets context " +
            "size 131072. Hermes may create private sessions/logs/cache state. Supported lazy installs remain " +
            "disabled. No registry, loopback, antivirus, boot, encryption, machine Python/PATH or Windows " +
            "policy changes; no test listeners or external supervisor.\r\n\r\n" +
            "The 22-second cooperative budget, 30-second host deadline and output/report bounds remain. " +
            "Maya stops the job before revoking grants and removing profile/filters. Files and reports remain. " +
            "Administrator consent is required; the child must pass all restricted-token checks. " +
            "Shutdown methods suppress some errors: a returned call is not complete cleanup proof. " +
            "Forced closure can leave cleanup pending. Stop on failure; do not retry or weaken protections. " +
            "Success qualifies neither governed execution nor containment or production; independent cleanup remains required.";
#elif HERMES_IMPORT
        internal const string Version = "0.1.1-hermes-import.1";
        internal const string Scope = "offline-hermes-import-v1";
        internal const string Consent =
            "Maya protected Hermes import " + Version + "\r\n\r\n" +
            "Unsigned development component, not production-qualified. With your consent, Maya " +
            "copies verified Python 3.13.14, pinned Hermes and 63 dependencies into a new private " +
            "ProgramData attempt. This profile permits at most 8192 files and a 4 MiB inventory; " +
            "32 MiB per-file and 256 MiB expanded limits remain. Extraction and cleanup may take longer.\r\n\r\n" +
            "Maya creates one ordinary AppContainer profile, grants read/execute on its runtime " +
            "and read/write on its low-integrity private state, and creates six profile-scoped " +
            "WFP network denies. Ordinary AppContainer has Windows' existing All Application " +
            "Packages access; that is not complete customer-data isolation. A reduced same-user " +
            "token, one-process job and child-process policy restrict one Python process.\r\n\r\n" +
            "Python imports the real run_agent:AIAgent class but never constructs an agent or calls " +
            "a model, tool, skill, connector or authoritative store. Imports can initialize tool " +
            "registries and native dependencies. Existing modules may skip optional imports. " +
            "Hermes lazy installs are disabled through its supported environment option. " +
            "No existing home, .env, credentials or customer files are provided. A fresh private " +
            "home/cache/temp configuration and explicit read-only import/DLL paths are used.\r\n\r\n" +
            "No synthetic listeners, path aliases, shared-memory fixture, public-file grant or " +
            "WFP event collection is needed. No Windows policy, registry grants, loopback exemption, " +
            "antivirus, boot, encryption or machine Python/PATH setting changes. " +
            "All network access remains denied. Python has a 22-second cooperative import budget " +
            "and unchanged 30-second host deadline; output/report bounds remain unchanged.\r\n\r\n" +
            "Maya stops the job before removing grants, profile and filters. Files and reports " +
            "remain for inspection. Process-local critical-error handling is unchanged. " +
            "Administrator consent is required for setup; Python must pass restricted-token checks. " +
            "Closing forcibly may leave cleanup pending. Do not retry or weaken protection after " +
            "failure. Import success does not qualify construction, Hermes execution, governance " +
            "or containment; independent cleanup is still required.";
#else
        internal const string Version = "0.1.0-screen.11";
        internal const string Scope = "synthetic-containment-screen-v1";
        internal const string Consent =
            "Maya protected Python containment screen " + Version + "\r\n\r\n" +
            "This is an unsigned development component, not the complete Maya product.\r\n\r\n" +
            "With your approval, Maya will:\r\n" +
            "- Copy its embedded Python 3.13.14 into a new, private Maya folder under ProgramData.\r\n" +
            "- Create one ordinary Windows AppContainer profile for this attempt, not LPAC.\r\n" +
            "  Ordinary AppContainer can access resources Windows already grants to All Application " +
            "Packages; this is broader implicit access than LPAC, not containment qualification.\r\n" +
            "- Give that profile read/execute access to its Python files and read/write access " +
            "to its private state; lower only that state folder's integrity label.\r\n" +
            "- Add six persistent network-block rules, scoped only to that profile: IPv4/IPv6 " +
            "outbound, listening and incoming connections. No network access is requested.\r\n" +
            "- Create a reduced, non-elevated launch token for your same user, without " +
            "changing your account, UAC settings or the setup host's token.\r\n" +
            "- Start one low-integrity Python process, with no extra capabilities or child " +
            "processes, for at most 30 seconds. It writes a fresh local startup record.\r\n" +
            "- Stop the process and remove its profile, rules and file grants afterward. " +
            "Keep the prepared files and result report for inspection.\r\n\r\n" +
             "Maya sets a process-local error mode inherited by Python to avoid critical-error " +
             "dialogs hiding exit failures. Windows Error Reporting is not disabled. " +
             "After a timeout, Maya stops Python before recording available output counts and " +
             "its startup marker; a timeout is never reported as startup success.\r\n\r\n" +
            "This screen also creates synthetic document, memory, business, policy, audit " +
            "and dummy-secret canaries inside this new Maya attempt folder. Python attempts " +
            "direct reads, writes, creation and deletion, plus fixed path/ADS/link routes. " +
            "One new public canary gets temporary All Application Packages read access. " +
            "Maya creates a private shared-memory object and four temporary loopback-only " +
            "TCP/UDP endpoints (IPv4 and IPv6), with host positive controls. Python attempts " +
            "network access, host process/token access and one fixed inert subprocess; no " +
            "shell or caller-selected code is used. No existing customer resource is a target. " +
            "For UDP, Maya attempts synthetic send/receive traffic and reads a bounded " +
            "snapshot of existing Windows filtering events to identify its own rule drops. " +
            "Event collection must already be enabled; Maya does not enable or change it. " +
            "Missing events remain inconclusive. No complete event-loss accounting is available. " +
            "The screen reads ACL metadata on the runtime and System32 roots, not private " +
            "contents. Temporary links, endpoints, shared memory and fixture grants are " +
            "removed after confirmed stop; inert canaries and reports remain for inspection. " +
            "Any observed unauthorized effect fails the screen. Missing evidence, a timeout " +
            "or unavailable target is never a pass. All protections and the 30-second child " +
            "limit remain unchanged. A completed screen still does not qualify containment.\r\n\r\n" +
            "No registry permissions, loopback exemptions, firewall defaults, antivirus, " +
            "encryption, boot settings or Azure resources will be changed. " +
            "No models, connectors, credentials or customer files are used.\r\n\r\n" +
            "The trusted setup host needs administrator rights for these changes; Python " +
            "must still pass restricted-token checks. This first candidate does not qualify " +
            "standard-user setup. If startup or cleanup fails, stop and send the report. " +
            "Do not disable Windows protections. Closing Maya forcibly may leave cleanup " +
            "pending; reopen it and use Recover cleanup. No unrestricted fallback or retry occurs.";
#endif

        [STAThread]
        public static int Main(string[] args)
        {
            try
            {
                Native.ConfigureErrorMode();
                Native.Require(Native.SetDefaultDllDirectories(0x800), "system_dll_search");
                if (IntPtr.Size != 8) throw new StartupFailure("requires_x64");
                string user = WindowsIdentity.GetCurrent().User.Value;
                if (args.Length != 0 && (args.Length != 2 || args[0] != "--elevated" || args[1] != user))
                    throw new StartupFailure("elevation_identity_changed");
                Application.EnableVisualStyles();
                Application.SetCompatibleTextRenderingDefault(false);
                using (var window = new StartupWindow()) Application.Run(window);
                return 0;
            }
            catch (Exception error)
            {
                MessageBox.Show("Maya did not start Python. Reason: " + FailureCode(error),
                    "Maya protected Python", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return 1;
            }
        }

        internal static string FailureCode(Exception error)
        {
            var failure = error as StartupFailure;
            return failure != null ? failure.Message : "operation_failed_" + error.GetType().Name;
        }

        internal static void RecordStartupFailure(Dictionary<string, object> record, Exception error)
        {
            record["status"] = "blocked";
            record["reason_code"] = FailureCode(error);
            var failure = error as StartupFailure;
            if (failure != null && failure.TokenCheck != null) record["token_check_failure"] = failure.TokenCheck;
        }

        internal static string ExpectedBeacon(string run)
        {
            Guid parsed;
            if (run == null || run.Length != 32 || !Guid.TryParseExact(run, "N", out parsed)) throw new StartupFailure("invalid_attempt_id");
            foreach (char value in run)
                if (!(value >= '0' && value <= '9' || value >= 'a' && value <= 'f')) throw new StartupFailure("invalid_attempt_id");
            return "MAYA_PROTECTED_PYTHON_STARTED_V1:" + run + "\n";
        }

        internal static bool StartupComplete(uint exit, string output, bool freshState, string run)
        {
            return exit == 0 && freshState && output == ExpectedBeacon(run);
        }

        internal static void RecordChildEvidence(Dictionary<string, object> record, uint? exit,
            string stdout, int stderrBytes, bool captureComplete, string run)
        {
            bool known = captureComplete && stdout != null;
            record["output_capture_complete"] = known;
            record["child_stdout_bytes"] = known ? (object)stdout.Length : null;
            record["child_stderr_bytes"] = known ? (object)stderrBytes : null;
            record["stdout_beacon_matches"] = known ? (object)(stdout == ExpectedBeacon(run)) : null;
            // Never substitute the job's forced-termination code for a natural exit.
            record["child_exit_observed_before_cleanup"] = exit.HasValue;
            if (exit.HasValue) record["child_exit_hex"] = "0x" + exit.Value.ToString("X8");
        }

        static bool ReadFreshBeacon(string directory, string run)
        {
            string path = Path.Combine(directory, "state", "python-startup.txt");
            try { File.GetAttributes(path); }
            catch (FileNotFoundException) { return false; }
            catch (DirectoryNotFoundException) { return false; }
            ProductFiles.NoLinks(path);
            return new FileInfo(path).Length <= 256 && File.ReadAllText(path) == ExpectedBeacon(run);
        }

        internal static Dictionary<string, object> ReadRecord(string path)
        {
            ProductFiles.NoLinks(path);
            if (new FileInfo(path).Length > 65536) throw new StartupFailure("record_too_large");
            return new JavaScriptSerializer().Deserialize<Dictionary<string, object>>(File.ReadAllText(path));
        }

        internal static void SaveRecord(string path, object value)
        {
            string text = SerializeRecord(value);
            ProductFiles.NoLinks(Path.GetDirectoryName(path));
            string temporary = path + "." + Guid.NewGuid().ToString("N") + ".tmp";
            using (var file = new FileStream(temporary, FileMode.CreateNew, FileAccess.Write, FileShare.None))
            using (var writer = new StreamWriter(file, new System.Text.UTF8Encoding(false)))
            {
                writer.Write(text);
                writer.Flush(); file.Flush(true);
            }
            if (File.Exists(path)) { ProductFiles.NoLinks(path); File.Replace(temporary, path, null); }
            else File.Move(temporary, path);
        }
        internal static string SerializeRecord(object value)
        {
            string text = new JavaScriptSerializer().Serialize(value);
            if (System.Text.Encoding.UTF8.GetByteCount(text) > ContainmentEvidence.MaximumReportBytes)
                throw new StartupFailure("record_too_large");
            return text;
        }
        internal static void RecordStageFailure(Dictionary<string, object> record, string prefix, string stage, Exception error)
        {
            record[prefix + "_stage"] = stage;
            record[prefix + "_hresult"] = "0x" + error.HResult.ToString("X8");
        }

        internal static List<string> Pending()
        {
            var result = new List<string>();
            if (!Directory.Exists(ProductFiles.Root)) return result;
            ProductFiles.VerifyRoot();
            foreach (string directory in Directory.GetDirectories(ProductFiles.Root))
            {
                Guid id;
                if (!Guid.TryParseExact(Path.GetFileName(directory), "N", out id))
                    throw new StartupFailure("unexpected_product_directory");
                ProductFiles.NoLinks(directory);
                string journal = Path.Combine(directory, "attempt.json");
                if (!File.Exists(journal)) throw new StartupFailure("attempt_record_missing");
                var record = ReadRecord(journal);
                if ((string)record["operator_sid"] != WindowsIdentity.GetCurrent().User.Value)
                    throw new StartupFailure("other_operator_attempt_present");
                if (!record.ContainsKey("cleanup_complete") || !(bool)record["cleanup_complete"])
                    result.Add(directory);
            }
            return result;
        }

        internal static string Execute(bool recover, Action<string,int> publish = null)
        {
            if (!recover) Native.CheckBaseline();
            ProductFiles.EnsureRoot();
            string ownerLock = Path.Combine(ProductFiles.Root, "lifecycle.lock");
            ProductFiles.NoLinks(ownerLock);
            using (var lifecycle = new FileStream(ownerLock, FileMode.OpenOrCreate, FileAccess.ReadWrite, FileShare.None))
                return ExecuteOwned(recover, publish);
        }

        static string ExecuteOwned(bool recover, Action<string,int> publish)
        {
            var user = WindowsIdentity.GetCurrent().User;
            var pending = Pending();
            if (recover && pending.Count != 1) throw new StartupFailure("recovery_requires_one_pending_attempt");
            if (!recover && pending.Count != 0) throw new StartupFailure("cleanup_pending_use_recovery");
            string run = recover ? Path.GetFileName(pending[0]) : Guid.NewGuid().ToString("N");
            string directory = Path.Combine(ProductFiles.Root, run);
#if HERMES_BRIDGE
            if (recover) throw new StartupFailure("bridge_recovery_requires_review");
#endif
            string moniker = "Maya.ProtectedPython.Startup1." + run;
            Dictionary<string, object> record;
            if (recover)
            {
                record = ReadRecord(Path.Combine(directory, "attempt.json"));
                if ((string)record["version"] != Version || (string)record["scope"] != Scope ||
                    (string)record["profile"] != moniker) throw new StartupFailure("recovery_record_mismatch");
                if (record.ContainsKey("profile_collision") && (bool)record["profile_collision"])
                    throw new StartupFailure("profile_collision_requires_review_not_deletion");
                int pid = Convert.ToInt32(record["host_pid"]);
                long ticks = Convert.ToInt64(record["host_start_ticks"]);
                try
                {
                    using (var prior = Process.GetProcessById(pid))
                        if (!prior.HasExited && prior.StartTime.ToUniversalTime().Ticks == ticks)
                            throw new StartupFailure("close_previous_maya_window_before_recovery");
                }
                catch (ArgumentException) { }
            }
            else
            {
                ProductFiles.CreateAttempt(directory, user);
                using (var host = Process.GetCurrentProcess())
                    record = new Dictionary<string, object> {
                        {"schema", "maya.protected_python.startup.v1"}, {"version", Version}, {"scope", Scope},
                        {"isolation_mode", "appcontainer-wfp"},
                        {"operator_sid", user.Value}, {"profile", moniker}, {"attempt_id", run},
                        {"host_pid", host.Id}, {"host_start_ticks", host.StartTime.ToUniversalTime().Ticks},
                        {"os_build", "26300.9711"}, {"host_elevated", true}, {"informed_consent", true},
                        {"python_version", "3.13.14"}, {"python_started", false}, {"child_resumed", false},
                        {"cleanup_complete", false}, {"production_qualified", false}, {"containment_qualified", false},
                        {"status", "preparing"}, {"created_utc", DateTime.UtcNow.ToString("o")},
                        {"launcher_sha256", ProductFiles.HashFile(Assembly.GetExecutingAssembly().Location)}
                    };
            }
            string recordPath = Path.Combine(directory, "attempt.json");
#if HERMES_MODEL
            record["real_inference"] = false;
#if HERMES_MODEL_FINAL
            record["model_case"] = "M08";
            record["model_mutation_origin"] = "trusted_fixed_coordinator_diagnostic";
            record["model_pending_cases"] = new[] {"M09"};
#elif HERMES_MODEL_ALLOWLIST
            record["model_case"] = "M07c";
            record["model_pending_cases"] = new[] {"M08","M09"};
#elif HERMES_MODEL_OVERSIZED
            record["model_case"] = "M07b";
            record["model_pending_cases"] = new[] {"M07c","M08","M09"};
#elif HERMES_MODEL_MALFORMED
            record["model_case"] = "M07a";
            record["model_pending_cases"] = new[] {"M07b","M07c","M08","M09"};
#elif HERMES_MODEL_OUTPUT_DENY
            record["model_case"] = "M06";
            record["model_pending_cases"] = new[] {"M07","M08","M09"};
#elif HERMES_MODEL_RECREATE
            record["model_case"] = "M05b";
            record["model_pending_cases"] = new[] {"M06","M07","M08","M09"};
#elif HERMES_MODEL_BUDGET
            record["model_case"] = "M05a";
            record["model_pending_cases"] = new[] {"M05b","M06","M07","M08","M09"};
#elif HERMES_MODEL_REPLAY
            record["model_case"] = "M04c";
            record["model_pending_cases"] = new[] {"M05","M06","M07","M08","M09"};
#elif HERMES_MODEL_REVOKE
            record["model_case"] = "M04b";
            record["model_pending_cases"] = new[] {"M04c","M05","M06","M07","M08","M09"};
#elif HERMES_MODEL_EXPIRY
            record["model_case"] = "M04a";
            record["model_pending_cases"] = new[] {"M04b","M04c","M05","M06","M07","M08","M09"};
#elif HERMES_MODEL_BODY
            record["model_case"] = "M03d";
            record["model_pending_cases"] = new[] {"M04","M05","M06","M07","M08","M09"};
            record["model_mutation_origin"] = "trusted_fixed_coordinator_diagnostic";
#elif HERMES_MODEL_ATTEMPT
            record["model_case"] = "M03c";
            record["model_pending_cases"] = new[] {"M03d","M04","M05","M06","M07","M08","M09"};
            record["model_mutation_origin"] = "trusted_fixed_coordinator_diagnostic";
#elif HERMES_MODEL_ROUTE
            record["model_case"] = "M03b";
            record["model_pending_cases"] = new[] {"M03c","M03d","M04","M05","M06","M07","M08","M09"};
            record["model_mutation_origin"] = "trusted_fixed_coordinator_diagnostic";
#elif HERMES_MODEL_VALIDATION
            record["model_case"] = "M03a";
            record["model_pending_cases"] = new[] {"M03b","M03c","M03d","M04","M05","M06","M07","M08","M09"};
            record["model_mutation_origin"] = "trusted_fixed_coordinator_diagnostic";
#elif HERMES_MODEL_DENY
            record["model_case"] = "M02";
            record["model_pending_cases"] = new[] {"M03","M04","M05","M06","M07","M08","M09"};
#else
            record["model_case"] = "M01";
            record["model_pending_cases"] = new[] {"M02","M03","M04","M05","M06","M07","M08","M09"};
#endif
#endif
            SaveRecord(recordPath, record);
            var isolation = new WindowsIsolation(moniker);
            var screen = new ContainmentScreen(directory, run, isolation.Package, user);
            var observations = new Dictionary<string, string>(StringComparer.Ordinal);
            record["security_resource_inventory"] = isolation.ResourceInventory();
            bool cleanup = false;
#if HERMES_JOURNAL_ACCESS
            JournalAccessRuntime bridge = null;
#elif HERMES_MODEL
            ModelBridgeRuntime bridge = null;
#elif HERMES_BRIDGE
            BridgeRuntime bridge = null;
#endif
            try
            {
                if (!recover)
                {
                    screen.Stage = "payload_extract";
                    ProductFiles.ExtractPayload(directory);
                    record["payload_verified"] = true;
                    screen.Stage = "profile_create";
                    isolation.CreateProfile();
                    screen.Stage = "file_grants";
                    ProductFiles.Grant(directory, isolation.Package, user);
#if HERMES_JOURNAL_ACCESS
                    record["real_inference"] = false;
                    record["independent_cleanup_verified"] = false;
#elif HERMES_MODEL
                    HermesImport.Prepare(directory);
                    File.Copy(Path.Combine(directory,"runtime","model-config.json"),Path.Combine(directory,"state","config.yaml"),false);
#elif HERMES_MEMORY
                    HermesMemory.Prepare(directory);
#elif HERMES_CONSTRUCTION
                    HermesConstruction.Prepare(directory);
#elif HERMES_IMPORT
                    HermesImport.Prepare(directory);
#else
                    screen.Prepare();
#endif
                    screen.Stage = "network_provision";
                    isolation.ProvisionNetwork();
                    record["network_filters_verified"] = 6;
#if HERMES_BRIDGE
                    screen.Stage = "bridge_worker_setup";
#if HERMES_JOURNAL_ACCESS
                    bridge = new JournalAccessRuntime(directory, run, user, record);
#elif HERMES_MODEL
                    record["real_inference"] = false;
                    bridge = new ModelBridgeRuntime(directory, run, user, record, publish);
#else
                    bridge = new BridgeRuntime(directory, run, user, record);
#endif
                    bridge.PrepareWorker();
#endif
#if !HERMES_IMPORT
                    screen.Stage = "udp_evidence_setup";
                    screen.ConfigureUdp(isolation, record);
#endif
                    screen.Stage = "child_create_suspended";
                    isolation.Start(directory, run, user);
                    screen.BindChild(checked((int)isolation.ChildPid));
#if !HERMES_IMPORT
                    screen.Stage = "plan_write";
                    screen.WritePlan(isolation.StandardHandles);
                    record["screen_fixture_inventory"] = screen.Plan;
                    screen.Stage = "acl_inventory";
                    record["screen_acl_metadata_inventory"] = screen.AclInventory();
#endif
                    record["restricted_token_verified"] = true;
                    record["child_pid"] = isolation.ChildPid;
                    record["status"] = "restricted_child_suspended";
                    screen.Stage = "suspended_record_write";
                    SaveRecord(recordPath, record);
                    screen.Stage = "child_resume_wait";
#if HERMES_JOURNAL_ACCESS
                    bridge.Run(isolation);
                    record["child_resumed"] = isolation.Resumed;
#elif HERMES_BRIDGE
                    uint exit = bridge.Run(isolation);
                    record["child_resumed"] = true;
                    record["child_exit_hex"] = "0x" + exit.ToString("X8");
                    record["fresh_state_beacon"] = ReadFreshBeacon(directory, run);
#if HERMES_MODEL
                    record["python_started"] = exit == 0 && (bool)record["fresh_state_beacon"] &&
                        record.ContainsKey("model_python_entry_observed") && true.Equals(record["model_python_entry_observed"]);
                    record["status"] = ModelFinalAdmission.Enabled ? "offline_model_final_text_rejection_child_completed" : ModelAllowlistAdmission.Enabled ? "offline_model_response_allowlist_rejection_child_completed" : ModelOversizedAdmission.Enabled ? "offline_model_response_size_rejection_child_completed" : ModelMalformedAdmission.Enabled ? "offline_model_response_json_rejection_child_completed" : ModelOutputDenialAdmission.Enabled ? "offline_model_runtime_output_denial_child_completed" : ModelRecreateAdmission.Enabled ? "offline_model_recreated_client_budget_child_completed" :
                        ModelBudgetAdmission.Enabled ? "offline_model_adapter_budget_child_completed" :
                        ModelReplayAdmission.Enabled ? "offline_model_replay_child_completed" :
                        ModelValidationAdmission.Enabled ? "offline_model_validation_child_completed" :
                        ModelDenialAdmission.Enabled ? "offline_model_denial_child_completed" : "offline_model_child_completed";
#else
                    record["python_started"] = exit == 0 && (bool)record["fresh_state_beacon"] &&
                        record.ContainsKey("bridge_python_entry_observed") && true.Equals(record["bridge_python_entry_observed"]);
                    record["status"] = "bridge_child_completed";
#endif
#else
                    uint exit = isolation.ResumeAndWait();
                    record["child_resumed"] = true;
                    screen.Stage = "child_startup_evidence";
                    RecordChildEvidence(record, exit, isolation.Stdout, isolation.StderrBytes,
                        isolation.OutputCaptureComplete, run);
                    bool beacon = ReadFreshBeacon(directory, run);
                    record["fresh_state_beacon"] = beacon;
                    record["python_entry_observed"] = beacon && isolation.OutputCaptureComplete && isolation.Stdout == ExpectedBeacon(run);
                    record["python_started"] = StartupComplete(exit, isolation.Stdout, beacon, run);
                    record["status"] = (bool)record["python_started"] ? "startup_completed_not_containment_qualified" : "startup_failed";
#endif
                }
            }
            catch (Exception error)
            {
                RecordStartupFailure(record, error);
                RecordStageFailure(record, "screen_failure", screen.Stage, error);
                record["profile_collision"] = isolation.ProfileCollision;
                record["child_resumed"] = isolation.Resumed;
                if (isolation.ExitCode.HasValue) record["child_exit_hex"] = "0x" + isolation.ExitCode.Value.ToString("X8");
            }
            finally
            {
                if (!recover) record["reduced_launch_token_verified"] = isolation.ReducedLaunchTokenVerified;
                if (!recover) record["startup_status"] = record["status"];
                // Keep durable network denies and grants if stopping the job is uncertain.
                try
                {
                    screen.Stage = "job_stop";
                    isolation.Stop();
#if HERMES_BRIDGE
                    if (bridge != null) bridge.Stop();
#endif
#if !HERMES_JOURNAL_ACCESS
                    if (!recover && isolation.Resumed && (string)record["startup_status"] == "blocked")
                    {
                        try
                        {
                            RecordChildEvidence(record, isolation.ExitCode, isolation.Stdout, isolation.StderrBytes,
                                isolation.OutputCaptureComplete, run);
                            record["evidence_phase"] = "after_job_stop";
                            record["fresh_state_beacon"] = null;
                            record["fresh_state_beacon"] = ReadFreshBeacon(directory, run);
                        }
                        catch (Exception error) { record["evidence_reason_code"] = FailureCode(error); }
                    }
                    if (!recover && isolation.Resumed)
                    {
                        try {
#if HERMES_MODEL
                            record["model_evidence_collected"] = true;
#elif HERMES_BRIDGE
                            record["bridge_evidence_collected"] = true;
#elif HERMES_MEMORY
                            screen.Stage = "hermes_memory_report";
                            HermesMemory.Collect(directory, run, record);
#elif HERMES_STATE
                            screen.Stage = "hermes_state_report";
                            HermesState.Collect(directory, run, record);
#elif HERMES_CONSTRUCTION
                            screen.Stage = "hermes_construction_report";
                            HermesConstruction.Collect(directory, run, record);
#elif HERMES_IMPORT
                            screen.Stage = "hermes_import_report";
                            HermesImport.Collect(directory, run, record);
#else
                            observations = screen.Collect(record);
#endif
                        }
                        catch (Exception error)
                        {
                            record["screen_evidence_reason_code"] = FailureCode(error);
                            RecordStageFailure(record, "screen_evidence_failure", screen.Stage, error);
                            screen.RecordNetworkEvidence(record);
                            if (record.ContainsKey("screen_host_unauthorized_network_effect") && (bool)record["screen_host_unauthorized_network_effect"] ||
                                record.ContainsKey("screen_host_postconditions") && !(bool)record["screen_host_postconditions"])
                                observations["host.effect"] = "failed";
                        }
                    }
#endif
                    screen.Cleanup();
                    screen.Stage = "file_grant_revocation";
                    ProductFiles.Revoke(directory, isolation.Package);
                    screen.Stage = "profile_delete";
                    isolation.DeleteProfile();
                    screen.Stage = "network_remove";
                    isolation.RemoveNetwork();
                    cleanup = true;
                    screen.Stage = "cleanup_complete";
                }
                catch (Exception error)
                {
                    record["cleanup_reason_code"] = FailureCode(error);
                    RecordStageFailure(record, "screen_cleanup_failure", screen.Stage, error);
                }
                record["screen_last_stage"] = screen.Stage;
                isolation.Dispose();
#if HERMES_BRIDGE
                if (bridge != null) bridge.Dispose();
#endif
                record["cleanup_complete"] = cleanup;
                if (!recover)
                {
#if HERMES_JOURNAL_ACCESS
                    record["status"] = JournalAccessRuntime.FinalStatus(record, cleanup);
#elif HERMES_MODEL
                    record["status"] = cleanup && true.Equals(record["python_started"]) &&
                        record.ContainsKey("model_evidence_matches") && true.Equals(record["model_evidence_matches"]) &&
                        record.ContainsKey("model_worker_stopped") && true.Equals(record["model_worker_stopped"])
                        ? (ModelFinalAdmission.Enabled ?
                            (record.ContainsKey("model_final_text_evidence_matches") && true.Equals(record["model_final_text_evidence_matches"])
                            ? "offline_model_final_text_rejected_pending_independent_cleanup" : "blocked") : ModelAllowlistAdmission.Enabled ?
                            (record.ContainsKey("model_allowlist_evidence_matches") && true.Equals(record["model_allowlist_evidence_matches"])
                            ? "offline_model_response_allowlist_rejected_pending_independent_cleanup" : "blocked") : ModelOversizedAdmission.Enabled ?
                            (record.ContainsKey("model_oversized_evidence_matches") && true.Equals(record["model_oversized_evidence_matches"])
                            ? "offline_model_response_size_rejected_pending_independent_cleanup" : "blocked") : ModelMalformedAdmission.Enabled ?
                            (record.ContainsKey("model_malformed_evidence_matches") && true.Equals(record["model_malformed_evidence_matches"])
                            ? "offline_model_response_json_rejected_pending_independent_cleanup" : "blocked") : ModelOutputDenialAdmission.Enabled ?
                            (record.ContainsKey("model_output_denial_evidence_matches") && true.Equals(record["model_output_denial_evidence_matches"])
                            ? "offline_model_runtime_output_denied_pending_independent_cleanup" : "blocked") : ModelRecreateAdmission.Enabled ?
                            (record.ContainsKey("model_recreate_evidence_matches") && true.Equals(record["model_recreate_evidence_matches"])
                            ? "offline_model_recreated_client_budget_rejected_pending_independent_cleanup" : "blocked") : ModelBudgetAdmission.Enabled ?
                            (record.ContainsKey("model_adapter_budget_evidence_matches") && true.Equals(record["model_adapter_budget_evidence_matches"])
                            ? "offline_model_adapter_budget_rejected_pending_independent_cleanup" : "blocked") : ModelReplayAdmission.Enabled ?
                            (record.ContainsKey("model_replay_evidence_matches") && true.Equals(record["model_replay_evidence_matches"])
                            ? "offline_model_lease_replay_rejected_pending_independent_cleanup" : "blocked") : ModelRevocationAdmission.Enabled ?
                            (record.ContainsKey("model_revocation_evidence_matches") && true.Equals(record["model_revocation_evidence_matches"])
                            ? "offline_model_lease_revoked_pending_independent_cleanup" : "blocked") : ModelExpiryAdmission.Enabled ?
                            (record.ContainsKey("model_expiry_evidence_matches") && true.Equals(record["model_expiry_evidence_matches"])
                            ? "offline_model_lease_expired_pending_independent_cleanup" : "blocked") : ModelBodyAdmission.Enabled ?
                            (record.ContainsKey("model_body_evidence_matches") && true.Equals(record["model_body_evidence_matches"])
                            ? "offline_model_body_rejected_pending_independent_cleanup" : "blocked") : ModelAttemptAdmission.Enabled ?
                            (record.ContainsKey("model_attempt_evidence_matches") && true.Equals(record["model_attempt_evidence_matches"])
                            ? "offline_model_attempt_rejected_pending_independent_cleanup" : "blocked") : ModelRouteAdmission.Enabled ?
                            (record.ContainsKey("model_route_evidence_matches") && true.Equals(record["model_route_evidence_matches"])
                            ? "offline_model_route_rejected_pending_independent_cleanup" : "blocked") : ModelValidationAdmission.Enabled ?
                            (record.ContainsKey("model_validation_evidence_matches") && true.Equals(record["model_validation_evidence_matches"])
                            ? "offline_model_validation_rejected_pending_independent_cleanup" : "blocked") : ModelDenialAdmission.Enabled ?
                            (record.ContainsKey("model_denial_evidence_matches") && true.Equals(record["model_denial_evidence_matches"])
                            ? "offline_model_egress_denied_pending_independent_cleanup" : "blocked") :
                            "offline_model_wire_completed_pending_independent_cleanup") : "blocked";
                    record["independent_cleanup_verified"] = false;
#elif HERMES_BRIDGE
                    record["status"] = cleanup && true.Equals(record["python_started"]) &&
                        record.ContainsKey("bridge_evidence_matches") && true.Equals(record["bridge_evidence_matches"]) &&
                        record.ContainsKey("bridge_worker_stopped") && true.Equals(record["bridge_worker_stopped"])
                        ? "bridge_document_completed_pending_independent_cleanup" : "blocked";
                    record["independent_cleanup_verified"] = false;
#elif HERMES_MEMORY
                    record["hermes_memory_status"] = HermesMemory.Result(record, cleanup);
                    record["status"] = record["hermes_memory_status"];
                    record["independent_cleanup_verified"] = false;
#elif HERMES_STATE
                    record["hermes_state_status"] = HermesState.Result(record, cleanup);
                    record["status"] = record["hermes_state_status"];
                    record["independent_cleanup_verified"] = false;
#elif HERMES_CONSTRUCTION
                    record["hermes_construction_status"] = HermesConstruction.Result(record, cleanup);
                    record["status"] = record["hermes_construction_status"];
                    record["independent_cleanup_verified"] = false;
#elif HERMES_IMPORT
                    record["hermes_import_status"] = HermesImport.Result(record, cleanup);
                    record["status"] = record["hermes_import_status"];
                    record["independent_cleanup_verified"] = false;
#else
                    if (!isolation.ExitCode.HasValue || isolation.ExitCode.Value != 0 ||
                        !record.ContainsKey("python_started") || !(bool)record["python_started"])
                        observations["execution.incomplete"] = "inconclusive";
                    record["screen_status"] = ContainmentScreen.Finish(observations, cleanup);
                    if ((string)record["screen_status"] == "screen_completed_not_containment_qualified")
                        record["screen_status"] = "observations_completed_pending_independent_cleanup";
                    record["screen_observations"] = observations;
                    record["screen_independent_cleanup_verified"] = false;
                    record["status"] = record["screen_status"];
#endif
                }
                if (!recover) record["finished_utc"] = DateTime.UtcNow.ToString("o");
                if (recover && cleanup)
                {
                    record["recovery_completed"] = true;
                    record["recovery_utc"] = DateTime.UtcNow.ToString("o");
                    record["status"] = record.ContainsKey("startup_status") ? record["startup_status"] : "security_cleanup_recovered";
                }
                if (!cleanup) record["status"] = "cleanup_pending_stop";
                SaveRecord(recordPath, record);
            }
            return recordPath;
        }
    }

    internal sealed class TokenCheckFailure
    {
        public string check { get; private set; }
        public int information_class { get; private set; }
        public uint expected { get; private set; }
        public uint observed { get; private set; }

        internal TokenCheckFailure(string name, int type, uint required, uint actual)
        { check = name; information_class = type; expected = required; observed = actual; }
    }

    internal sealed class StartupFailure : Exception
    {
        internal TokenCheckFailure TokenCheck { get; private set; }
        internal StartupFailure(string code) : base(code) { }
        internal StartupFailure(string code, TokenCheckFailure detail) : base(code) { TokenCheck = detail; }
    }

    internal sealed class StartupWindow : Form
    {
#if HERMES_MODEL
        readonly TextBox modelOutput = new TextBox { ReadOnly=true, Multiline=true, Dock=DockStyle.Fill, ScrollBars=ScrollBars.Vertical };
#endif
        readonly CheckBox consent = new CheckBox();
        readonly Button start = new Button(), recover = new Button(), reports = new Button();
        readonly Label status = new Label();
        bool active;
        string reportPath;
        readonly bool administrator;

        internal StartupWindow()
        {
            administrator = new WindowsPrincipal(WindowsIdentity.GetCurrent()).IsInRole(WindowsBuiltInRole.Administrator);
            Text = "Maya | Protected Python startup"; Font = new Font("Segoe UI", 9);
            AutoScaleMode = AutoScaleMode.Dpi; ClientSize = new Size(700, 660);
#if HERMES_MODEL
            Text = "Maya | Offline model bridge";ClientSize = new Size(700,720);
#endif
            MinimumSize = new Size(650, 620); StartPosition = FormStartPosition.CenterScreen;
            var layout = new TableLayoutPanel { Dock = DockStyle.Fill, ColumnCount = 1, RowCount = 5, Padding = new Padding(18) };
#if HERMES_MODEL
            layout.RowCount=6;
#endif
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 42));
            layout.RowStyles.Add(new RowStyle(SizeType.Percent, 100));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 50));
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 45));
#if HERMES_MODEL
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 60));
#endif
            layout.RowStyles.Add(new RowStyle(SizeType.Absolute, 85));
#if HERMES_MODEL
            layout.Controls.Add(new Label { Text = "Maya offline model bridge", Font = new Font(Font.FontFamily, 18), Dock = DockStyle.Fill }, 0, 0);
#else
            layout.Controls.Add(new Label { Text = "Maya protected Python", Font = new Font(Font.FontFamily, 18), Dock = DockStyle.Fill }, 0, 0);
#endif
            layout.Controls.Add(new TextBox { Text = ProtectedPython.Consent, Multiline = true, ReadOnly = true,
                ScrollBars = ScrollBars.Vertical, Dock = DockStyle.Fill, BackColor = Color.White }, 0, 1);
            consent.Text = "I approve the changes described above for this VM attempt.";
            consent.Dock = DockStyle.Fill; layout.Controls.Add(consent, 0, 2);
            var buttons = new FlowLayoutPanel { Dock = DockStyle.Fill, WrapContents = false };
            start.Text = administrator ? "Start protected Python" : "Open setup";
            start.AutoSize = true; start.Enabled = false;
            recover.Text = "Recover cleanup"; recover.AutoSize = true; recover.Enabled = false;
            reports.Text = "Open results"; reports.AutoSize = true; reports.Enabled = false;
            buttons.Controls.Add(start); buttons.Controls.Add(recover); buttons.Controls.Add(reports);
            layout.Controls.Add(buttons, 0, 3);
            status.Dock = DockStyle.Fill; status.Text = "No security changes made. Prepared for Windows 11 Pro build 26300.9711 only.";
#if HERMES_MODEL
            layout.Controls.Add(modelOutput,0,4);layout.Controls.Add(status,0,5);
#else
            layout.Controls.Add(status, 0, 4);
#endif
            Controls.Add(layout);
            consent.CheckedChanged += delegate { if (!active) { start.Enabled = consent.Checked; recover.Enabled = consent.Checked; } };
            start.Click += async delegate { await Run(false); };
            recover.Click += async delegate { await Run(true); };
            reports.Click += delegate { Process.Start(new ProcessStartInfo(Path.GetDirectoryName(reportPath)) { UseShellExecute = true }); };
            FormClosing += delegate(object sender, FormClosingEventArgs e) { if (active) { e.Cancel = true; status.Text = "Finishing startup and security cleanup. Please wait."; } };
        }

        async Task Run(bool cleanup)
        {
            if (!consent.Checked || active) return;
            start.Enabled = recover.Enabled = consent.Enabled = false;
            if (!administrator)
            {
                try
                {
                    if (cleanup) throw new StartupFailure("open_setup_then_select_recover_cleanup");
                    string user = WindowsIdentity.GetCurrent().User.Value;
                    using (Process.Start(new ProcessStartInfo(Assembly.GetExecutingAssembly().Location,
                        "--elevated " + user) { UseShellExecute = true, Verb = "runas" })) { }
                    Close();
                }
                catch (Win32Exception error)
                { status.Text = error.NativeErrorCode == 1223 ? "Administrator approval cancelled. Python was not started." : "Setup did not open. No security setup attempted."; }
                catch (Exception error) { status.Text = ProtectedPython.FailureCode(error); }
                return;
            }
            active = true; status.Text = cleanup ? "Removing this product's pending security setup..." : "Preparing and starting protected Python...";
            try
            {
#if HERMES_MODEL
                modelOutput.Clear();
                reportPath = await Task.Run(() => ProtectedPython.Execute(cleanup, PublishModelOutput));
#else
                reportPath = await Task.Run(() => ProtectedPython.Execute(cleanup));
#endif
                var record = ProtectedPython.ReadRecord(reportPath);
                string outcome = (string)record["status"];
                string description = !(bool)record["cleanup_complete"] ? "Cleanup needs attention. Stop here; do not run Python again." :
                    cleanup ? "Security cleanup completed. Python was not launched again." :
#if HERMES_JOURNAL_ACCESS
                    outcome == "access_matrix_denied_pending_independent_cleanup" ?
                    "Both journal access probes reported complete denials. Independent cleanup checks are still required." :
                    "The journal access test was blocked.";
#else
#if HERMES_MODEL
                    outcome == "offline_model_lease_replay_rejected_pending_independent_cleanup" ? "M04c replay rejected after one synthetic dispatch/runtime delivery. No operator output was published." :
                    outcome == "offline_model_lease_revoked_pending_independent_cleanup" ? "M04b unused unexpired-grant revocation verified before any gateway call. No model output was released." :
                    outcome == "offline_model_lease_expired_pending_independent_cleanup" ? "M04a unused-grant expiry verified before any gateway call. No model output was released." :
                    outcome == "offline_model_body_rejected_pending_independent_cleanup" ? "M03d exact-body validation verified before any gateway call. No model output was released." :
                    outcome == "offline_model_attempt_rejected_pending_independent_cleanup" ? "M03c worker attempt binding verified before any gateway call. No model output was released." :
                    outcome == "offline_model_route_rejected_pending_independent_cleanup" ? "M03b worker route validation verified before any gateway call. No model output was released." :
                    outcome == "offline_model_validation_rejected_pending_independent_cleanup" ? "M03a worker validation verified before any gateway call. No model output was released." :
                    outcome == "offline_model_egress_denied_pending_independent_cleanup" ? "M02 gateway denial verified. No model request was dispatched and no model output was released." :
                    outcome == "offline_model_wire_completed_pending_independent_cleanup" ? "Offline model-wire test completed with a synthetic response. No inference occurred." :
#endif
                    outcome == "startup_completed_not_containment_qualified" ? "Python completed startup. Containment is not yet qualified." :
                    "Python did not complete startup.";
#endif
                status.Text = description + "\r\n" +
                    (record.ContainsKey("child_exit_hex") ? "Python exit: " + record["child_exit_hex"] + ". " : "") +
                    "Cleanup complete: " + record["cleanup_complete"] + ".\r\n" + reportPath;
                reports.Enabled = true;
            }
            catch (Exception error) { status.Text = "Python was not started again. Reason: " + ProtectedPython.FailureCode(error); }
            finally { active = false; }
        }
#if HERMES_MODEL
        void PublishModelOutput(string text, int milliseconds)
        {
            if(text==null || System.Text.Encoding.UTF8.GetByteCount(text)>1024)throw new StartupFailure("model_operator_output_size");
            ModelPublication.Run(action=>BeginInvoke(action),delegate {
                modelOutput.Text=text;modelOutput.Update();
                if(modelOutput.Text!=text)throw new StartupFailure("model_operator_readback");
            },milliseconds);
        }
#endif
    }
}
