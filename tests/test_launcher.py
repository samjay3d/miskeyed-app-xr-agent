import hashlib
import json
import zipfile

import pytest

from miskeyed_app_xr_agent import cli


def test_platform_contract():
    assert cli.platform_id("Linux", "x86_64") == "linux-x86_64"
    assert cli.platform_id("Windows", "AMD64") == "windows-x86_64"
    with pytest.raises(RuntimeError):
        cli.platform_id("Darwin", "arm64")


def test_release_manifest_url_is_versioned():
    assert cli.manifest_url("1.2.3", "linux-x86_64").endswith(
        "/releases/download/v1.2.3/miskeyed-xr-agent-1.2.3-linux-x86_64.json"
    )


def test_install_is_verified_atomic_and_reused(tmp_path, monkeypatch):
    archive = tmp_path / "source.zip"
    with zipfile.ZipFile(archive, "w") as package:
        package.writestr("kit/kit", "kernel")
        package.writestr("apps/miskeyed.xr.kit", "experience")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    manifest = {
        "schema": 1, "app": "miskeyed-xr-agent", "version": "0.1.0",
        "platform": "linux-x86_64",
        "package": {"url": "https://example.invalid/app.zip", "sha256": digest},
        "launch": {"executable": "kit/kit", "experience": "apps/miskeyed.xr.kit"},
    }
    downloads = []

    def download(url, destination):
        downloads.append(url)
        if url.endswith(".json"):
            destination.write_text(json.dumps(manifest), encoding="utf-8")
        else:
            destination.write_bytes(archive.read_bytes())

    monkeypatch.setattr(cli, "_download", download)
    monkeypatch.setattr(cli, "platform_id", lambda: "linux-x86_64")
    root = tmp_path / "installed"
    installed = cli.install(root)
    assert (installed / ".miskeyed-install.json").is_file()
    assert (installed / "apps/miskeyed.xr.kit").is_file()
    assert cli.install(root) == installed
    assert len(downloads) == 2


def test_bad_checksum_leaves_no_install(tmp_path, monkeypatch):
    manifest = {
        "schema": 1, "app": "miskeyed-xr-agent", "version": "0.1.0",
        "platform": "linux-x86_64",
        "package": {"url": "https://example.invalid/app.zip", "sha256": "0" * 64},
    }
    monkeypatch.setattr(cli, "platform_id", lambda: "linux-x86_64")
    monkeypatch.setattr(cli, "_download", lambda url, path: path.write_text(json.dumps(manifest) if url.endswith(".json") else "bad"))
    root = tmp_path / "installed"
    with pytest.raises(RuntimeError, match="checksum"):
        cli.install(root)
    assert not (root / "0.1.0/linux-x86_64").exists()
