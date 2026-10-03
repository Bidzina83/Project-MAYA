# Pre-G1 Security Checkpoint

## Approved Order And Status

The user approved this checkpoint on 2026-10-03 before G1:

1. Verify the 28 CodeQL review items against the exact patched Hermes source and
   identify product reachability.
2. Fix reachable credential disclosure and security-sensitive endpoint checks;
   fix or explicitly block the native search expression.
3. Document the 29 metadata false positives individually, preserving upstream
   fixture provenance and without blanket scanner exclusions.
4. Resume G1 only after the checkpoint acceptance below passes.

G1 remains held. Implementation is a source-only security candidate, not an
accepted production runtime. No alert has been dismissed. No wheel, installer,
runtime pin, capability marker or production activation guard has changed.

## Source And Alert Dispositions

All 57 GitHub alerts (#54-#110) were read at Maya commit
`99733930086b863f99bda943873fa64d47a490b9`; all instances cite test snapshots.
The frozen snapshots are excluded from the Maya wheel, but mirror native Hermes
code at pin `b13e2fd6948a59eeb59fe618914147d97a2ee90a`. Therefore fixture-only
locations do not establish runtime safety. They remain immutable.

The [individual disposition register](codeql-security-disposition-20261003.json)
accounts for every input, without deduplication:

- 27 receive a source-candidate fix through Patch 24: 10 endpoint predicates,
  14 conditional URL diagnostic claims, two credential-fragment displays and
  one search expression.
- 29 flag model identifiers, credential-source names or an OAuth Boolean, not
  the claimed credential value. They have evidence-based metadata dispositions,
  not automatic GitHub dismissals.
- #96 is a generic native CLI output renderer. It records/displays caller text,
  including intentionally private conversation content. A concrete credential
  source or unauthorized recipient has not been established. Maya's canonical
  runtime factory is `run_agent:AIAgent`, not `HermesCLI`. The native interactive
  CLI/background renderer is not qualified in the initial Maya host profile.
  Its delivery/history sinks remain explicit G2/G4 work; do not redact all
  legitimate conversation text or count it as a closed disclosure boundary.

These alerts do not establish that actual customer credentials are hardcoded in
the repository. They do establish native credential-fragment display behavior.

## Candidate Fix Boundary

`0024-codeql-security-checkpoint.patch` applies after the exact 23-patch G0
source. It preserves the accepted G0 contract and receipts as historical evidence.
The overlay changes ten native modules, with independent patch/source hashes in
[its contract](governance-security-checkpoint.json).

Credential displays use fixed configured/missing labels, including both OpenAI
and Anthropic startup, native CLI configuration, Anthropic 401 diagnostics and
the shared debug-header masker. No prefix or suffix is retained. Callable Entra
credentials are never invoked by a display operation.

The reviewed endpoint diagnostics use a display-only presence label. The label
never becomes a transport URL. Adjacent startup, local context/stream timeout and
model-discovery diagnostics are included; provider discovery exceptions use a
fixed code. This is not a claim that all other Hermes diagnostics are qualified.

Provider classification reuses native parsed-host helpers rather than a second
registry. Host/path/query lookalikes do not select the reviewed provider behavior.
Kimi and MiniMax route matching uses slash-delimited parsed paths. MiniMax's
explicit port/trailing-dot variants retain Bearer/beta behavior. Native hostname
parsing rejects userinfo, backslashes, embedded whitespace, malformed ports and
encoded authority ambiguity. Classification never authorizes egress.

The adjacent host-derived credential selector now requires a canonical endpoint
from the existing native credential registry. Its documented Groq/Mistral legacy
hosts remain supported explicitly. An unrelated TLD with the same vendor label
cannot select an ambient key. No user provider plugins are discovered merely
to choose that key. Explicit custom credentials are unchanged. Maya still requires
explicit secret references; this native compatibility fallback does not authorize
ambient credentials in the managed product host.

Maya model configuration rejects credential-bearing base URLs, query/fragment
channels, invalid ports and parser ambiguity before readiness or construction.
It does not silently rewrite them. Provider query parameters such as Azure's
`api-version` belong to SDK adapter parameters, not a Maya base-URL secret channel.
Customer paths and local IPv6 endpoints remain accepted unchanged.

Native conversation search rejects queries over 4096 characters before regex
work and removes the overlapping underscore repetition. It preserves native
phrase, prefix, Unicode, dotted/hyphenated/underscored term behavior in the covered
controls. This remains Hermes conversation search, not Maya SMB memory, and does
not grant native session-search tool permission.

## Verification And Acceptance

The reconstruction tool reads pinned Git objects, applies the original 23 patches
then the security overlay, checks every resulting native file, and writes a
separate security manifest. Source inventory identity is stable across checkout
line endings. The test file is hashed in the contract, checked during preparation
and again after copying to the disposable native test tree; results retain its
digest. Required tests may not be silently substituted or skipped.

Independent read-only review identified an Anthropic credential alias, adjacent
diagnostic sinks, MiniMax equivalent forms, ambient hostname-key derivation and
missing test-byte binding. They are included in the corrected candidate and its
focused probes. This is one review cycle, not independent production approval.

Local product/model/provenance checks pass. The required 47 Phase 6/update/setup/
closure tests, context validation and compilation pass. A preliminary native
security run passed 23 probes; subsequent review required additional changes.
Only the final corrected receipt can support acceptance.

The final corrected local run passed 193 native tests with no failures, skips or
omitted files: 29 security probes, 25 existing hostname controls, 132 native
provider-resolution controls and seven third-party Anthropic OAuth controls.
The 36 Maya model/provenance/workflow checks also pass. Credential prefix/suffix
markers remain absent from both complete native startup modes and the complete
configuration-display method. Canonical provider/auth, custom explicit credentials,
legitimate FTS/SQLite queries and equivalent MiniMax endpoint forms remain covered.
These are bounded security-path controls, not G1/full-loop qualification.

Independent final stages `governance-security-20261003-final-c` and `-final-d`
have identical security manifest SHA256
`eb51f699a4879b7d66631542141d5e369018507bacded3e193f91f7fdb6cdf6e`.
The security test digest recorded by the final result is
`6dfe36c028cb38a59813ac350edd3acc8c85c822c11272a0668b2e62dc04ffd5`.
Native source and patch digests are in the security contract. Evidence is retained
in the ignored final-c stage's `native-security-result.json` and
`native-dependencies.json`; no generated source tree belongs in a commit.

The preliminary Windows bounded native run had 959 passes, no assertion failures,
one required POSIX-permission skip, and three unexecuted files. It correctly failed
the gate. This is diagnostic evidence, not acceptance of the final patch.

Checkpoint acceptance requires:

1. Final focused native security probes and registered routing/authentication
   controls pass with zero skips against the exact hashed overlay.
2. Two clean reconstructions agree on the final security manifest.
3. All 16 required ordinary native files execute without skips for both unpatched
   and security candidate sources on the prepared Python 3.13 Linux environment.
4. The 57-item disposition register remains complete; native CLI/privacy and
   broader diagnostic/egress qualification are retained as explicit exclusions,
   not inferred to be healthy or enabled.

The manual `Governance Security Checkpoint` workflow implements these Linux
checks. It needs the committed/pushed candidate, then reviewed receipts. It does
not install customer software, use credentials, build an installer or enable G1.
Until those receipts are accepted, step 4 above is not complete.

The first Linux run (37146339919) passed all 193 focused native checks, then
blocked before bounded regressions: native Bedrock import triggered lazy
installation of boto3 with unlocked transitive dependencies. The evidence shows
botocore 1.42.97 and s3transfer 0.16.1 instead of locked 1.42.89 and 0.16.0.
Both native workflows now prepare the existing Bedrock extra through locked sync;
the runner requires that extra and sets HERMES_DISABLE_LAZY_INSTALLS=1. This is
test-environment preparation, not enabling Bedrock in Maya or changing native
patches. Fresh Linux receipts are still required; the failed run is not accepted.

## Commands

```text
python scripts/prepare_governance_security_checkpoint.py --source-repo <Hermes-clone> --output <new-stage>
python scripts/run_governance_native_regressions.py --stage <new-stage> --python <prepared-python> --mode security --security-checkpoint
python scripts/run_governance_native_regressions.py --stage <new-stage> --python <prepared-python> --mode bounded --security-checkpoint
python -m unittest tests.test_governance_security_checkpoint tests.test_governance_baseline tests.test_phase2_model_config tests.test_phase2_local_model_endpoint_readiness -v
```

Commit only tracked source, patch, test, workflow and documentation changes.
Generated `.codex-build` stages and receipts are ignored; no customer state or
private keys belong in the commit. Frozen CodeQL fixture locations may remain open
after this source fix; any GitHub disposition is a separate explicit action.
