"""Launch the CI experience from the exact KAT package selected for release."""

from __future__ import annotations

import argparse
import subprocess
import tempfile
import zipfile
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--platform", choices=("linux-x86_64", "windows-x86_64"), required=True)
    args = parser.parse_args()

    executable_relative = Path("kit/kit.exe" if args.platform.startswith("windows") else "kit/kit")
    experience_relative = Path("apps/miskeyed.xr.ci.kit")
    with tempfile.TemporaryDirectory(prefix="miskeyed-kat-package-") as temporary:
        install = Path(temporary)
        with zipfile.ZipFile(args.archive) as package:
            package.extractall(install)
        candidates = list(install.glob(f"**/{executable_relative.as_posix()}"))
        if len(candidates) != 1:
            raise SystemExit(f"expected one packaged Kit executable, found {len(candidates)}")
        executable = candidates[0]
        root = executable.parents[1]
        experience = root / experience_relative
        if not experience.is_file():
            raise SystemExit(f"packaged CI experience is missing: {experience_relative}")
        if not args.platform.startswith("windows"):
            executable.chmod(executable.stat().st_mode | 0o111)
        result = subprocess.run(
            [str(executable), str(experience), "--no-window"],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=180,
        )
        print(result.stdout)
        if result.returncode:
            raise SystemExit(f"packaged Kit exited with {result.returncode}")
        for marker in ("KIT_CI_PASS", "KIT_CI_UNLOAD"):
            if marker not in result.stdout:
                raise SystemExit(f"packaged Kit output omitted {marker}")


if __name__ == "__main__":
    main()
