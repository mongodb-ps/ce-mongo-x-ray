"""PyInstaller hook for x_ray package.

This hook collects all dynamically imported modules from:
- x_ray.healthcheck.check_items (which imports x_ray.healthcheck.rules)
- x_ray.log_analysis.log_items
- x_ray.ftdc_analysis.ftdc_items
- x_ray.ai (used for OpenAI API analysis)
"""

from PyInstaller.utils.hooks import collect_submodules

# Collect all submodules from dynamically loaded packages
hiddenimports = []
hiddenimports += collect_submodules("x_ray.healthcheck.check_items")
hiddenimports += collect_submodules("x_ray.log_analysis.log_items")
hiddenimports += collect_submodules("x_ray.ftdc_analysis.ftdc_items")
hiddenimports += collect_submodules("pyftdc")
hiddenimports.append("x_ray.ai")
