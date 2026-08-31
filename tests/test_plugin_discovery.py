"""
Copyright (c) 2026 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.

Tests for command plugin discovery and the dev plugins/ override.
"""

import pytest

from mongo_x_ray.plugins import _load_local_plugins, _plugins_folder, discover_plugins

# The fake plugin modules created in tmp folders are dynamic by design.


def _make_local_plugin(root, checkout_name, plugin_name):
    """Create a minimal plugin checkout under ``root/plugins/<checkout_name>``."""
    pkg = root / "plugins" / checkout_name / "src" / f"mongo_x_ray_{checkout_name.replace('-', '_')}"
    pkg.mkdir(parents=True)
    (pkg / "plugin.py").write_text(
        f"""\
from mongo_x_ray.plugin import Plugin


class LocalPlugin(Plugin):
    name = {plugin_name!r}
    help = "local"

    def run(self, args):
        return 0
""",
        encoding="utf-8",
    )
    return root / "plugins" / checkout_name


def test_plugins_folder_defaults_to_core_repo_plugins():
    folder = _plugins_folder()
    assert folder.name == "plugins"
    # the default folder is the core repository's plugins/ directory
    assert (folder.parent / "pyproject.toml").is_file()


def test_load_local_plugin_skips_dirs_without_src(tmp_path):
    root = tmp_path / "plugins"
    (root / "not-a-plugin").mkdir(parents=True)
    assert _load_local_plugins(root / "not-a-plugin") == []


def test_local_plugin_is_discovered(monkeypatch, tmp_path):
    _make_local_plugin(tmp_path, "demo", "demo")
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(tmp_path / "plugins"))
    plugins = discover_plugins()
    assert plugins["demo"].name == "demo"


def test_local_checkout_with_multiple_plugins_registers_all(monkeypatch, tmp_path):
    checkout = tmp_path / "plugins" / "mongo-x-ray-multi"
    pkg = checkout / "src" / "mongo_x_ray_multi"
    pkg.mkdir(parents=True)
    (pkg / "plugin.py").write_text(
        "from mongo_x_ray.plugin import Plugin\n"
        "class FirstPlugin(Plugin):\n"
        "    name = 'first'\n"
        "    def run(self, args):\n"
        "        return 0\n"
        "class SecondPlugin(Plugin):\n"
        "    name = 'second'\n"
        "    def run(self, args):\n"
        "        return 0\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(tmp_path / "plugins"))
    plugins = discover_plugins()
    assert {"first", "second"} <= set(plugins)


def _installed_command_names():
    """Command names contributed by the installed mongo-x-ray-* plugins."""
    from mongo_x_ray import plugins as plugins_mod
    from mongo_x_ray.plugin import ENTRY_POINT_GROUP

    return {
        ep.name
        for dist in plugins_mod._distributions()
        for ep in dist.entry_points
        if ep.group == ENTRY_POINT_GROUP
    }


def test_local_plugin_overrides_installed(monkeypatch, tmp_path):
    # A local checkout claiming the name "ftdc" wins over the installed one.
    _make_local_plugin(tmp_path, "fake-ftdc", "ftdc")
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(tmp_path / "plugins"))
    plugins = discover_plugins()
    assert type(plugins["ftdc"]).__module__ == "mongo_x_ray_fake_ftdc.plugin"
    assert plugins["ftdc"].help == "local"
    # other installed plugins are still discovered from entry points
    assert _installed_command_names() <= set(plugins)


def test_falls_back_to_installed_when_plugins_folder_empty(monkeypatch, tmp_path):
    empty = tmp_path / "plugins"
    empty.mkdir()
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(empty))
    plugins = discover_plugins()
    # with no local checkouts the command set is exactly the installed plugins
    assert set(plugins) == _installed_command_names()


def test_subcommand_alias_resolves_to_plugin():
    pytest.importorskip("mongo_x_ray_hc")

    from mongo_x_ray.__main__ import resolve_plugin

    plugins = discover_plugins()
    plugin = resolve_plugin(plugins, "hc")
    assert plugin is not None
    assert plugin.name == "healthcheck"
    # canonical name and unknown names behave as expected
    assert resolve_plugin(plugins, "healthcheck") is plugin
    assert resolve_plugin(plugins, "does-not-exist") is None


def test_plugin_version_requested_and_version(monkeypatch, tmp_path):
    pytest.importorskip("mongo_x_ray_ftdc")

    # Isolate from the real plugins/ checkouts: only installed entry points.
    empty = tmp_path / "plugins"
    empty.mkdir()
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(empty))

    from importlib.metadata import version as pkg_version

    from mongo_x_ray.__main__ import _plugin_version_requested

    plugin = _plugin_version_requested(["x-ray", "ftdc", "--version"])
    assert plugin is not None
    assert plugin.version() == pkg_version(plugin.distribution)
    # a bare --version is the core version, not a plugin's
    assert _plugin_version_requested(["x-ray", "--version"]) is None
    # --version must come after the subcommand
    assert _plugin_version_requested(["x-ray", "ftdc", "/tmp/data"]) is None


def test_local_library_package_is_detected_and_importable(monkeypatch, tmp_path):
    from mongo_x_ray.plugins import _local_import_packages

    # A library checkout with no plugin.py (like the risk register).
    pkg = tmp_path / "plugins" / "mongo-x-ray-lib" / "src" / "mongo_x_ray_lib"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("VALUE = 42\n", encoding="utf-8")

    checkout = tmp_path / "plugins" / "mongo-x-ray-lib"
    assert [p.name for p in _local_import_packages(checkout)] == ["mongo_x_ray_lib"]

    # discover_plugins() must put the library src on sys.path so other plugins
    # import the local checkout.
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(tmp_path / "plugins"))
    discover_plugins()

    import mongo_x_ray_lib  # type: ignore[import-not-found]  # created at runtime in tmp_path

    assert mongo_x_ray_lib.VALUE == 42


def test_discover_library_plugins_lists_only_commandless_packages(monkeypatch, tmp_path):
    from types import SimpleNamespace

    from mongo_x_ray import plugins as plugins_mod
    from mongo_x_ray.plugin import ENTRY_POINT_GROUP

    class FakeDist:
        def __init__(self, name, summary, has_command=False):
            self.metadata = {"Name": name, "Summary": summary}
            self.entry_points = [SimpleNamespace(group=ENTRY_POINT_GROUP)] if has_command else []

    fake_dists = [
        FakeDist("mongo-x-ray", "MongoDB analysis and diagnostics"),
        FakeDist("mongo-x-ray-ftdc", "FTDC analysis plugin for x-ray", has_command=True),
        FakeDist(
            "mongo-x-ray-risk",
            "Known-risks knowledge base (ChromaDB vector search) for x-ray",
            has_command=True,  # the risk register ships the ingest command
        ),
        FakeDist("mongo-x-ray-lib", "A pure library plugin"),
        FakeDist("unrelated-pkg", "Not an x-ray plugin"),
    ]
    monkeypatch.setattr(plugins_mod, "distributions", lambda: fake_dists)
    monkeypatch.setattr(plugins_mod, "_plugins_folder", lambda: tmp_path)

    library = plugins_mod.discover_library_plugins()
    # command plugins (including the risk register's ingest) are not library plugins
    assert library == {"lib": "A pure library plugin"}


def test_risk_ingest_command_is_discovered():
    pytest.importorskip("mongo_x_ray_risk")

    from mongo_x_ray.plugins import discover_plugins

    plugins = discover_plugins()
    assert "ingest" in plugins
    assert plugins["ingest"].distribution == "mongo-x-ray-risk"
    assert "CSV" in plugins["ingest"].help


# --- trust gating for installed plugins -------------------------------------


def test_is_trusted_accepts_editable_and_trusted_git(monkeypatch):
    from mongo_x_ray import plugins as plugins_mod

    monkeypatch.delenv(plugins_mod.TRUST_ALL_ENV, raising=False)
    assert plugins_mod._is_trusted("mongo-x-ray-ftdc", "local editable: file:///home/dev/mongo-x-ray-ftdc")
    assert plugins_mod._is_trusted(
        "mongo-x-ray-search", "vcs(git): https://github.com/zhangyaoxing/mongo-x-ray-search.git"
    )
    assert plugins_mod._is_trusted("mongo-x-ray-ftdc", "vcs(git): git@github.com:mongodb-ps/ce-mongo-x-ray.git")


def test_is_trusted_allowlisted_names_trusted_from_pypi(monkeypatch):
    from mongo_x_ray import plugins as plugins_mod

    monkeypatch.delenv(plugins_mod.TRUST_ALL_ENV, raising=False)
    # pip index installs have no direct_url.json; archive/unknown origins of
    # canonical names are trusted once the official package owns the name.
    assert plugins_mod._is_trusted("mongo-x-ray-ftdc", "unknown (no direct_url.json)")
    assert plugins_mod._is_trusted(
        "mongo-x-ray-ftdc", "archive: https://files.pythonhosted.org/packages/.../mongo_x_ray_ftdc.whl"
    )
    assert plugins_mod._is_trusted("mongo-x-ray-risk", "unknown (unparsable direct_url.json)")


def test_is_trusted_rejects_non_allowlisted_and_evil_origins(monkeypatch):
    from mongo_x_ray import plugins as plugins_mod

    monkeypatch.delenv(plugins_mod.TRUST_ALL_ENV, raising=False)
    # typosquat names outside the allowlist are refused even from PyPI
    assert not plugins_mod._is_trusted("mongo-x-ray-evil", "unknown (no direct_url.json)")
    assert not plugins_mod._is_trusted(
        "mongo-x-ray-evil", "archive: https://files.pythonhosted.org/packages/.../mongo_x_ray_evil.whl"
    )
    # a git fork of a canonical name from an untrusted owner is refused
    assert not plugins_mod._is_trusted(
        "mongo-x-ray-ftdc", "vcs(git): https://github.com/evil-user/mongo-x-ray-ftdc.git"
    )


def test_is_trusted_env_bypass(monkeypatch):
    from mongo_x_ray import plugins as plugins_mod

    monkeypatch.setenv(plugins_mod.TRUST_ALL_ENV, "1")
    assert plugins_mod._is_trusted("mongo-x-ray-evil", "unknown (no direct_url.json)")


def test_dist_origin_parses_direct_url(tmp_path, monkeypatch):
    import json
    from importlib.metadata import Distribution
    from typing import cast

    from mongo_x_ray import plugins as plugins_mod

    def origin_of(dist: object) -> str:
        return plugins_mod._dist_origin(cast(Distribution, dist))

    class FakeDist:
        def __init__(self, direct_url):
            self._direct_url = direct_url

        def read_text(self, filename):
            if filename != "direct_url.json" or self._direct_url is None:
                raise FileNotFoundError(filename)
            return self._direct_url

    editable = FakeDist(json.dumps({"url": "file:///home/dev/x", "dir_info": {"editable": True}}))
    assert origin_of(editable).startswith("local editable")

    git = FakeDist(
        json.dumps({"url": "https://github.com/zhangyaoxing/mongo-x-ray-risk.git", "vcs_info": {"vcs": "git"}})
    )
    assert origin_of(git).startswith("vcs(git)")

    archive = FakeDist(json.dumps({"url": "https://files.pythonhosted.org/pkg.whl", "archive_info": {"hash": "x"}}))
    assert origin_of(archive).startswith("archive")

    assert origin_of(FakeDist(None)) == "unknown (no direct_url.json)"


def test_untrusted_entry_point_command_is_skipped_without_import(monkeypatch, tmp_path, caplog):
    from types import SimpleNamespace

    from mongo_x_ray import plugins as plugins_mod
    from mongo_x_ray.plugin import ENTRY_POINT_GROUP

    def never_loaded():
        raise AssertionError("entry point must not be imported")

    class FakeDist:
        def __init__(self, name):
            self.metadata = {"Name": name, "Summary": "x"}
            self.entry_points = [
                SimpleNamespace(group=ENTRY_POINT_GROUP, name="evil", load=never_loaded),
            ]

        def read_text(self, filename):
            raise FileNotFoundError(filename)

    monkeypatch.setattr(plugins_mod, "distributions", lambda: [FakeDist("mongo-x-ray-evil")])
    monkeypatch.setattr(plugins_mod, "_plugins_folder", lambda: tmp_path)
    monkeypatch.delenv(plugins_mod.TRUST_ALL_ENV, raising=False)

    plugins = plugins_mod.discover_plugins()
    assert "evil" not in plugins
    assert "Skipping untrusted plugin" in caplog.text


def test_local_checkout_egg_info_dist_is_ignored(monkeypatch, tmp_path, caplog):
    from types import SimpleNamespace

    from mongo_x_ray import plugins as plugins_mod
    from mongo_x_ray.plugin import ENTRY_POINT_GROUP

    checkout = tmp_path / "plugins" / "mongo-x-ray-ftdc"
    (checkout / "src").mkdir(parents=True)

    def never_loaded():
        raise AssertionError("entry point must not be imported")

    class FakeDist:
        def __init__(self, name):
            self.metadata = {"Name": name, "Summary": "x"}
            self.entry_points = [SimpleNamespace(group=ENTRY_POINT_GROUP, name="ftdc", load=never_loaded)]

        def locate_file(self, name):
            return checkout / "src"

        def read_text(self, filename):
            raise FileNotFoundError(filename)

    monkeypatch.setattr(plugins_mod, "distributions", lambda: [FakeDist("mongo-x-ray-ftdc")])
    monkeypatch.setattr(plugins_mod, "_plugins_folder", lambda: tmp_path / "plugins")
    monkeypatch.delenv(plugins_mod.TRUST_ALL_ENV, raising=False)

    plugins = plugins_mod.discover_plugins()
    # The egg-info build artifact of a local checkout is ignored without a
    # trust warning: it is the same code as the (trusted) local checkout.
    assert "ftdc" not in plugins
    assert "Skipping untrusted" not in caplog.text


def test_frozen_discovery_skips_local_scan_and_trust_gate(monkeypatch, tmp_path, caplog):
    import sys
    from types import SimpleNamespace

    from mongo_x_ray import plugins as plugins_mod
    from mongo_x_ray.plugin import ENTRY_POINT_GROUP, Plugin

    class EvilPlugin(Plugin):
        name = "evil"
        help = "bundled"

        def run(self, args):
            return 0

    class FakeDist:
        def __init__(self, name):
            self.metadata = {"Name": name, "Summary": "x"}
            self.entry_points = [SimpleNamespace(group=ENTRY_POINT_GROUP, name="evil", load=lambda: EvilPlugin)]

        def read_text(self, filename):
            raise FileNotFoundError(filename)

    # A local checkout that must NOT be scanned when frozen.
    checkout = tmp_path / "plugins" / "mongo-x-ray-demo"
    pkg = checkout / "src" / "mongo_x_ray_demo"
    pkg.mkdir(parents=True)
    (pkg / "plugin.py").write_text(
        "from mongo_x_ray.plugin import Plugin\n"
        "class LocalPlugin(Plugin):\n"
        "    name = 'local'\n"
        "    def run(self, args):\n"
        "        return 0\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(plugins_mod, "_distributions", lambda: [FakeDist("mongo-x-ray-evil")])
    monkeypatch.setattr(plugins_mod, "_plugins_folder", lambda: tmp_path / "plugins")
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    plugins = plugins_mod.discover_plugins()
    # Bundled entry points are trusted without an origin check...
    assert "evil" in plugins
    # ...and the local checkout scan is skipped entirely.
    assert "local" not in plugins
    assert "Skipping untrusted" not in caplog.text


def test_frozen_library_discovery_trusts_bundled(monkeypatch, tmp_path, caplog):
    import sys

    from mongo_x_ray import plugins as plugins_mod

    class FakeDist:
        def __init__(self, name, summary):
            self.metadata = {"Name": name, "Summary": summary}
            self.entry_points = []

        def read_text(self, filename):
            raise FileNotFoundError(filename)

    monkeypatch.setattr(
        plugins_mod,
        "_distributions",
        lambda: [FakeDist("mongo-x-ray-lib", "A pure library plugin")],
    )
    monkeypatch.setattr(plugins_mod, "_plugins_folder", lambda: tmp_path)
    monkeypatch.setattr(sys, "frozen", True, raising=False)

    library = plugins_mod.discover_library_plugins()
    assert library == {"lib": "A pure library plugin"}
    assert "Untrusted library plugin" not in caplog.text
