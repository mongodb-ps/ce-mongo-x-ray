"""
Copyright (c) 2026 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.

Environment file (`.env`) loading.

Every entry point funnels through :func:`load_env_file`, which runs before any
module snapshots an environment variable:

* `mongo_x_ray.__init__` calls it when the package is imported, so a run started
  from a terminal, a Makefile target, a VS Code *task* or the test runner behaves
  the same as a debug session;
* `utils` and `ai_client` call it again defensively, `ai_client` because it reads
  `AI_MODEL` at import time.

VS Code's `envFile` (see `.vscode/launch.json`) and variables exported by the
shell/CI always win: the file only supplies defaults (`load_dotenv(override=False)`).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def _candidates() -> list[Path]:
    """Return the `.env` paths to try, nearest directory first.

    The working directory and its parents come first, which is what a developer
    expects when starting the app from anywhere inside the checkout, then the
    package location and its parents so an installed source checkout still finds
    the file when it is started from an unrelated directory.
    """
    directories: list[Path] = []
    cwd = Path.cwd().resolve()
    package = Path(__file__).resolve().parent
    for directory in (cwd, *cwd.parents, package, *package.parents):
        if directory not in directories:
            directories.append(directory)
    return [directory / ".env" for directory in directories]


def load_env_file() -> Optional[Path]:
    """Load the first `.env` file found and return its path.

    Returns ``None`` when no file exists or `python-dotenv` is not installed.
    Variables that are already set are never overwritten.
    """
    try:
        from dotenv import load_dotenv
    except ImportError:
        logger.debug("python-dotenv is not installed; .env is not loaded")
        return None

    for path in _candidates():
        if path.is_file():
            load_dotenv(path, override=False)
            logger.debug("Loaded environment file %s", path)
            return path

    logger.debug("No .env file found")
    return None
