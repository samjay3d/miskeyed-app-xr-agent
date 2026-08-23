import platform

from miskeyed_app_xr_agent import cli


def test_supported_platform_contract():
    assert cli.supported_platform("Linux")
    assert cli.supported_platform("Windows")
    assert not cli.supported_platform("Darwin")


def test_kit_paths_are_platform_specific(tmp_path):
    linux, linux_exe = cli.kit_paths(tmp_path, "Linux")
    windows, windows_exe = cli.kit_paths(tmp_path, "Windows")
    assert linux_exe == linux / "kit/kit"
    assert windows_exe == windows / "kit/kit.exe"


def test_launch_uses_built_app_and_extension_folders(tmp_path, monkeypatch):
    target, executable = cli.kit_paths(tmp_path, platform.system())
    executable.parent.mkdir(parents=True)
    executable.touch()
    (target / "apps").mkdir()
    (target / "apps/miskeyed.xr.kit").touch()
    calls = []
    monkeypatch.setattr(cli.subprocess, "run", lambda command, **kwargs: calls.append((command, kwargs)))
    cli.launch(tmp_path, ["--/app/window/title=Test"])
    assert calls[0][0][0] == str(executable)
    assert str(target / "exts") in calls[0][0]
