"""Validate a KAT fat package and emit the launcher's release manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--platform", choices=("linux-x86_64", "windows-x86_64"), required=True)
    parser.add_argument("--repository", default="samjay3d/miskeyed-app-xr-agent")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    executable = "kit/kit.exe" if args.platform.startswith("windows") else "kit/kit"
    experience = "apps/miskeyed.xr.kit"
    with zipfile.ZipFile(args.archive) as package:
        names = set(package.namelist())
        prefixes = {name.split("/", 1)[0] for name in names if "/" in name}
        # KAT packages may have a single archive root directory.
        prefix = ""
        if executable not in names and len(prefixes) == 1:
            prefix = next(iter(prefixes)) + "/"
        required = [prefix + executable, prefix + experience]
        missing = [name for name in required if name not in names]
        if missing:
            raise SystemExit(f"not a runnable KAT fat package; missing {missing}")
        if not any("license" in name.lower() or "notice" in name.lower() for name in names):
            raise SystemExit("KAT package contains no license/notice material")
    digest = hashlib.sha256(args.archive.read_bytes()).hexdigest()
    release = f"https://github.com/{args.repository}/releases/download/v{args.version}"
    manifest = {
        "schema": 1,
        "app": "miskeyed-xr-agent",
        "version": args.version,
        "platform": args.platform,
        "packaging": {"authority": "nvidia-kit-app-template", "type": "fat"},
        "package": {"url": f"{release}/{args.archive.name}", "sha256": digest},
        "launch": {"executable": prefix + executable, "experience": prefix + experience},
    }
    args.output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
