# mongo-x-ray 2.0.0 — Release Notes

**Scope**: v1.5.3 (2026-08-19) → 2.0.0 (2026-08-31, 68 commits)
**TL;DR**: Re-architected from a monolith into a **core + plugin (`mongo-x-ray-*`)** model, with security hardening, packaging and engineering improvements.

## Breaking Changes ⚠️

- **Plugin architecture**: analysis features were extracted from the core into separate `mongo-x-ray-*` plugin packages. `pip install mongo-x-ray` alone no longer provides any commands — you must also install the plugins you need (e.g. `mongo-x-ray-log`, `mongo-x-ray-ftdc`)
- **Import package rename**: `x_ray` → `mongo_x_ray` (update imports in any code referencing the core)
- **Prebuilt binaries**: ship with the `log` and `ftdc` plugins bundled; other functionality is available via `pip`-installed plugins or a custom build
- **MongoDB 5.0+** is now the documented minimum; the compatibility matrix was removed

## New Features ✨

- **Dynamic CLI from plugin discovery**: the command list is built from the installed plugins at startup; `--help` shows what is available, and subcommand aliases are supported (`healthcheck` / `hc`)
- **Per-plugin `--version`**: `x-ray <command> --version` reports the plugin's own version
- **Library-plugin detection**: packages that register no CLI command are detected and listed in `--help`
- **Security hardening**: plugin loading is gated on the **install origin** (local editable installs, trusted git owners, allow-listed PyPI packages); untrusted plugins are skipped with a warning
- **Packaging**: the PyInstaller build automatically bundles every plugin installed in the build environment; the frozen binary only uses bundled plugins and never probes externally installed ones

## Refactoring / Architecture 🏗️

- Split out separate plugin repositories: `mongo-x-ray-log`, `mongo-x-ray-ftdc` (see below)
- Shared components consolidated in core: a unified `BaseFramework`, `BaseParser`, `shared` utilities, and a shared issue catalog (`mongo_x_ray.issues`)
- Runtime dependencies trimmed from 23 to 5 (pymongo / Markdown / openai / python-dotenv / WeasyPrint)

## Tooling / CI / Quality 🔧

- **ruff fully replaces pylint + black** (editor + lint gate), with matching VSCode recommendations
- pyright `typeCheckingMode=basic` with type fixes; explicit isort `known-first-party` config eliminates cross-workspace import-order differences
- **CodeQL enabled on all repositories**; all alerts fixed (uninitialized variables, mixed returns, …)
- Copyright header script (`misc/add_copyright.sh`): scans core sources, unifies/adds headers, auto-updates the year, and produces format-clean output
- Dependency updates: openai → 3.5.0, ruff → 0.16.5, pyinstaller, pygments, idna, python-dotenv, …

## New Repositories 📦

| Repository | Description |
|---|---|
| `mongo-x-ray-log` | MongoDB log analysis (with AI-assisted analysis) |
| `mongo-x-ray-ftdc` | FTDC analysis |

## Upgrade Guide (1.5.3 → 2.0.0)

```bash
pip install mongo-x-ray mongo-x-ray-log mongo-x-ray-ftdc
```

- Rename `x_ray.*` imports to `mongo_x_ray.*`
- Binary users: download the prebuilt binary (ships with `log` and `ftdc`); build your own with `make plugin-deps` + `make build` to bundle additional installed plugins
