# miskeyed-app-xr-agent

The smallest practical Omniverse Kit integration harness for the
`codex/create-new-repository-miskeyed-xr-agent` branch of
[`samjay3d/miskeyed-xr-agent`](https://github.com/samjay3d/miskeyed-xr-agent).
Kit owns OpenXR, rendering, USD, and scene queries. This repository owns only
the host adapter and application wiring.

All Omniverse-specific Python code follows the project namespace convention:
`miskeyed.kit.<module>`. This extension is `miskeyed.kit.xr_agent`; portable
core code remains under the separately owned `miskeyed.xr.agent` package.

## Current milestone

The Kit dependency build installs `miskeyed-xr-agent==0.1.0` from PyPI into a
`pip_prebundle` dependency extension. Kit CI provisions
the official NVIDIA runtime, launches it headless, loads this extension,
creates a stage through Kit's live `omni.usd` context, grounds a real core
`SpatialIntentFrame` against a USD cube, submits `move this there` through
`IntentTimeline`, verifies the `/World/Target` result, unloads, and exits.

## Prerequisites

* An Omniverse Kit SDK checkout/build (`kit` or `kit.exe`)
* An Oculus Rift S configured as the active OpenXR runtime
* CMake 3.24+, Python 3.10+, and internet access
* An extracted Omniverse Kit SDK whose license has been accepted

## Configure and build

For the shortest local path (Ninja required):

```bash
cmake --preset dev
cmake --build --preset dev
ctest --preset dev
```

For a local Kit installation:

```bash
cmake -S . -B build -DKIT_ROOT=/absolute/path/to/extracted-kit-sdk
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

Download Kit SDK from NVIDIA's official
[Kit App Template/NGC workflow](https://github.com/NVIDIA-Omniverse/kit-app-template#quick-start).
The SDK cannot be silently downloaded by CMake because NVIDIA requires the
developer to accept its product terms. `KIT_ROOT` makes that one unavoidable
manual step explicit. The official Kit App Template dependency build installs
the released core wheel using Kit's own Python and exposes it through
`miskeyed.xr.python_deps`; this repository never builds or copies the core.

Launch the staged app with `cmake --build build --target launch`. The native
core wheel must support the Python ABI embedded by the selected Kit SDK.

When using the `dev` preset, supply Kit while configuring and launch with:

```bash
cmake --preset dev -DKIT_ROOT=/absolute/path/to/extracted-kit-sdk
cmake --build build/dev --target launch
```

## Supported CI targets

The core repository independently builds, tests, and publishes its wheels.
This app has only `kit-ci`. It uses the
official NVIDIA Kit App Template tooling to provision Kit, locates Kit's runtime
and Python, installs `miskeyed-xr-agent==0.1.0` into `pip_prebundle`, launches the headless CI
experience, and requires the extension to complete a Kit/OpenUSD grounding pass
before requesting a clean process exit. Any provisioning, extension-load,
scene-context, grounding, or shutdown error fails the job.

The headless job intentionally exercises Kit and OpenUSD without claiming XR
hardware tracking. Rift S tracking remains a separate physical acceptance test;
the production experience enables Kit's OpenXR extension and never creates a
second session.

The Windows job explicitly initializes the Visual Studio developer environment
before using the Ninja preset. This is required because installing Visual Studio
on a GitHub runner does not by itself place `cl.exe` on the job's `PATH`.

Look for `[miskeyed.xr]` in the console. The production adapter directly uses
`omni.kit.xr.core.XRCore.get_singleton()`, `/user/head`, `/user/hand/right`, and
their Kit-owned virtual-world poses. It never creates another OpenXR session.

## Boundary

```text
Oculus Rift S -> OpenXR runtime -> Kit XR lifecycle -> KitXRAdapter
  -> miskeyed-xr-agent SpatialIntentFrame -> Kit scene query / USD target
```

Controller aim, raycasts, text grounding, visualization, and preview/undo are
deliberately deferred until live head tracking is proven. See
[`INTEGRATION_FINDINGS.md`](INTEGRATION_FINDINGS.md) for the live contract log.
