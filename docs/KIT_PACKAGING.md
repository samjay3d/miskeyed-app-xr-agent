# Kit packaging authority

`miskeyed-app-xr-agent` uses NVIDIA Kit App Template (KAT), pinned in
`kit-sdk.toml`, as the sole authority for Kit dependency resolution and package
composition. `apps/miskeyed.xr.kit` is the production dependency root. CI
materializes this repository under KAT's `source/`, runs `repo build`, runs the
extension precacher, and creates a fat package with `repo package`.

The former approach—archiving an NGC SDK directory and manually deciding which
directories form a runtime—is not supported. No code in this repository prunes
or copies arbitrary SDK directories into a release.

## Fat and thin findings

At the pinned KAT revision, a **fat package** contains the Kit kernel and the
resolved extension cache and is explicitly the package form supported by
KAT's `repo test --from-package`. It can run without an end-user NGC account.
This is therefore the release format used by the first implementation.

A **thin package** excludes `kit/`, `extscache/`, and `extsbuild/`. It contains
the configured application and custom content, but does not by itself define a
portable, immutable, cross-application shared store or an offline dependency
acquisition protocol. It therefore cannot yet satisfy `uvx`'s no-NVIDIA-login,
offline-after-download contract on its own. Thin output is retained as an
investigation target, not shipped or treated as a home-grown shared runtime.

If a later `miskeyed-application` layer adds sharing, it must consume a
supported KAT output/lock contract. It must not recreate Kit's dependency
resolver or split a raw SDK tree.

## Ownership

* NGC Kit SDK is a developer/CI input only.
* KAT owns extension closure, precache/locking, kernel composition, and package
  creation.
* This repository owns `miskeyed.xr.kit`, its extensions, and the tiny launcher.
* The launcher downloads a tested fat package from the matching GitHub Release,
  verifies its release manifest and checksum, installs atomically, and launches
  that package. Users receive no NGC URL or credential.
