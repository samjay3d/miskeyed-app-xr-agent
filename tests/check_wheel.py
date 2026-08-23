"""Assert that the PyPI artifact is only a portable Kit bootstrap wrapper."""

from __future__ import annotations

import email
import sys
import zipfile
from pathlib import Path


def main() -> None:
    wheels = list(Path(sys.argv[1]).glob("*.whl"))
    assert len(wheels) == 1, f"expected one wheel, found: {wheels}"
    wheel = wheels[0]
    assert wheel.name.endswith("-py3-none-any.whl"), wheel.name
    with zipfile.ZipFile(wheel) as archive:
        metadata_path = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = email.message_from_bytes(archive.read(metadata_path))
    runtime_dependencies = [
        value for value in (metadata.get_all("Requires-Dist") or []) if "extra ==" not in value
    ]
    assert not runtime_dependencies, runtime_dependencies
    print(f"PORTABLE_WRAPPER={wheel.name} runtime_dependencies=none")


if __name__ == "__main__":
    main()
