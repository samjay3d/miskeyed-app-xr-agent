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

The build fetches the reviewed core revision, compiles its real Python
extension, and stages it beside a supported Kit application. Kit CI provisions
the official NVIDIA runtime, launches it headless, loads this extension,
creates a stage through Kit's live `omni.usd` context, grounds a real core
`SpatialIntentFrame` against a USD cube, submits `move this there` through
`IntentTimeline`, verifies the `/World/Target` result, unloads, and exits.

## Prerequisites

* An Omniverse Kit SDK checkout/build (`kit` or `kit.exe`)
* An Oculus Rift S configured as the active OpenXR runtime
* CMake 3.24+, a C++20 compiler, Python development headers, and internet access
* An extracted Omniverse Kit SDK whose license has been accepted

## Configure and build

For the shortest local path (Ninja required):

```bash
cmake --preset dev
cmake --build --preset dev
ctest --preset dev
```

The reproducible default fetches the exact reviewed core commit:

```bash
cmake -S . -B build -DKIT_ROOT=/absolute/path/to/extracted-kit-sdk
cmake --build build --parallel
ctest --test-dir build --output-on-failure
```

During joint development, use the branch checkout directly instead:

```bash
cmake -S . -B build \
  -DMISKEYED_XR_AGENT_SOURCE=/absolute/path/to/miskeyed-xr-agent \
  -DKIT_ROOT=/absolute/path/to/extracted-kit-sdk
cmake --build build --parallel
```

Download Kit SDK from NVIDIA's official
[Kit App Template/NGC workflow](https://github.com/NVIDIA-Omniverse/kit-app-template#quick-start).
The SDK cannot be silently downloaded by CMake because NVIDIA requires the
developer to accept its product terms. `KIT_ROOT` makes that one unavoidable
manual step explicit; everything owned by this repository/core is built and
staged by CMake.

Launch the staged app with `cmake --build build --target launch`. The native
core module must be built with the same Python ABI as the selected Kit SDK; if
Kit embeds a different Python, configure CMake with
`-DPython_EXECUTABLE=/path/to/kit/python`.

When using the `dev` preset, supply Kit while configuring and launch with:

```bash
cmake --preset dev -DKIT_ROOT=/absolute/path/to/extracted-kit-sdk \
  -DPython_EXECUTABLE=/path/to/kit/python
cmake --build build/dev --target launch
```

## Supported CI targets

`core-ci` checks out `miskeyed-xr-agent` separately on clean Linux and Windows
runners, disables OpenXR and Python bindings, builds its native spatial library
and host example, and runs the core tests. It does not configure this Kit app or
resolve any Kit/Omniverse package. That is the dependency-boundary proof.

`kit-ci` is a required implementation target, not a placeholder. It uses the
official NVIDIA Kit App Template tooling to provision Kit, locates Kit's runtime
and Python, compiles this application against that ABI, launches the headless CI
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

Look for `[miskeyed.xr]` in the console. `XR runtime bridge discovered` means
the Kit-owned bridge was found. A missing bridge is reported as an integration
failure, not replaced by a mock or a second OpenXR session.

## Boundary

```text
Oculus Rift S -> OpenXR runtime -> Kit XR lifecycle -> KitXRAdapter
  -> miskeyed-xr-agent SpatialIntentFrame -> Kit scene query / USD target
```

Controller aim, raycasts, text grounding, visualization, and preview/undo are
deliberately deferred until live head tracking is proven. See
[`INTEGRATION_FINDINGS.md`](INTEGRATION_FINDINGS.md) for the live contract log.
