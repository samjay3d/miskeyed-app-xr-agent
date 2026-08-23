"""Small installer/launcher for a tested Kit App Template package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

PACKAGE = "miskeyed-app-xr-agent"
REPOSITORY = "samjay3d/miskeyed-app-xr-agent"


def app_version() -> str:
    try:
        return version(PACKAGE)
    except PackageNotFoundError:
        return "0.1.0"


def platform_id(system: str | None = None, machine: str | None = None) -> str:
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    if machine not in {"x86_64", "amd64"} or system not in {"Linux", "Windows"}:
        raise RuntimeError(f"unsupported Kit platform: {system} {machine}")
    return ("linux" if system == "Linux" else "windows") + "-x86_64"


def default_install_root(system: str | None = None) -> Path:
    system = system or platform.system()
    if system == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "Miskeyed" / "apps" / "xr-agent"


def manifest_url(release: str, target: str) -> str:
    return f"https://github.com/{REPOSITORY}/releases/download/v{release}/miskeyed-xr-agent-{release}-{target}.json"


def _download(url: str, destination: Path) -> None:
    with urllib.request.urlopen(url, timeout=120) as response, destination.open("wb") as stream:
        shutil.copyfileobj(response, stream)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def install(root: Path, *, reinstall: bool = False) -> Path:
    release, target = app_version(), platform_id()
    destination = root / release / target
    marker = destination / ".miskeyed-install.json"
    if marker.is_file() and not reinstall:
        return destination

    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".xr-agent-", dir=root) as temporary:
        temporary_path = Path(temporary)
        manifest_path = temporary_path / "manifest.json"
        _download(manifest_url(release, target), manifest_path)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (manifest.get("schema"), manifest.get("app"), manifest.get("version"), manifest.get("platform")) != (1, "miskeyed-xr-agent", release, target):
            raise RuntimeError("release manifest identity does not match this launcher")
        package = manifest["package"]
        archive = temporary_path / Path(package["url"]).name
        _download(package["url"], archive)
        if _sha256(archive) != package["sha256"]:
            raise RuntimeError("Kit application package checksum mismatch")
        extracted = temporary_path / "install"
        extracted.mkdir()
        with zipfile.ZipFile(archive) as package_zip:
            package_zip.extractall(extracted)
        (extracted / ".miskeyed-install.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        if destination.exists():
            if not reinstall:
                raise RuntimeError(f"incomplete installation exists at {destination}; use --reinstall")
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        extracted.replace(destination)
    return destination


def launch(installation: Path, extra: list[str]) -> None:
    manifest = json.loads((installation / ".miskeyed-install.json").read_text(encoding="utf-8"))
    executable = installation / manifest["launch"]["executable"]
    experience = installation / manifest["launch"]["experience"]
    if not executable.is_file() or not experience.is_file():
        raise RuntimeError("packaged Kit executable or production experience is missing")
    subprocess.run([str(executable), str(experience), *extra], cwd=installation, check=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog=PACKAGE)
    parser.add_argument("--version", action="version", version=app_version())
    parser.add_argument("--install", action="store_true", help="install without launching")
    parser.add_argument("--reinstall", action="store_true")
    parser.add_argument("--install-dir", type=Path, default=default_install_root())
    parser.add_argument("kit_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        installed = install(args.install_dir, reinstall=args.reinstall)
        if not args.install:
            launch(installed, args.kit_args)
    except (OSError, KeyError, ValueError, RuntimeError, zipfile.BadZipFile, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"{PACKAGE}: {exc}\n")
    return 0
