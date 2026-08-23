"""PyInstaller hook for the x_ray package.

Collects the dynamically-imported modules of the core ``x_ray`` package.
Analysis plugins (healthcheck, log, ftdc, gmd) ship as separate
``mongo-x-ray-*`` distributions and are not part of this package.
"""

# chromadb resolves its implementation classes by fully-qualified name at
# runtime (see chromadb.config._abstract_type_keys and the SegmentType mapping
# in chromadb.segment.impl.manager.local), so PyInstaller's static analysis
# cannot discover them. Pin the concrete modules used by the embedded
# PersistentClient so the packaged binary keeps working.
hiddenimports = [
    "x_ray.ai_client",
    "x_ray.risk_register.db",
    "x_ray.risk_register.shared",
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
