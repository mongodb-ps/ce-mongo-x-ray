"""Tests for command plugin discovery and the dev plugins/ override."""

from mongo_x_ray.plugins import _load_local_plugin, _plugins_folder, discover_plugins

# The fake plugin modules created in tmp folders are dynamic by design.
# pylint: disable=import-outside-toplevel


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
    assert _load_local_plugin(root / "not-a-plugin") is None


def test_local_plugin_is_discovered(monkeypatch, tmp_path):
    _make_local_plugin(tmp_path, "demo", "demo")
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(tmp_path / "plugins"))
    plugins = discover_plugins()
    assert plugins["demo"].name == "demo"


def test_local_plugin_overrides_installed(monkeypatch, tmp_path):
    # A local checkout claiming the name "ftdc" wins over the installed one.
    _make_local_plugin(tmp_path, "fake-ftdc", "ftdc")
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(tmp_path / "plugins"))
    plugins = discover_plugins()
    assert type(plugins["ftdc"]).__module__ == "mongo_x_ray_fake_ftdc.plugin"
    assert plugins["ftdc"].help == "local"
    # other installed plugins are still discovered from entry points
    assert {"log", "gmd", "healthcheck"} <= set(plugins)


def test_falls_back_to_installed_when_plugins_folder_empty(monkeypatch, tmp_path):
    empty = tmp_path / "plugins"
    empty.mkdir()
    monkeypatch.setenv("MONGO_X_RAY_PLUGINS", str(empty))
    plugins = discover_plugins()
    assert {"ftdc", "log", "gmd", "healthcheck"} <= set(plugins)


def test_subcommand_alias_resolves_to_plugin():
    from mongo_x_ray.__main__ import resolve_plugin

    plugins = discover_plugins()
    plugin = resolve_plugin(plugins, "hc")
    assert plugin is not None
    assert plugin.name == "healthcheck"
    # canonical name and unknown names behave as expected
    assert resolve_plugin(plugins, "healthcheck") is plugin
    assert resolve_plugin(plugins, "does-not-exist") is None
