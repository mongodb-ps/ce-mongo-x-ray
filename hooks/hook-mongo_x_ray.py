"""PyInstaller hook for the ``mongo_x_ray`` package.

Collects the dynamically-imported modules of the core ``mongo_x_ray`` package
and bundles every installed ``mongo-x-ray-*`` plugin.

A frozen binary cannot see site-packages, so plugin discovery through
``importlib.metadata`` (``distributions()`` / ``entry_points()``) only works
inside the binary when the plugin packages *and* their dist-info metadata are
bundled here. Any ``mongo-x-ray-*`` distribution installed in the build
environment at build time is collected: its import packages (so ``ep.load()``
finds the modules) and its dist-info (so entry points, library-plugin listing
and ``x-ray <cmd> --version`` work).
"""

import logging
from importlib.metadata import distributions

from PyInstaller.utils.hooks import collect_all, copy_metadata

logger = logging.getLogger(__name__)

hiddenimports = [
    "mongo_x_ray.ai_client",
]
datas: list = []
binaries: list = []

for dist in distributions():
    try:
        name = dist.metadata["Name"]
    except KeyError:
        continue
    if name == "mongo-x-ray":
        # Core's own dist-info so `x-ray --version` reports the real version.
        datas += copy_metadata("mongo-x-ray")
        continue
    if not name.startswith("mongo-x-ray-"):
        continue
    top_level = dist.read_text("top_level.txt") or ""
    for pkg in (part for part in top_level.split() if part):
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    datas += copy_metadata(name)
    logger.info("Bundling plugin %s (%s)", name, top_level.strip())
