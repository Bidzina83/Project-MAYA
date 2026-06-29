# Phase 2 Package Verification

Phase 2 extends the clean package verifier to cover Enterprise BYO command and
configuration surfaces from an installed wheel.

The verifier still avoids editable installs and repository path shims. It
builds a wheel, installs that wheel into a temporary virtual environment, and
runs installed package and CLI surfaces.

The Enterprise BYO package checks prove:

- `project_maya` exports the model, connector, and revocation validation
  helpers needed by Phase 2;
- an Enterprise configuration with `broker.mode=disabled` and customer-owned
  model and connector credentials validates from the installed package;
- `export-config` preserves Enterprise edition, disabled broker mode, and
  customer-owned connector modes;
- `import-config` validates the same configuration and remains dry-run by
  default;
- `reset-integration --revoke-provider` reports provider revocation as
  unavailable and never claims external revocation;
- `doctor` reports model and connector diagnostics without printing secret
  references.

The verifier does not contact external providers, perform OAuth, refresh
tokens, run a broker flow, or use Maya-managed model billing. Those remain
outside the Phase 2 package-verification boundary.
