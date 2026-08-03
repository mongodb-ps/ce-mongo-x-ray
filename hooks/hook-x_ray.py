"""PyInstaller hook for x_ray package.

This hook collects all dynamically imported modules from:
- x_ray.healthcheck.check_items (which imports x_ray.healthcheck.rules)
- x_ray.log_analysis.log_items
- x_ray.ftdc_analysis.ftdc_items
- x_ray.risk_register (ChromaDB vector search)
- x_ray.ai_client (OpenAI API analysis)
"""

from PyInstaller.utils.hooks import collect_submodules

# Collect all submodules from dynamically loaded packages
hiddenimports = []
hiddenimports += collect_submodules("x_ray.healthcheck.check_items")
hiddenimports += collect_submodules("x_ray.log_analysis.log_items")
hiddenimports += collect_submodules("x_ray.ftdc_analysis.ftdc_items")
hiddenimports += collect_submodules("pyftdc")
hiddenimports.append("x_ray.ai_client")
hiddenimports.append("x_ray.risk_register.db")
hiddenimports.append("x_ray.risk_register.shared")

# chromadb resolves its implementation classes by fully-qualified name at
# runtime (see chromadb.config._abstract_type_keys and the SegmentType mapping
# in chromadb.segment.impl.manager.local), so PyInstaller's static analysis
# cannot discover them. Pin the concrete modules used by the embedded
# PersistentClient so the packaged binary keeps working.
hiddenimports += [
    "chromadb.api.rust",
    "chromadb.db.impl.sqlite",
    "chromadb.execution.executor.local",
    "chromadb.quota.simple_quota_enforcer",
    "chromadb.rate_limit.simple_rate_limit",
    "chromadb.segment.impl.manager.local",
    "chromadb.segment.impl.metadata.sqlite",
    "chromadb.segment.impl.vector.local_hnsw",
    "chromadb.segment.impl.vector.local_persistent_hnsw",
    "chromadb.telemetry.product.posthog",
]
