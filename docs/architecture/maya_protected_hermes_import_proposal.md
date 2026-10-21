# Protected Hermes Import Compatibility Proposal

## Status

Proposed next after Screen 11. The user's continuation permits recording that
result and preparing this proposal. No new package, dependency download,
workstation import, VM run, installer change or security change is performed
or authorized by this document. Preparation and one eventual VM attempt need
their own explicit decisions. This is not Gate A acceptance.

## Question And Smallest Useful Test

Can the actual selected Hermes package and the dependencies needed to import
its supported run_agent:AIAgent entry point load under Maya's AppContainer/WFP
restriction profile, using the bundled Python 3.13.14?

The first test imports the real module, resolves the actual AIAgent class and
reports bounded provenance and stage results, then exits. It does not construct
an agent, call chat/run_conversation, invoke the Maya adapter's start method,
run skills, attach authoritative memory or make an inference request. Import
can itself have side effects: review its transitive initialization paths before
freezing the payload. Do not describe an import as inert or a full Hermes start.

## Artifact Selection

Use the existing production packaging source as the proposed baseline:
`setup.py` pins Bidzina83/hermes-agent at
`b13e2fd6948a59eeb59fe618914147d97a2ee90a`. Its documented Python range
is >=3.11,<3.14; 3.13.14 is inside that range, but this is not evidence that
every Windows dependency or AppContainer path works.

The separate governance candidate in hermes_plugins/candidate.py pins
0.17.0+maya.gov12.candidate.20261002 and SHA256
af979f8445e56e0379c7ad5252a228be5e7cf924c86f37c3c76a85ade867a323.
It is not an interchangeable runtime, and this proposal does not approve its
patches, bypass its qualification checks or replace the production pin.

Before package preparation, bind the exact source/wheel identity, complete
dependency closure, CPython 3.13 Windows x64 wheel compatibility, hashes and
licenses. Use existing verified artifacts where available. Missing artifacts,
unavailable wheels, an unresolved dependency or required source compilation
must be disclosed, not solved by an unreviewed version change or native install.
No claim is made yet that a suitable complete offline wheel set is available.

## Product-Owned Package Contract

- Reuse the existing Maya consent/setup/restricted-launch/report/cleanup path;
  no external supervisor, reference launcher or new test harness on the VM.
- Keep the Python engine and restriction profile: zero capabilities, reduced
  token, six scoped network denies, job/child policy, three inherited pipes,
  isolated Python flags and the existing deadlines/output bounds.
- Stage verified Hermes/dependency files read-only inside this attempt's runtime.
  Use explicit product-owned import configuration compatible with isolated mode;
  no editable install, repository path, user-site fallback, PYTHONPATH dependence,
  online pip or machine-wide Python/PATH change.
- Use a fresh private Hermes home and temporary/cache paths only in the approved
  writable state. Do not copy an existing user home, .env, tokens, configuration,
  skills or credentials. These path additions require exact impact review before
  assembly; no path, permission or environment change is silently inherited.
- Keep all networking denied, including models and localhost services. No gateway
  exception, loopback exemption, secret, connector or synthetic model server.
- Verify all payload hashes before restricted resume. No native dependency runs
  during local assembly. Source inspection and inert fixture checks only.

## Evidence And Verdict

Record the exact launcher, Python, Hermes and dependency identities; actual
module origins and installed distribution metadata; Python entry, module-import
stages, resolution of the real class, natural exit and bounded output. Origins
must be inside the verified runtime; a callable stub, mock, merely discoverable
module or metadata-only installation cannot satisfy the import objective.

On failure, distinguish Python entry failure, missing dependency, native DLL
load failure, denied resource and import side effect using bounded redacted
evidence. Unknown causes stay unknown. Do not log environment dumps or credentials.
Stop after the first attempt: no grant, capability, alternative launcher,
deadline increase, retargeted dependency or automatic retry.

Success means only offline import compatibility in that exact restricted
environment. It does not establish construction, model execution, native memory,
governed actions, connectors, Metabase, broad containment or production readiness.
Later tests must separately assess construction/shutdown and bounded operational
state before any gateway/model route is introduced. They must use the existing
authorization architecture, not optional Hermes hooks as the enforcement boundary.

## Next Decision

Approve bounded source/dependency assessment and package preparation for this
import-only scope. If that assessment reveals a requirement beyond the stated
scope, return the impact and alternatives before changes. Once the package and
its exact impact are reviewed, seek separate approval for one RDP VM run and
fresh in-product consent. Do not restart Screen 11 to obtain more evidence.

## Approved Preparation Assessment

The user subsequently approved package preparation. The assessment in
`maya_protected_hermes_import_build_assessment.md` found a file-count guard
conflict and an incomplete cached installed tree. No ready-to-run package or
native result exists. A bounded import-specific inventory envelope and verified
wheel acquisition are proposed for explicit approval, not silently applied.
