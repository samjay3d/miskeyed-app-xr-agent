import hashlib
import json
import zipfile

import pytest

from miskeyed_app_xr_agent import cli
from scripts.prepare_kit_template import prepare


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


def test_prepare_excludes_internal_nvidia_repo_dependencies(tmp_path):
    repo = tmp_path / "repo"
    template = tmp_path / "template"
    (repo / "apps").mkdir(parents=True)
    (repo / "exts").mkdir()
    pip = repo / "kit-template/tools/deps/pip.toml"
    pip.parent.mkdir(parents=True)
    pip.write_text("# app dependencies\n", encoding="utf-8")
    (template / "source").mkdir(parents=True)
    deps = template / "tools/deps"
    deps.mkdir(parents=True)
    (deps / "repo-deps-nv.packman.xml").write_text("internal", encoding="utf-8")
    (deps / "pip.toml").write_text("# KAT dependencies\n", encoding="utf-8")
    (template / "tools/VERSION.md").write_text("old\n", encoding="utf-8")
    (template / "premake5.lua").write_text("", encoding="utf-8")
    (template / "repo.toml").write_text(
        'name = "kit-sdk"\n[repo_precache_exts]\napps = []\n', encoding="utf-8"
    )

    prepare(repo, template, "1.2.3")

    assert not (deps / "repo-deps-nv.packman.xml").exists()
