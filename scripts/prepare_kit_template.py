"""Materialize this product in a pinned Kit App Template checkout."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


def prepare(repo: Path, template: Path, version: str) -> None:
    # Production KAT revisions can retain NVIDIA-internal repo tooling in the
    # public source tree.  It is not part of an external application's build
    # or packaging graph and its packages are not available from the public
    # Packman remotes (for example, repo_docs).  Keep the public KAT toolchain
    # authoritative while excluding that internal-only bootstrap input.
    (template / "tools/deps/repo-deps-nv.packman.xml").unlink(missing_ok=True)

    source = template / "source"
    shutil.rmtree(source / "apps", ignore_errors=True)
    shutil.rmtree(source / "extensions", ignore_errors=True)
    shutil.copytree(repo / "apps", source / "apps")
    shutil.copytree(repo / "exts", source / "extensions")

    # KAT's build discovers manually-authored apps through premake and precaches
    # the extension closure from repo_precache_exts.apps.
    (template / "premake5.lua").write_text(
        (template / "premake5.lua").read_text(encoding="utf-8")
        + '\ndefine_app("miskeyed.xr.kit")\ndefine_app("miskeyed.xr.ci.kit")\n',
        encoding="utf-8",
    )
    repo_toml = template / "repo.toml"
    config = repo_toml.read_text(encoding="utf-8")
    config = config.replace('name = "kit-sdk"', 'name = "miskeyed-app-xr-agent"', 1)
    config, count = re.subn(
        r'(?s)(\[repo_precache_exts\].*?\napps\s*=\s*)\[.*?\]',
        r'\1["${root}/source/apps/miskeyed.xr.kit"]',
        config,
        count=1,
    )
    if count != 1:
        raise RuntimeError("pinned Kit App Template repo_precache_exts layout changed")
    repo_toml.write_text(config, encoding="utf-8")
    (template / "tools/VERSION.md").write_text(version + "\n", encoding="utf-8")
    with (template / "tools/deps/pip.toml").open("a", encoding="utf-8") as stream:
        stream.write((repo / "kit-template/tools/deps/pip.toml").read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    prepare(args.repo.resolve(), args.template.resolve(), args.version)


if __name__ == "__main__":
    main()
