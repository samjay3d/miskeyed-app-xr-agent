# Integration findings

This file is a running, append-only-at-the-bottom integration log. Findings are
resolved only after validation against a real Kit build and headset.

## F-001 — Kit XR pose API varies by Kit release (open)

**Observed:** Kit extension identifiers and the Python surface used to read the
Kit-owned OpenXR session are not stable enough to infer without the target Kit
SDK. The repository does not yet include a Kit SDK or Rift S runtime.

**Boundary decision:** This belongs in `KitXRAdapter`. The adapter probes only
Kit XR modules/interfaces and refuses to create an OpenXR loader, instance, or
session. Once the target Kit release is known, replace discovery with its
documented API and record the extension/version here.

**Core proposal:** None. Host lifecycle ownership is intentionally outside
`miskeyed-xr-agent`.

## F-002 — Core construction contract cannot be verified offline (open)

**Observed:** The requested source branch is not present in this workspace and
network access to GitHub is unavailable. In particular, the constructor shapes
for `SpatialIntentFrame`, pose samples, reference-space identity/generation,
opaque targets, and `IntentTimeline` cannot be validated.

**Boundary decision:** Do not copy or guess these domain types. The development
bootstrap installs the sibling source checkout editable, and the adapter's
`load_core_contract()` fails with an actionable error unless the real package
exports the required symbols.

**Core proposal:** Export the integration types from one documented public
module and provide a host-adapter example that explicitly carries host timestamp,
reference-space ID, and reference-space generation.

