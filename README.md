# miskeyed-app-xr-agent

The smallest practical Omniverse Kit integration harness for the
`codex/create-new-repository-miskeyed-xr-agent` branch of
[`samjay3d/miskeyed-xr-agent`](https://github.com/samjay3d/miskeyed-xr-agent).
Kit owns OpenXR, rendering, USD, and scene queries. This repository owns only
the host adapter and application wiring.

## Current milestone

This initial scaffold boots a Kit experience, enables Kit's XR extensions, and
runs an intentionally strict runtime probe. The probe logs which Kit XR Python
module and interface are present. It **does not** create an OpenXR instance or
session and it does not manufacture tracking data. The exact public pose API
must be confirmed against the Kit build used with the Rift S before the adapter
is connected; that is the first recorded integration finding.

## Prerequisites

* An Omniverse Kit SDK checkout/build (`kit` or `kit.exe`)
* An Oculus Rift S configured as the active OpenXR runtime
* A sibling checkout of `miskeyed-xr-agent` on the integration branch

Bootstrap the core library from source (never vendor it here):

```bash
git clone --branch codex/create-new-repository-miskeyed-xr-agent \
  https://github.com/samjay3d/miskeyed-xr-agent.git ../miskeyed-xr-agent
./scripts/use-local-core.sh ../miskeyed-xr-agent
```

Launch with the Kit SDK:

```bash
/path/to/kit apps/miskeyed.xr.kit
```

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

