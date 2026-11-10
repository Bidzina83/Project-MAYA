# Fixed Role Entry And Handshake Source Review

Approved source and inert checks completed 2026-11-10. The fixed Python worker
and child wrappers load only the named sibling role module and bind literal
roles. They are not admitted by any payload or selected by any launcher.
See `maya_final_output_actual_token_root_entry_review.md` for the design.

The shared handshake verifies the expected Python version/flags, one attempt
argument, fixed entry layout, role working directory and local PID. It accepts
one exact v2 challenge on the private framed input and requires EOF before
constructing the Windows backend. It binds the validated request ID to the
single-use session and emits exactly one bounded reply. Invalid or trailing
input rejects before opens; short output fails without a retry. No traceback
or raw exception is sent. Exit zero means completed framing, not access pass.

47 injected Python tests passed, including preflight/argument/path checks,
malformed/partial/extra input, missing EOF, fresh challenge, short output and
fixed literal roles and helper path. Wrappers were inspected as AST, not
executed. The existing C# v2 admission accepted 20 Python handshake-generated
frames with the expected outcomes (61 assertions); 692 v2, 399 v1 and 108
focused Python regressions passed. Existing pytest cache_dir warning only.

No backend call, launcher selector, allowlist entry, profile, provisioning,
package or VM run. Runtime module origin and actual private pipe, EOF,
process/token and physical path evidence remain future coordinator obligations.
Next: freeze and review the exact compile combination, three root admissions,
control inventory and lifecycle integration before source wiring. Final3 stays
blocked and qualification flags remain unchanged.
