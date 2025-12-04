"""PyInstaller hook for x_ray package.

This hook collects all dynamically imported modules from:
- x_ray.healthcheck.check_items (which imports x_ray.healthcheck.rules)
- x_ray.log_analysis.log_items (which imports x_ray.ai when AI enabled)

Control AI support via BUILD_WITH_AI environment variable:
- BUILD_WITH_AI=1: Include AI modules (build-ai)
- BUILD_WITH_AI=0 or unset: Exclude AI modules (build-lite, default)
"""

import os
from PyInstaller.utils.hooks import collect_submodules

# Check if building with AI support
build_with_ai = os.environ.get("BUILD_WITH_AI", "0") == "1"

# Collect all submodules from dynamically loaded packages
hiddenimports = []
hiddenimports += collect_submodules("x_ray.healthcheck.check_items")
hiddenimports += collect_submodules("x_ray.log_analysis.log_items")

# Include AI module only if building with AI support
if build_with_ai:
    excludedimports = []
else:
    excludedimports = [
        "x_ray.ai",
        "torch",
        "transformers",
        "accelerate",
        "bitsandbytes",
        "torchvision",
        "scipy",
        "PIL",
    ]
