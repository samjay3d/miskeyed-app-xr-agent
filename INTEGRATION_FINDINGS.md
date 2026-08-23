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

## F-002 — Core construction contract unavailable (resolved 2026-08-23)

**Observed:** The branch now publicly exposes `miskeyed.xr.agent`, including
`SpatialIntentFrame`, `ReferenceSpace`, pose/ray values, `resolve_target`, and
`IntentTimeline`. Revision `ea1c6106c9e85b3d23491c403e47a6e4d6818fb0` was
reviewed and is the reproducible CMake default.

**Boundary decision:** CMake compiles that core revision directly, while
`MISKEYED_XR_AGENT_SOURCE` selects a live sibling checkout. `KitXRSample` is an
adapter input DTO, not a duplicate portable domain model. Translation constructs
the core's real types and preserves Kit time/space values verbatim.

**Core result:** The requested single public module and host integration example
now exist. No core change is proposed for this finding.

## F-003 — Kit SDK acquisition requires product-term acceptance (resolved 2026-08-23)

**Observed:** NVIDIA distributes current production Kit SDK releases through
NGC and its Kit App Template workflow. It is not appropriate for an unattended
CMake configure to accept those terms for the developer.

**Boundary decision:** Local developers may supply `KIT_ROOT`. In CI, the
official NVIDIA Kit App Template tooling provisions the runtime as a supported
job step. Kit availability is expected; provisioning failure fails `kit-ci`.

## F-004 — Core assumes pybind11 must be installed (open)

**Observed:** The core's Python option unconditionally calls
`find_package(pybind11 CONFIG REQUIRED)`, even when a parent CMake project has
already provided the official `pybind11` targets with `FetchContent`.

**Boundary decision:** This app supplies a minimal package-discovery bridge to
the already-created upstream targets. This is build integration only and does
not belong in the runtime adapter.

**Core proposal:** Skip `find_package` when `pybind11::module` already exists.

## F-005 — Public CI did not exercise Kit (resolved 2026-08-23)

**Observed:** GitHub-hosted runners can build the complete open-source adapter
and core but do not contain the licensed Kit SDK, an NVIDIA GPU, an OpenXR
runtime, or a Rift S.

**Boundary decision:** `core-ci` builds the core checkout alone on Linux and
Windows. `kit-ci` provisions official Kit on a hosted runner, builds against its
Python ABI, launches Kit headless, loads the extension, uses the live
`omni.usd` context, grounds a core frame to `/World/Target`, and exits cleanly.
Live tracking remains a physical hardware gate, not a reason to omit Kit CI.

## F-009 — Headless Kit needs a deterministic integration experience (resolved 2026-08-23)

**Observed:** The production app enables OpenXR and expects hardware, which is
not the correct entry point for a headless scene-context integration check.

**Boundary decision:** `miskeyed.xr.ci.kit` is a real Kit experience with USD
and the extension but no XR runtime dependency. A one-shot update callback
creates a USD cube in Kit's context, raycasts its world bound, calls the real
core `resolve_target` and `IntentTimeline`, checks the opaque SdfPath, then asks
Kit to quit. The production experience continues to own the OpenXR path.

## F-010 — Kit runtime discovery ignored Packman symlinks (resolved 2026-08-23)

**Observed:** Kit CI run `32625539575` successfully provisioned Kit 110.2 and
completed NVIDIA's release build, then failed in the runtime-location step. The
workflow searched only `find -type f`, but Packman exposes
`_build/linux-x86_64/release/kit/kit` and its Python through symlinks.

**Boundary decision:** Use the stable output layout printed and produced by the
pinned official Kit App Template build and validate both paths with `test -x`,
which follows symlinks. Do not heuristically scan the SDK tree.

## F-006 — Pointing confidence is categorical, not numeric (resolved 2026-08-23)

**Observed:** Exercising the staged native binding caught that
`PointingIntent.confidence` requires the core `TrackingConfidence` enum; the
first adapter draft incorrectly annotated the Kit-side value as a float.

**Boundary decision:** `KitXRSample` carries the mapped core confidence enum and
the staged-core smoke test assigns it through the real pybind11 property. The
core contract is coherent; no core change is proposed.

## F-007 — Omniverse adapter namespace was inconsistent (resolved 2026-08-23)

**Observed:** The first extension used the flat ID `miskeyed.xr.adapter` and
Python package `miskeyed_kit_xr`, obscuring which code is Kit-specific and
breaking the established `miskeyed.kit.<module>` convention.

**Boundary decision:** The extension ID is now `miskeyed.kit.xr_agent`, and all
of its Python implementation lives below `miskeyed.kit.xr_agent`. Parent
directories remain PEP 420 namespace packages so the separately staged
`miskeyed.xr.agent` core can coexist without path-order tricks.

## F-008 — Windows CI did not initialize the MSVC environment (resolved 2026-08-23)

**Observed:** The CI preset selects Ninja. Although GitHub's Windows image has
Visual Studio installed, Ninja cannot compile until `cl.exe` and the matching
SDK environment are exported into the job.

**Boundary decision:** The Windows matrix leg now runs the standard
`ilammy/msvc-dev-cmd` setup action before CMake configure. Linux remains
unchanged, and both platforms continue through the identical CMake preset.
