# mongo-x-ray 2.1.2 — Release Notes

**Scope**: v2.1.1 → 2.1.2 (2026-11-05)
**TL;DR**: MongoDB 9.0 support in the driver compatibility matrix, and a configurable snapshot history window threshold. Reports, CLI and API are unchanged.

## New Features ✨

- **MongoDB 9.0 in the driver compatibility matrix**: the log plugin's client metadata check now knows the minimum driver versions for 9.0, so a 9.0 deployment flags drivers that are too old for it
- The matrix is written with version strings (`"mongoc": "1.15"`) instead of arrays (`[1, 15]`), matching how the [driver compatibility table](https://www.mongodb.com/docs/drivers/compatibility/) quotes versions, which keeps 100+ entries maintainable by hand

## Changed 🔧

- **Snapshot history window threshold is configurable**: the health check compared `minSnapshotHistoryWindowInSeconds` against a constant. It now reads `min_snapshot_history_window_seconds` from the check item configuration — `healthcheck.item_config.ServerParametersItem` for the health check, and `gmd.item_config.ServerStatusItem` for the gmd plugin, which reuses the rule. The default is unchanged (5 seconds) and the recommendation quoted in the finding follows the configured value

## Documentation

- README: install and plugin notes revised, and the `x-ray` usage line corrected to `{hc,log,ftdc}`

## Upgrade Guide (2.1.1 → 2.1.2)

```bash
pip install -U mongo-x-ray mongo-x-ray-hc mongo-x-ray-log mongo-x-ray-ftdc mongo-x-ray-gmd mongo-x-ray-risk
```

- Drop-in release: no CLI, API or report changes, and no configuration changes are required (the new key defaults to the previous behaviour)
- Upgrade `mongo-x-ray-log` together with `mongo-x-ray`: this release writes the compatibility matrix with version strings, and a log release older than 2.1.2 fails to read it (`ValueError: Invalid version array`)
