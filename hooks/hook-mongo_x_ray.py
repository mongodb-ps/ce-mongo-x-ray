"""PyInstaller hook for the mongo_x_ray package.

Collects the dynamically-imported modules of the core ``mongo_x_ray`` package.
Analysis plugins (healthcheck, log, ftdc, gmd) and the risk-register knowledge
base ship as separate ``mongo-x-ray-*`` distributions and are not part of this
package.
"""

hiddenimports = [
    "mongo_x_ray.ai_client",
]
