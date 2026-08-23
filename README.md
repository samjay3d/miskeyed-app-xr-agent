# miskeyed-app-xr-agent

The smallest practical Omniverse Kit integration harness for the
`codex/create-new-repository-miskeyed-xr-agent` branch of
[`samjay3d/miskeyed-xr-agent`](https://github.com/samjay3d/miskeyed-xr-agent).
Kit owns OpenXR, rendering, USD, and scene queries. This repository owns only
the host adapter and application wiring.

## Current milestone

The build now fetches the reviewed core revision, compiles its real Python
extension, and stages it beside the Kit application. The runtime probe logs
which Kit XR Python module and interface are present. It **does not** create an
OpenXR instance or session and it does not manufacture tracking data. The exact
public pose API must still be confirmed against the Kit build used with the
Rift S before the adapter is connected.

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

## What CI proves

The normal `CI` workflow runs on clean GitHub-hosted Linux and Windows machines
with Python 3.10 and 3.12. It fetches the pinned core, compiles the actual native
binding, stages the app, runs adapter tests, imports the staged package, creates
a real core `SpatialIntentFrame`, and uploads the stage as an artifact.

Kit SDK itself is licensed software and a GitHub-hosted runner cannot accept
NVIDIA's terms for you. The manual `Licensed Kit SDK smoke test` workflow is the
honest second CI tier: attach a self-hosted Linux runner labeled
`omniverse-kit`, set the repository variable `KIT_ROOT`, and dispatch it. That
runner also needs `KIT_PYTHON` set to the executable shipped with that SDK. The
job builds with Kit's Python ABI and boots the staged app for 100 updates. A
Rift S hardware acceptance run remains a physical test, not a mocked CI claim.

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
