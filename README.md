# miskeyed-app-xr-agent

The reference `miskeyed-app-*` configured Omniverse Kit application. Kit owns
the UI, USD scene, rendering, and OpenXR lifecycle; `miskeyed.kit.xr_agent`
adapts Kit-owned poses into the host-neutral `miskeyed-xr-agent==0.1.0` core.
It never creates a second OpenXR session.

## User experience

```bash
uvx miskeyed-app-xr-agent
```

The universal, dependency-free PyPI wheel resolves its platform/version
manifest from the matching GitHub Release, downloads the **tested Kit App
Template fat package**, verifies SHA-256, installs it atomically under the
platform application-data directory, and launches `apps/miskeyed.xr.kit`.
The end user needs no NGC account, Kit SDK, source checkout, or separate core
installation. Useful switches are `--version`, `--install`, `--reinstall`, and
`--install-dir`.

## Build and package authority

NVIDIA's pinned [Kit App Template](https://github.com/NVIDIA-Omniverse/kit-app-template)
is the packaging authority. CI materializes `apps/` and `exts/` into its
`source/` tree, adds `miskeyed.xr.kit` to `repo_precache_exts.apps`, then runs:

```bash
repo build --release
repo precache_exts
repo package
repo test --from-package
```

The production `apps/miskeyed.xr.kit` experience—not the reduced headless
smoke—is the dependency root, so Kit resolves UI, USD, rendering, XR/OpenXR,
platform plugins, our extensions, and the PyPI prebundle transitively. Release
code never archives or prunes a raw SDK directory. See
[`docs/KIT_PACKAGING.md`](docs/KIT_PACKAGING.md) for the fat/thin investigation.

The core dependency is deliberately independent of this application's version:
`kit-template/tools/deps/pip.toml` pins `miskeyed-xr-agent==0.1.0`, installed by
Kit's Python into `pip_prebundle`.

## Development

Fast host-side checks do not require Kit:

```bash
python -m pytest -q
python -m build
python tests/check_wheel.py dist
```

Kit CI runs on Linux and Windows and publishes only the exact KAT packages that
passed `repo test --from-package`. NGC/developer credentials are producer-side
only and never appear in launcher metadata or an end-user manifest.

## Architecture

```text
Kit XR/OpenXR + USD
        -> miskeyed.kit.xr_agent KitXRAdapter
        -> miskeyed.xr.agent SpatialIntentFrame / IntentTimeline
        -> grounded USD target
```
