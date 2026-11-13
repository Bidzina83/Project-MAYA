# Maya Project Reset Demo

**Decision:** Is there enough evidence to invest in a governed Windows product?
This milestone is not a production release or a containment qualification.

## Starting Point

Prior tests demonstrated bundled Python startup under AppContainer, an
offline authorized document release, and a native Hermes SDK exchange with a
synthetic response. They did not demonstrate one useful operator workflow
with real inference and independently verified authorization. The journal
probe remains blocked; retain its evidence and do not build another successor
as part of this milestone.

## Conditions and Actions

| Condition | Action | Required evidence |
| --- | --- | --- |
| C1. Safe scope before using a real provider | Trace the selected document, exact approved request, response, and audit record. Confirm that only the trusted broker holds the credential and can send provider traffic. Exclude tools, connectors, memory writes, retries, and background requests. Explicitly decide whether this demo depends on the unresolved journal guarantee. | Reviewed data flow, allowlisted synthetic input, named authorization and egress checks, and an explicit go/no-go for real traffic. |
| C2. Runs on ordinary Windows | Package the smallest usable flow with the bundled runtime. Test on a clean Windows setup without a separate Python install, Docker, or a VM dependency. Record any elevation or manual setup. | Another person can launch the demo from the instructions and reach the approval screen. Any elevation is disclosed; developer-only repair is not an acceptable setup step. |
| C3. Approval controls dispatch | Show the operator which synthetic document content will be sent and to which provider/model. Bind approval to that request. Exercise approval, denial, and request alteration after approval. Start with an instrumented synthetic endpoint. | One approved dispatch; zero denied or altered dispatches. Verify independently at the endpoint or trusted transport, not just in the UI. A failure must never silently retry or publish a result. |
| C4. Produces a useful answer | After C1-C3 pass, run one approved real inference on a short synthetic document with known answers. Display the response and its supporting excerpts. Repeat with a different synthetic fixture and exercise one real-provider denial path with trusted transport observation. | An operator verifies the answer against the document and can tell which request was authorized. The approved runs each dispatch once; the denied run dispatches zero times. |
| C5. Leaves evidence an operator can check | Correlate approval or denial, dispatch, and result using one request identifier. Show the evidence alongside the result; do not log credentials or claim the demo log is crash-durable. | A reviewer can distinguish approved, denied, and failed runs without trusting a success banner or reading raw diagnostics. |

## Decision Points

- **DP1, before real traffic:** If C1 cannot be established, stay offline.
  If the unresolved journal guarantee is essential to this workflow, redesign
  the evidence path or pick a workflow that does not depend on it. Otherwise
  record the journal guarantee as an open release requirement, not a waiver.
- **DP2, before expanding scope:** If C2 fails, simplify packaging or reconsider
  the runtime split. If C3 fails, stop real-provider work and fix or simplify
  the broker boundary. A useful answer cannot compensate for an unauthorized
  dispatch.
- **DP3, investment decision:** If C1-C5 pass, continue with one next workflow.
  If governance works but the answer is not useful, change the workflow before
  investing in infrastructure. If the required isolation or authorization
  cannot be demonstrated in this bounded design, redesign or pause investment.

## Stop Rule

Agree on a timebox before implementation. If two attempts at the same condition
fail without evidence that changes the next decision, stop and call it out.
Record the observed result and choose a simpler route, a redesigned test, or a
pause. Do not queue another diagnostic build by default.

**First implementation slice:** one synthetic document, one question, an
approval screen, an instrumented synthetic endpoint, and a result/evidence
view. Build the approved and denied paths together. No real provider until DP1
and the offline dispatch checks pass.
