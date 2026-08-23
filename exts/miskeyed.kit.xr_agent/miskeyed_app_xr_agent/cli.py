"""Thin PyPI launcher; NVIDIA Kit remains provisioned by NVIDIA tooling."""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
from pathlib import Path

KIT_TEMPLATE_REVISION = "483e364a4176f102f2d3c3aaf9f301a103d61d69"
KIT_TEMPLATE_URL = "https://github.com/NVIDIA-Omniverse/kit-app-template.git"
CORE_REQUIREMENT = "miskeyed-xr-agent==0.1.0"


def supported_platform(system: str | None = None) -> bool:
    return (system or platform.system()) in {"Linux", "Windows"}


def default_install_root(system: str | None = None) -> Path:
    name = system or platform.system()
    if name == "Windows":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "miskeyed-app-xr-agent" / "kit-app-template"


def kit_paths(root: Path, system: str | None = None) -> tuple[Path, Path]:
    name = system or platform.system()
    target = root / "_build" / ("windows-x86_64" if name == "Windows" else "linux-x86_64") / "release"
    executable = target / "kit" / ("kit.exe" if name == "Windows" else "kit")
    return target, executable


def write_project(template_root: Path) -> None:
    """Materialize app-owned Kit metadata around the installed Python package."""

    import miskeyed.kit.xr_agent as xr_agent

    source = Path(xr_agent.__file__).parent
    extension = template_root / "source/extensions/miskeyed.kit.xr_agent"
    package = extension / "miskeyed/kit/xr_agent"
    package.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, package, dirs_exist_ok=True)
    (extension / "config").mkdir(parents=True, exist_ok=True)
    (extension / "config/extension.toml").write_text(_XR_EXTENSION_TOML, encoding="utf-8")
    (extension / "premake5.lua").write_text(_XR_PREMAKE, encoding="utf-8")

    dependency = template_root / "source/extensions/miskeyed.xr.python_deps"
    (dependency / "config").mkdir(parents=True, exist_ok=True)
    (dependency / "config/extension.toml").write_text(_DEPS_EXTENSION_TOML, encoding="utf-8")
    (dependency / "premake5.lua").write_text(_DEPS_PREMAKE, encoding="utf-8")
    (dependency / "stubs").mkdir(parents=True, exist_ok=True)
    (dependency / "stubs/dependency.pyi").write_text('"""PyPI prebundle marker."""\n', encoding="utf-8")

    apps = template_root / "source/apps"
    apps.mkdir(parents=True, exist_ok=True)
    (apps / "miskeyed.xr.kit").write_text(_APP_KIT, encoding="utf-8")
    with (template_root / "tools/deps/pip.toml").open("a", encoding="utf-8") as stream:
        stream.write(_PIP_TOML)


def install_kit(root: Path) -> None:
    if not supported_platform():
        raise RuntimeError("NVIDIA Kit SDK is supported by this launcher on Linux and Windows, not macOS")
    if not (root / ".git").exists():
        subprocess.run(["git", "clone", KIT_TEMPLATE_URL, str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "checkout", KIT_TEMPLATE_REVISION], check=True)
    write_project(root)
    command = root / ("repo.bat" if platform.system() == "Windows" else "repo.sh")
    subprocess.run([str(command), "build"], cwd=root, check=True)


def launch(root: Path, extra: list[str]) -> None:
    target, executable = kit_paths(root)
    app = target / "apps/miskeyed.xr.kit"
    if not executable.exists() or not app.exists():
        raise RuntimeError(f"Kit app is not provisioned under {root}; run install-kit first")
    subprocess.run(
        [str(executable), str(app), "--ext-folder", str(target / "exts"),
         "--ext-folder", str(target / "extsbuild"), "--ext-folder", str(target / "extscache"), *extra],
        check=True,
    )


def doctor(root: Path) -> int:
    target, executable = kit_paths(root)
    print(f"platform={platform.system()} architecture={platform.machine()}")
    print(f"kit_supported={supported_platform()}")
    print(f"kit_root={root}")
    print(f"kit_executable={executable} exists={executable.exists()}")
    print(f"core_requirement={CORE_REQUIREMENT} owner=Kit-pip_prebundle")
    return 0 if supported_platform() else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="miskeyed-kit-xr")
    parser.add_argument("--root", type=Path, default=default_install_root())
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("doctor")
    subcommands.add_parser("install-kit")
    launch_parser = subcommands.add_parser("launch")
    launch_parser.add_argument("kit_args", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return doctor(args.root)
        if args.command == "install-kit":
            install_kit(args.root)
        else:
            launch(args.root, args.kit_args)
    except (OSError, RuntimeError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"miskeyed-kit-xr: {exc}\n")
    return 0


_PIP_TOML = f'''\n[[dependency]]\npython = "../../_build/target-deps/python"\npackages = ["{CORE_REQUIREMENT}"]\ntarget = "../../_build/target-deps/pip_prebundle"\nappend_to_install_folder = true\n'''
_DEPS_EXTENSION_TOML = '''[package]\ntitle="Miskeyed XR Python Dependencies"\nversion="0.1.0"\n[[python.module]]\npath="pip_prebundle"\n'''
_DEPS_PREMAKE = '''local ext=get_current_extension_info()\nproject_ext(ext)\nrepo_build.prebuild_link { { "%{root}/_build/target-deps/pip_prebundle", ext.target_dir.."/pip_prebundle" }, { "stubs", ext.target_dir.."/stubs" } }\n'''
_XR_EXTENSION_TOML = '''[package]\ntitle="Miskeyed Kit XR Agent"\nversion="0.1.0"\n[dependencies]\n"miskeyed.xr.python_deps"={}\n"omni.kit.xr.core"={optional=true}\n"omni.usd"={}\n"omni.ui"={optional=true}\n[[python.module]]\nname="miskeyed.kit.xr_agent"\n'''
_XR_PREMAKE = '''local ext=get_current_extension_info()\nproject_ext(ext)\nrepo_build.prebuild_link { { "config", ext.target_dir.."/config" }, { "miskeyed", ext.target_dir.."/miskeyed" } }\n'''
_APP_KIT = '''[package]\ntitle="Miskeyed XR Agent"\nversion="0.1.0"\n[dependencies]\n"omni.usd"={}\n"omni.ui"={}\n"omni.kit.xr.core"={}\n"omni.kit.xr.system.openxr"={}\n"miskeyed.kit.xr_agent"={}\n'''
