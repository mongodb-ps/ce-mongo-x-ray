"""Shared FTDC metric names and mappings."""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class Metric:
    """An FTDC metric key and its user-facing name."""

    name: str
    key: str


OPCOUNTER_METRICS: Final = {
    key: Metric(name, f"serverStatus.opcounters.{key}")
    for key, name in (
        ("query", "Query"),
        ("insert", "Insert"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("command", "Command"),
        ("getmore", "GetMore"),
    )
}

OPCOUNTER_REPL_METRICS: Final = {
    key: Metric(f"Replication {metric.name.lower()}", f"serverStatus.opcountersRepl.{key}")
    for key, metric in OPCOUNTER_METRICS.items()
}

OP_LATENCY_METRICS: Final = {
    operation: {
        "ops": Metric(f"{name} operations", f"serverStatus.opLatencies.{operation}.ops"),
        "latency": Metric(f"{singular} latency", f"serverStatus.opLatencies.{operation}.latency"),
        "queryable_encryption_latency": Metric(
            f"{singular} queryable encryption latency",
            f"serverStatus.opLatencies.{operation}.queryableEncryptionLatencyMicros",
        ),
    }
    for operation, name, singular in (
        ("reads", "Read", "Read"),
        ("writes", "Write", "Write"),
        ("commands", "Command", "Command"),
        ("transactions", "Transaction", "Transaction"),
    )
}

CPU_METRICS: Final = {
    "boot_time": Metric("System boot time", "systemMetrics.cpu.btime"),
    "context_switches": Metric("CPU context switches", "systemMetrics.cpu.ctxt"),
    "guest": Metric("CPU guest", "systemMetrics.cpu.guest_ms"),
    "guest_nice": Metric("CPU guest nice", "systemMetrics.cpu.guest_nice_ms"),
    "idle": Metric("CPU idle", "systemMetrics.cpu.idle_ms"),
    "iowait": Metric("CPU I/O wait", "systemMetrics.cpu.iowait_ms"),
    "irq": Metric("CPU hardware interrupt", "systemMetrics.cpu.irq_ms"),
    "nice": Metric("CPU nice", "systemMetrics.cpu.nice_ms"),
    "available_cores": Metric(
        "CPU cores available to the process",
        "systemMetrics.cpu.num_cores_available_to_process",
    ),
    "logical_cores": Metric("Logical CPU cores", "systemMetrics.cpu.num_logical_cores"),
    "processes": Metric("Processes created", "systemMetrics.cpu.processes"),
    "blocked_processes": Metric("Blocked processes", "systemMetrics.cpu.procs_blocked"),
    "running_processes": Metric("Running processes", "systemMetrics.cpu.procs_running"),
    "softirq": Metric("CPU software interrupt", "systemMetrics.cpu.softirq_ms"),
    "steal": Metric("CPU steal", "systemMetrics.cpu.steal_ms"),
    "system": Metric("CPU system", "systemMetrics.cpu.system_ms"),
    "user": Metric("CPU user", "systemMetrics.cpu.user_ms"),
}

MEMORY_METRICS: Final = {
    "active": Metric("Active memory", "systemMetrics.memory.Active_kb"),
    "active_anonymous": Metric("Active anonymous memory", "systemMetrics.memory.Active(anon)_kb"),
    "active_file": Metric("Active file-backed memory", "systemMetrics.memory.Active(file)_kb"),
    "anonymous_huge_pages": Metric("Anonymous huge pages", "systemMetrics.memory.AnonHugePages_kb"),
    "buffers": Metric("Buffer memory", "systemMetrics.memory.Buffers_kb"),
    "cached": Metric("Cached memory", "systemMetrics.memory.Cached_kb"),
    "dirty": Metric("Dirty memory", "systemMetrics.memory.Dirty_kb"),
    "inactive": Metric("Inactive memory", "systemMetrics.memory.Inactive_kb"),
    "inactive_anonymous": Metric("Inactive anonymous memory", "systemMetrics.memory.Inactive(anon)_kb"),
    "inactive_file": Metric("Inactive file-backed memory", "systemMetrics.memory.Inactive(file)_kb"),
    "available": Metric("Available system memory", "systemMetrics.memory.MemAvailable_kb"),
    "free": Metric("Free system memory", "systemMetrics.memory.MemFree_kb"),
    "total": Metric("Total system memory", "systemMetrics.memory.MemTotal_kb"),
    "swap_cached": Metric("Cached swap", "systemMetrics.memory.SwapCached_kb"),
    "swap_free": Metric("Free swap", "systemMetrics.memory.SwapFree_kb"),
    "swap_total": Metric("Total swap", "systemMetrics.memory.SwapTotal_kb"),
}

TCMALLOC_METRICS: Final = {
    "bytes_in_use_by_app": Metric(
        "TCMalloc bytes in use by the application",
        "serverStatus.tcmalloc.generic.bytes_in_use_by_app",
    ),
    "current_allocated_bytes": Metric(
        "TCMalloc currently allocated bytes",
        "serverStatus.tcmalloc.generic.current_allocated_bytes",
    ),
    "heap_size": Metric("TCMalloc heap size", "serverStatus.tcmalloc.generic.heap_size"),
    "peak_memory_usage": Metric("TCMalloc peak memory usage", "serverStatus.tcmalloc.generic.peak_memory_usage"),
    "physical_memory_used": Metric(
        "TCMalloc physical memory used",
        "serverStatus.tcmalloc.generic.physical_memory_used",
    ),
    "virtual_memory_used": Metric(
        "TCMalloc virtual memory used",
        "serverStatus.tcmalloc.generic.virtual_memory_used",
    ),
    "total_free_bytes": Metric(
        "TCMalloc total free bytes",
        "serverStatus.tcmalloc.tcmalloc_derived.total_free_bytes",
    ),
    "unmapped_bytes": Metric(
        "TCMalloc unmapped bytes",
        "serverStatus.tcmalloc.tcmalloc_derived.unmapped_bytes",
    ),
}

WIREDTIGER_CACHE_METRICS: Final = {
    "bytes_allocated_for_updates": Metric(
        "WiredTiger cache bytes allocated for updates",
        "serverStatus.wiredTiger.cache.bytes allocated for updates",
    ),
    "bytes_current": Metric(
        "WiredTiger bytes currently in cache",
        "serverStatus.wiredTiger.cache.bytes currently in the cache",
    ),
    "bytes_dirty_cumulative": Metric(
        "WiredTiger cumulative dirty cache bytes",
        "serverStatus.wiredTiger.cache.bytes dirty in the cache cumulative",
    ),
    "bytes_maximum": Metric(
        "WiredTiger maximum configured cache bytes",
        "serverStatus.wiredTiger.cache.maximum bytes configured",
    ),
    "pages_current": Metric(
        "WiredTiger pages currently in cache",
        "serverStatus.wiredTiger.cache.pages currently held in the cache",
    ),
    "tracked_dirty_bytes": Metric(
        "WiredTiger dirty bytes in cache",
        "serverStatus.wiredTiger.cache.tracked dirty bytes in the cache",
    ),
    "tracked_dirty_pages": Metric(
        "WiredTiger dirty pages in cache",
        "serverStatus.wiredTiger.cache.tracked dirty pages in the cache",
    ),
}

DISK_METRIC_PREFIX: Final = "systemMetrics.disks."
DISK_METRICS: Final = {
    "io_in_progress": Metric("Disk queue length", "io_in_progress"),
    "io_queued_ms": Metric("Disk queued I/O time", "io_queued_ms"),
    "io_time_ms": Metric("Disk I/O time", "io_time_ms"),
    "read_sectors": Metric("Disk sectors read", "read_sectors"),
    "read_time_ms": Metric("Disk read time", "read_time_ms"),
    "reads": Metric("Disk reads", "reads"),
    "reads_merged": Metric("Merged disk reads", "reads_merged"),
    "write_sectors": Metric("Disk sectors written", "write_sectors"),
    "write_time_ms": Metric("Disk write time", "write_time_ms"),
    "writes": Metric("Disk writes", "writes"),
    "writes_merged": Metric("Merged disk writes", "writes_merged"),
}

MOUNT_METRIC_PREFIX: Final = "systemMetrics.mounts."
MOUNT_METRICS: Final = {
    "available": Metric("Disk available", "available"),
    "capacity": Metric("Disk capacity", "capacity"),
    "free": Metric("Disk free", "free"),
}

REPL_SET_MEMBER_METRIC_PREFIX: Final = "replSetGetStatus.members."
REPL_SET_MEMBER_METRICS: Final = {
    "state": Metric("Replica set member state", "state"),
    "self": Metric("Local replica set member", "self"),
}

DERIVED_METRIC_NAMES: Final = {
    "system_memory_utilization": "System memory utilization",
    "memory_fragmentation_ratio": "Memory fragmentation ratio",
    "cache_fill": "Cache fill",
    "cache_dirty": "Cache dirty",
    "disk_utilization": "Disk utilization",
}

# The static subset currently required by OverviewItem. Dynamic disk and mount
# names are selected using the prefixes and suffix mappings above.
OVERVIEW_STATIC_METRICS: Final = {
    CPU_METRICS["available_cores"].key,
    CPU_METRICS["user"].key,
    CPU_METRICS["system"].key,
    CPU_METRICS["iowait"].key,
    MEMORY_METRICS["total"].key,
    MEMORY_METRICS["available"].key,
    TCMALLOC_METRICS["heap_size"].key,
    TCMALLOC_METRICS["current_allocated_bytes"].key,
    WIREDTIGER_CACHE_METRICS["bytes_current"].key,
    WIREDTIGER_CACHE_METRICS["tracked_dirty_bytes"].key,
    WIREDTIGER_CACHE_METRICS["bytes_maximum"].key,
    *(metric.key for metric in OPCOUNTER_METRICS.values()),
    *(metric.key for metric in OPCOUNTER_REPL_METRICS.values()),
    *(
        metric.key
        for operation in ("reads", "writes")
        for metric in (
            OP_LATENCY_METRICS[operation]["ops"],
            OP_LATENCY_METRICS[operation]["latency"],
        )
    ),
}
