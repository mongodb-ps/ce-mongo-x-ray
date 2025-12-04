"""PyInstaller hook for x_ray package.

This hook collects all dynamically imported modules from:
- x_ray.healthcheck.check_items
- x_ray.log_analysis.log_items
"""

from PyInstaller.utils.hooks import collect_submodules

# Collect all submodules from dynamically loaded packages
hiddenimports = []

# Healthcheck check items
hiddenimports += collect_submodules("x_ray.healthcheck.check_items")

# Log analysis log items
hiddenimports += collect_submodules("x_ray.log_analysis.log_items")

# Also collect other dynamically imported modules
hiddenimports += collect_submodules("x_ray.healthcheck.rules")
