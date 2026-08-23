# Integration findings

This file is a running, append-only-at-the-bottom integration log. Findings are
resolved only after validation against a real Kit build and headset.

## F-001 — Kit XR pose API varies by Kit release (resolved 2026-08-23)

**Observed:** The pinned Kit 110.2 line exposes `XRCore` from
`omni.kit.xr.core`. `XRCore.get_singleton().get_input_device()` provides
`/user/head` and `/user/hand/right`; devices expose `get_virtual_world_pose()`.

**Boundary decision:** `KitXRAdapter` targets that API directly. Head and right
controller virtual-world poses become the core head pose and controller ray.
There is no multi-major compatibility probe and no app-owned OpenXR lifecycle.

**Core proposal:** None. Host lifecycle ownership is intentionally outside
`miskeyed-xr-agent`.

## F-002 — Core ownership boundary (resolved 2026-08-23)

**Observed:** `miskeyed-xr-agent==0.1.0` publicly exposes `miskeyed.xr.agent`, including
`SpatialIntentFrame`, `ReferenceSpace`, pose/ray values, `resolve_target`, and
`IntentTimeline`, as platform wheels on PyPI.

**Boundary decision:** `miskeyed-xr-agent` owns and publishes the host-neutral
core. `miskeyed-app-xr-agent` consumes exactly version 0.1.0 from PyPI through
Kit App Template's `pip_prebundle`. App CMake does not fetch or compile core.

**Core result:** The requested single public module and host integration example
now exist. No core change is proposed for this finding.

## F-003 — Kit SDK acquisition requires product-term acceptance (resolved 2026-08-23)

**Observed:** NVIDIA distributes current production Kit SDK releases through
NGC and its Kit App Template workflow. It is not appropriate for an unattended
CMake configure to accept those terms for the developer.

**Boundary decision:** Local developers may supply `KIT_ROOT`. In CI, the
official NVIDIA Kit App Template tooling provisions the runtime as a supported
job step. Kit availability is expected; provisioning failure fails `kit-ci`.

## F-004 — App-side pybind11 bridge (resolved 2026-08-23)

**Observed:** The core's Python option unconditionally calls
`find_package(pybind11 CONFIG REQUIRED)`, even when a parent CMake project has
already provided the official `pybind11` targets with `FetchContent`.

**Boundary decision:** Deleted the app-side core build and pybind11 bridge. Wheel
compatibility is now a core release-matrix responsibility and a hard `kit-ci`
gate.

**Core result:** PyPI publishes a CPython 3.12 manylinux x86-64 wheel compatible
with Kit 110.2's Python 3.12 runtime.

## F-011 — Kit stub generation requires a local marker (resolved 2026-08-23)

**Observed:** Kit CI run `32626616830` proved that Kit's Python 3.12.13 selected
and installed `miskeyed-xr-agent==0.1.0`, then the Kit App Template post-build
stub generator rejected the dependency-only extension because its payload had
no local `.pyi` file.

**Boundary decision:** The dependency extension links one marker stub alongside
the official `pip_prebundle`. It does not describe or duplicate core types; it
only identifies that the typed/native API is owned by the installed wheel.

## F-012 — Local extensions stage under `exts`, not `extsbuild` (resolved 2026-08-23)

**Observed:** Kit CI run `32626746750` completed wheel installation, stub
generation, and the Kit build. Launch then could not resolve
`miskeyed.kit.xr_agent` because the command exposed registry links from
`extsbuild` but not local projects staged under the release `exts` directory.

**Boundary decision:** Launch includes both `$KIT_ROOT/exts` for this app's
extensions and `$KIT_ROOT/extsbuild`/`extscache` for Kit-provided dependencies.

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
