"""Shared FTDC metric names and mappings."""

from typing import Final

OPCOUNTER_METRICS: Final = {
    name: f"serverStatus.opcounters.{name}" for name in ("query", "insert", "update", "delete", "command", "getmore")
}

OPCOUNTER_REPL_METRICS: Final = {
    name: f"serverStatus.opcountersRepl.{name}"
    for name in ("query", "insert", "update", "delete", "command", "getmore")
}

OP_LATENCY_METRICS: Final = {
    operation: {
        "ops": f"serverStatus.opLatencies.{operation}.ops",
        "latency": f"serverStatus.opLatencies.{operation}.latency",
        "queryable_encryption_latency": (f"serverStatus.opLatencies.{operation}.queryableEncryptionLatencyMicros"),
    }
    for operation in ("reads", "writes", "commands", "transactions")
}

CPU_METRICS: Final = {
    "boot_time": "systemMetrics.cpu.btime",
    "context_switches": "systemMetrics.cpu.ctxt",
    "guest": "systemMetrics.cpu.guest_ms",
    "guest_nice": "systemMetrics.cpu.guest_nice_ms",
    "idle": "systemMetrics.cpu.idle_ms",
    "iowait": "systemMetrics.cpu.iowait_ms",
    "irq": "systemMetrics.cpu.irq_ms",
    "nice": "systemMetrics.cpu.nice_ms",
    "available_cores": "systemMetrics.cpu.num_cores_available_to_process",
    "logical_cores": "systemMetrics.cpu.num_logical_cores",
    "processes": "systemMetrics.cpu.processes",
    "blocked_processes": "systemMetrics.cpu.procs_blocked",
    "running_processes": "systemMetrics.cpu.procs_running",
    "softirq": "systemMetrics.cpu.softirq_ms",
    "steal": "systemMetrics.cpu.steal_ms",
    "system": "systemMetrics.cpu.system_ms",
    "user": "systemMetrics.cpu.user_ms",
}

MEMORY_METRICS: Final = {
    "active": "systemMetrics.memory.Active_kb",
    "active_anonymous": "systemMetrics.memory.Active(anon)_kb",
    "active_file": "systemMetrics.memory.Active(file)_kb",
    "anonymous_huge_pages": "systemMetrics.memory.AnonHugePages_kb",
    "buffers": "systemMetrics.memory.Buffers_kb",
    "cached": "systemMetrics.memory.Cached_kb",
    "dirty": "systemMetrics.memory.Dirty_kb",
    "inactive": "systemMetrics.memory.Inactive_kb",
    "inactive_anonymous": "systemMetrics.memory.Inactive(anon)_kb",
    "inactive_file": "systemMetrics.memory.Inactive(file)_kb",
    "available": "systemMetrics.memory.MemAvailable_kb",
    "free": "systemMetrics.memory.MemFree_kb",
    "total": "systemMetrics.memory.MemTotal_kb",
    "swap_cached": "systemMetrics.memory.SwapCached_kb",
    "swap_free": "systemMetrics.memory.SwapFree_kb",
    "swap_total": "systemMetrics.memory.SwapTotal_kb",
}

TCMALLOC_METRICS: Final = {
    "bytes_in_use_by_app": "serverStatus.tcmalloc.generic.bytes_in_use_by_app",
    "current_allocated_bytes": "serverStatus.tcmalloc.generic.current_allocated_bytes",
    "heap_size": "serverStatus.tcmalloc.generic.heap_size",
    "peak_memory_usage": "serverStatus.tcmalloc.generic.peak_memory_usage",
    "physical_memory_used": "serverStatus.tcmalloc.generic.physical_memory_used",
    "virtual_memory_used": "serverStatus.tcmalloc.generic.virtual_memory_used",
    "total_free_bytes": "serverStatus.tcmalloc.tcmalloc_derived.total_free_bytes",
    "unmapped_bytes": "serverStatus.tcmalloc.tcmalloc_derived.unmapped_bytes",
}

WIREDTIGER_CACHE_METRICS: Final = {
    "bytes_allocated_for_updates": "serverStatus.wiredTiger.cache.bytes allocated for updates",
    "bytes_current": "serverStatus.wiredTiger.cache.bytes currently in the cache",
    "bytes_dirty_cumulative": "serverStatus.wiredTiger.cache.bytes dirty in the cache cumulative",
    "bytes_maximum": "serverStatus.wiredTiger.cache.maximum bytes configured",
    "pages_current": "serverStatus.wiredTiger.cache.pages currently held in the cache",
    "tracked_dirty_bytes": "serverStatus.wiredTiger.cache.tracked dirty bytes in the cache",
    "tracked_dirty_pages": "serverStatus.wiredTiger.cache.tracked dirty pages in the cache",
}

DISK_METRIC_PREFIX: Final = "systemMetrics.disks."
DISK_METRICS: Final = {
    "io_in_progress": "io_in_progress",
    "io_queued_ms": "io_queued_ms",
    "io_time_ms": "io_time_ms",
    "read_sectors": "read_sectors",
    "read_time_ms": "read_time_ms",
    "reads": "reads",
    "reads_merged": "reads_merged",
    "write_sectors": "write_sectors",
    "write_time_ms": "write_time_ms",
    "writes": "writes",
    "writes_merged": "writes_merged",
}

MOUNT_METRIC_PREFIX: Final = "systemMetrics.mounts."
MOUNT_METRICS: Final = {
    "available": "available",
    "capacity": "capacity",
    "free": "free",
}

# The static subset currently required by OverviewItem. Dynamic disk and mount
# names are selected using the prefixes and suffix mappings above.
OVERVIEW_STATIC_METRICS: Final = {
    CPU_METRICS["available_cores"],
    CPU_METRICS["user"],
    CPU_METRICS["system"],
    CPU_METRICS["iowait"],
    MEMORY_METRICS["total"],
    MEMORY_METRICS["available"],
    TCMALLOC_METRICS["heap_size"],
    TCMALLOC_METRICS["current_allocated_bytes"],
    WIREDTIGER_CACHE_METRICS["bytes_current"],
    WIREDTIGER_CACHE_METRICS["tracked_dirty_bytes"],
    WIREDTIGER_CACHE_METRICS["bytes_maximum"],
    *OPCOUNTER_METRICS.values(),
    *(
        metric
        for operation in ("reads", "writes")
        for metric in (
            OP_LATENCY_METRICS[operation]["ops"],
            OP_LATENCY_METRICS[operation]["latency"],
        )
    ),
}
