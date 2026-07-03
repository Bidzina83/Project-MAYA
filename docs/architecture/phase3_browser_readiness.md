# Phase 3 Browser Readiness

## Status

Browser readiness hardening slice for Phase 3 Capability Dependency and
Readiness Foundation.

## Decision

Maya reports browser readiness through deterministic local checks before
browser automation is treated as product-complete.

The `maya-browser` profile now reports:

- supported browser executable readiness;
- customer-managed browser automation driver/runtime readiness;
- local governance policy readiness for browser actions.

The readiness layer does not launch a browser, install a browser, download
drivers, or perform live browser automation. It only reports whether the local
profile has the minimum declared surfaces for later governed browser work.

## Doctor Behavior

`maya doctor` emits stable checks such as:

- `dependencies.profile.maya-browser`
- `dependencies.browser.executable`
- `dependencies.browser.automation-driver`
- `dependencies.browser.governance-policy`

When `maya-browser` is enabled, a missing supported browser executable is a
required dependency failure. The automation driver/runtime is reported as
customer-managed in Phase 3 because Maya has not yet selected or packaged a
browser automation implementation. Governance policy readiness is also
reported explicitly because browser actions are consequential local/external
actions and must pass the local authorization gateway.

Messages are redacted and do not print full executable paths, secrets, browser
profile paths, cookies, session data, or customer URLs.

## Non-Goals

This slice does not:

- install Chrome, Edge, Chromium, browser drivers, or Playwright/Selenium
  browser payloads;
- launch a browser;
- inspect user browser profiles, cookies, history, extensions, or sessions;
- implement browser automation workflows;
- claim browser automation support for any platform.

Those capabilities belong to later browser integration and installer work.
