# Python Token-Access Role Source Review

Approved disconnected source and inert parity checks completed 2026-11-10.
`src/project_maya/windows_runtime/journal_access_role.py` has no executable
entry or launcher route. It does not load a Windows DLL at import. No role
wrapper, payload allowlist, synthetic provisioning or package was changed.

The module accepts a trusted attempt directory, fixed role, PID and challenge.
It validates the exact v2 command once, constructs the reviewed fixed paths,
and issues only exact-mask open/identity/close calls through an adapter. It
lexically validates the Windows path without reading protected target metadata
at bootstrap. This does not replace the coordinator's opened-object checks.
The native binding captures last-error at failed open/query and queries the
same exact-mask handle. It attempts close once after every successful open;
query or close failure cannot turn an open into a denial. No content access,
mutation, arbitrary command path, retry or extra rights.

22 Python tests passed, including both roles, fixed path/flag/mask checks,
single-use invalid command handling, bounded private-frame round-trip and
injected native call/error ordering. 20 Python-generated framed vectors passed
the existing C# v2 admission gate with 61 assertions, including forbidden opens
with unavailable identity/close, incomplete controls and replay rejection.
Prior 692 v2 and 399 v1 assertions, compile exclusions and 108 focused Python
regressions passed. Existing pytest cache_dir warning remains. No real Windows
backend call, worker, child, native probe or VM execution occurred.

Before source wiring, review fixed root wrappers, how the trusted channel
challenge binds the role session, exact compile combination and synthetic
inventory. No payload assembly, permission changes, native qualification or
actual token-access conclusion follows from parity. Final3 stays blocked.
