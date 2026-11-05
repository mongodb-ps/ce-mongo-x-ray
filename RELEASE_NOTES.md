# mongo-x-ray 2.1.1 — Release Notes

**Scope**: v2.1.0 (2026-09-10) → 2.1.1 (2026-11-05)
**TL;DR**: A dependency and automation release. The driver and the tooling move to patched versions — several of them fix security advisories — and the Dependabot pipeline that delivers those updates is repaired. Reports, CLI and API are unchanged.

## Dependencies

- **`pymongo` 4.18.0 → 4.18.3** — the driver update closes five advisories:
  - [`GHSA-98qm-wvgf-w4cf`](https://github.com/advisories/GHSA-98qm-wvgf-w4cf) (CVE-2026-106435, high) — out-of-bounds read in BSON decoding via a malformed Regex element
  - [`GHSA-v4x9-3549-crwv`](https://github.com/advisories/GHSA-v4x9-3549-crwv) (CVE-2026-96749, high) — heap out-of-bounds write via a signed size overflow in BSON encoding
  - [`GHSA-vp6j-j7w5-5xjj`](https://github.com/advisories/GHSA-vp6j-j7w5-5xjj) (CVE-2026-96748, high) — host injection in connection-string parsing via percent-encoded delimiters
  - [`GHSA-qx36-8mw2-4r3x`](https://github.com/advisories/GHSA-qx36-8mw2-4r3x) (CVE-2026-96747, medium) — forced Unix domain socket connection via a `.sock` KMS endpoint
  - [`GHSA-8fvv-fgr5-f8ch`](https://github.com/advisories/GHSA-8fvv-fgr5-f8ch) (CVE-2026-88029, medium) — GridFS `delete` now matches the file ID exactly
- `openai` 3.8.0 → 3.31.0 and `python-dotenv` 1.2.3 → 1.2.4
- Build: `setuptools` 84.0.0 → 84.2.1 ([`GHSA-xmj3-9gf7-h52w`](https://github.com/advisories/GHSA-xmj3-9gf7-h52w), low — Windows path escape via `namespace_packages.txt` during a legacy wheel install)
- Dev tooling: `pylint` 4.0.8 → 4.1.3 ([`GHSA-22qq-2fwx-7p67`](https://github.com/advisories/GHSA-22qq-2fwx-7p67), CVE-2026-114608, medium — arbitrary code execution through the pickled stats cache), `ruff` 0.16.6 → 0.17.1, `pyright` 1.1.411 → 1.1.414, `pyinstaller` 6.22.2 → 6.22.3, `playwright` 1.62.0 → 1.64.1, `pluggy` 1.6.0 → 1.7.0, `iniconfig` 2.3.0 → 2.3.1

## Changed 🔧

- **`make plugin-deps`** installs the published `mongo-x-ray-hc` (`>=2.1.0`) from PyPI instead of a git checkout, so a binary built from source bundles the released healthcheck plugin
- README refinements and a `.vscode` default-formatter tweak

## Development 🔩

- **Dependabot auto-merge repaired**: the workflow waited for "every check to pass" including its own `auto-merge` check, which stays in progress until the job ends — so it always timed out, and updates piled up (ten open pull requests here). It now ignores its own check, retries a merge that lost a race with a sibling update, asks Dependabot to rebase when the branch conflicts, and stays green when a branch was modified by hand
- Repository labels `dependencies`, `python` and `github-actions` were added, so Dependabot can tag its pull requests

## Upgrade Guide (2.1.0 → 2.1.1)

```bash
pip install -U mongo-x-ray mongo-x-ray-log mongo-x-ray-ftdc mongo-x-ray-hc
```

- Drop-in release: no API, CLI or report changes, and no configuration changes
- If you pin `pymongo` yourself, note that the security fixes above only exist in 4.18.3
