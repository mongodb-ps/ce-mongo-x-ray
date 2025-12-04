import enum

from x_ray.healthcheck.shared import SEVERITY


class ISSUE(enum.Enum):
    # Build Info Issues
    EOL_VERSION_USED = 100
    RAPID_RELEASE_VERSION_USED = 101
    DEVELOPMENT_RELEASE_VERSION_USED = 102
    # Replica Set Issues
    NO_PRIMARY = 200
    UNHEALTHY_MEMBER = 201
    INITIALIZING_MEMBER = 202
    DELAYED_MEMBER = 203
    # Replica Set Configuration Issues
    INSUFFICIENT_VOTING_MEMBERS = 300
    EVEN_VOTING_MEMBERS = 301
    DELAYED_VOTING_MEMBER = 302
    DELAYED_ELECTABLE_MEMBER = 303
    DELAYED_NON_HIDDEN_MEMBER = 304
    DELAYED_SECONDARY_MEMBER = 305
    ARBITER_MEMBER = 306
    # Sharded Cluster Issues
    IRRESPONSIVE_MONGOS = 400
    NO_ACTIVE_MONGOS = 401
    SINGLE_MONGOS = 402
    # Oplog Issues
    OPLOG_WINDOW_TOO_SMALL = 500
    # Data Size Issues
    COLLECTION_TOO_LARGE = 600
    AVG_OBJECT_SIZE_TOO_LARGE = 601
    # Fragmentation Issues
    HIGH_COLLECTION_FRAGMENTATION = 700
    HIGH_INDEX_FRAGMENTATION = 701
    # Latency Issues
    HIGH_READ_LATENCY = 800
    HIGH_WRITE_LATENCY = 801
    HIGH_COMMAND_LATENCY = 802
    HIGH_TRANSACTION_LATENCY = 803
    # Index Issues
    UNUSED_INDEX = 900
    TOO_MANY_INDEXES = 901
    REDUNDANT_INDEX = 902
    # Security Issues
    AUTHORIZATION_DISABLED = 1000
    LOG_REDACTION_DISABLED = 1001
    TLS_DISABLED = 1002
    OPTIONAL_TLS = 1003
    OPEN_BIND_IP = 1004
    DEFAULT_PORT_USED = 1005
    AUDITING_DISABLED = 1006
    ENCRYPTION_AT_REST_DISABLED = 1007
    ENCRYPTION_AT_REST_USING_KEYFILE = 1008
    # Query Targeting Issues
    POOR_QUERY_TARGETING_KEYS = 1100
    POOR_QUERY_TARGETING_OBJECTS = 1101
    # Connections Issues
    HIGH_CONNECTION_USAGE_RATIO = 1200
    # Cache Issues
    HIGH_SWAPPING = 1300
    HIGH_UPDATES_RATIO = 1301
    CRITICAL_UPDATES_RATIO = 1302
    HIGH_DIRTY_RATIO = 1303
    CRITICAL_DIRTY_RATIO = 1304
    HIGH_CACHE_FILL_RATIO = 1305
    CRITICAL_CACHE_FILL_RATIO = 1306
    # Shard Key Issues
    IMPROPER_SHARD_KEY = 1400
    IMBALANCED_SHARDING = 1401
    # Host Issues
    HOSTS_DIFFERENT_HARDWARE = 1500
    NUMA_ENABLED = 1501
    NUMA_DISABLED = 1502


ISSUE_MSG_MAP = {
    ISSUE.EOL_VERSION_USED: {
        "id": ISSUE.EOL_VERSION_USED,
        "severity": SEVERITY.HIGH,
        "title": "Server Version EOL",
        "description": "Server version {version} is below EOL version {eol_version}. Consider upgrading to the latest version.",
    },
    ISSUE.RAPID_RELEASE_VERSION_USED: {
        "id": ISSUE.RAPID_RELEASE_VERSION_USED,
        "severity": SEVERITY.MEDIUM,
        "title": "Rapid Release Version Detected",
        "description": "Server version {version} is a unsupported rapid release version. Consider using release versions for better stability and support.",
    },
    ISSUE.DEVELOPMENT_RELEASE_VERSION_USED: {
        "id": ISSUE.DEVELOPMENT_RELEASE_VERSION_USED,
        "severity": SEVERITY.MEDIUM,
        "title": "Development Release Version Detected",
        "description": "Server version {version} appears to be a development release. Consider using stable release versions for production environments.",
    },
    ISSUE.NO_PRIMARY: {
        "id": ISSUE.NO_PRIMARY,
        "severity": SEVERITY.HIGH,
        "title": "No Primary",
        "description": "`{set_name}` does not have a primary.",
    },
    ISSUE.UNHEALTHY_MEMBER: {
        "id": ISSUE.UNHEALTHY_MEMBER,
        "severity": SEVERITY.HIGH,
        "title": "Unhealthy Member",
        "description": "`{set_name}` member `{host}` is in `{state}` state.",
    },
    ISSUE.INITIALIZING_MEMBER: {
        "id": ISSUE.INITIALIZING_MEMBER,
        "severity": SEVERITY.LOW,
        "title": "Initializing Member",
        "description": "`{set_name}` member `{host}` is being initialized in `{state}` state.",
    },
    ISSUE.DELAYED_MEMBER: {
        "id": ISSUE.DELAYED_MEMBER,
        "severity": SEVERITY.HIGH,
        "title": "High Replication Lag",
        "description": "`{set_name}` member `{host}` has high replication lag of {lag} seconds.",
    },
    ISSUE.INSUFFICIENT_VOTING_MEMBERS: {
        "id": ISSUE.INSUFFICIENT_VOTING_MEMBERS,
        "severity": SEVERITY.HIGH,
        "title": "Insufficient Voting Members",
        "description": "`{set_name}` has only {voting_members} voting members. Consider adding more to ensure fault tolerance.",
    },
    ISSUE.EVEN_VOTING_MEMBERS: {
        "id": ISSUE.EVEN_VOTING_MEMBERS,
        "severity": SEVERITY.HIGH,
        "title": "Even Voting Members",
        "description": "`{set_name}` has an even number of voting members, which can lead to split-brain scenarios. Consider adding an additional member.",
    },
    ISSUE.DELAYED_VOTING_MEMBER: {
        "id": ISSUE.DELAYED_VOTING_MEMBER,
        "severity": SEVERITY.HIGH,
        "title": "Delayed Voting Member",
        "description": "`{set_name}` member `{host}` is a delayed secondary but is also a voting member. This can lead to performance issues.",
    },
    ISSUE.DELAYED_ELECTABLE_MEMBER: {
        "id": ISSUE.DELAYED_ELECTABLE_MEMBER,
        "severity": SEVERITY.HIGH,
        "title": "Delayed Electable Member",
        "description": "`{set_name}` member `{host}` is a delayed secondary but has non-zero priority. This can lead to potential issues.",
    },
    ISSUE.DELAYED_NON_HIDDEN_MEMBER: {
        "id": ISSUE.DELAYED_NON_HIDDEN_MEMBER,
        "severity": SEVERITY.HIGH,
        "title": "Non-Hidden Delayed Member",
        "description": "`{set_name}` member `{host}` is a delayed secondary and should be configured as hidden.",
    },
    ISSUE.DELAYED_SECONDARY_MEMBER: {
        "id": ISSUE.DELAYED_SECONDARY_MEMBER,
        "severity": SEVERITY.LOW,
        "title": "Delayed Secondary Member",
        "description": "`{set_name}` member `{host}` is a delayed secondary. Delayed secondaries are not recommended in general.",
    },
    ISSUE.ARBITER_MEMBER: {
        "id": ISSUE.ARBITER_MEMBER,
        "severity": SEVERITY.HIGH,
        "title": "Arbiter Member",
        "description": "`{set_name}` member `{host}` is an arbiter. Arbiters are not recommended.",
    },
    ISSUE.IRRESPONSIVE_MONGOS: {
        "id": ISSUE.IRRESPONSIVE_MONGOS,
        "severity": SEVERITY.LOW,
        "title": "Irresponsive Mongos",
        "description": "Mongos `{host}` is not responsive. Last ping was at `{ping_latency}` seconds ago. This is expected if the mongos has been removed from the cluster.",
    },
    ISSUE.NO_ACTIVE_MONGOS: {
        "id": ISSUE.NO_ACTIVE_MONGOS,
        "severity": SEVERITY.HIGH,
        "title": "No Active Mongos",
        "description": "No active mongos found in the cluster.",
    },
    ISSUE.SINGLE_MONGOS: {
        "id": ISSUE.SINGLE_MONGOS,
        "severity": SEVERITY.HIGH,
        "title": "Single Mongos",
        "description": "Only one mongos `{mongos}` is available in the cluster. No failover is possible.",
    },
    ISSUE.OPLOG_WINDOW_TOO_SMALL: {
        "id": ISSUE.OPLOG_WINDOW_TOO_SMALL,
        "severity": SEVERITY.HIGH,
        "title": "Oplog Window Too Small",
        "description": "`Replica set oplog window is `{retention_hours}` hours, below the recommended minimum `{oplog_window_threshold}` hours.",
    },
    ISSUE.COLLECTION_TOO_LARGE: {
        "id": ISSUE.COLLECTION_TOO_LARGE,
        "severity": SEVERITY.LOW,
        "title": "Collection Too Large",
        "description": "Collection `{ns}` has size `{size_gb} GB`, which exceeds the recommended maximum of `{collection_size_gb} GB`. Consider sharding the collection.",
    },
    ISSUE.AVG_OBJECT_SIZE_TOO_LARGE: {
        "id": ISSUE.AVG_OBJECT_SIZE_TOO_LARGE,
        "severity": SEVERITY.LOW,
        "title": "Average Object Size Too Large",
        "description": "Collection `{ns}` has an average object size of `{avg_obj_size_kb} KB`, which exceeds the recommended maximum of `{obj_size_kb} KB`. Consider optimizing your data schema.",
    },
    ISSUE.HIGH_COLLECTION_FRAGMENTATION: {
        "id": ISSUE.HIGH_COLLECTION_FRAGMENTATION,
        "severity": SEVERITY.MEDIUM,
        "title": "High Collection Fragmentation",
        "description": "Collection `{ns}` has a high fragmentation ratio of `{fragmentation:.2%}`.",
    },
    ISSUE.HIGH_INDEX_FRAGMENTATION: {
        "id": ISSUE.HIGH_INDEX_FRAGMENTATION,
        "severity": SEVERITY.MEDIUM,
        "title": "High Index Fragmentation",
        "description": "Collection `{ns}` index `{index_name}` has a high fragmentation ratio of `{fragmentation:.2%}`.",
    },
    ISSUE.HIGH_READ_LATENCY: {
        "id": ISSUE.HIGH_READ_LATENCY,
        "severity": SEVERITY.MEDIUM,
        "title": "High Read Latency",
        "description": "Collection `{ns}` has a higher average read latency `{avg_r_latency:.2f}ms` than threshold `{op_latency_ms:.2f}ms`.",
    },
    ISSUE.HIGH_WRITE_LATENCY: {
        "id": ISSUE.HIGH_WRITE_LATENCY,
        "severity": SEVERITY.MEDIUM,
        "title": "High Write Latency",
        "description": "Collection `{ns}` has a higher average write latency `{avg_w_latency:.2f}ms` than threshold `{op_latency_ms:.2f}ms`.",
    },
    ISSUE.HIGH_COMMAND_LATENCY: {
        "id": ISSUE.HIGH_COMMAND_LATENCY,
        "severity": SEVERITY.MEDIUM,
        "title": "High Command Latency",
        "description": "Collection `{ns}` has a higher average command latency `{avg_c_latency:.2f}ms` than threshold `{op_latency_ms:.2f}ms`.",
    },
    ISSUE.HIGH_TRANSACTION_LATENCY: {
        "id": ISSUE.HIGH_TRANSACTION_LATENCY,
        "severity": SEVERITY.MEDIUM,
        "title": "High Transaction Latency",
        "description": "Collection `{ns}` has a higher average transaction latency `{avg_t_latency:.2f}ms` than threshold `{op_latency_ms:.2f}ms`.",
    },
    ISSUE.UNUSED_INDEX: {
        "id": ISSUE.UNUSED_INDEX,
        "severity": SEVERITY.LOW,
        "title": "Unused Index",
        "description": "Index `{index_name}` in collection `{ns}` has not been used for more than `{unused_index_days}` days.",
    },
    ISSUE.TOO_MANY_INDEXES: {
        "id": ISSUE.TOO_MANY_INDEXES,
        "severity": SEVERITY.MEDIUM,
        "title": "Too Many Indexes",
        "description": "Collection `{ns}` has more than `{max_num_indexes}` indexes (`{num_indexes}` indexes detected), which can cause potential write performance issues.",
    },
    ISSUE.REDUNDANT_INDEX: {
        "id": ISSUE.REDUNDANT_INDEX,
        "severity": SEVERITY.MEDIUM,
        "title": "Redundant Index",
        "description": "Index `{index1}` in collection `{ns}` is redundant with another index `{index2}`.",
    },
    ISSUE.AUTHORIZATION_DISABLED: {
        "id": ISSUE.AUTHORIZATION_DISABLED,
        "severity": SEVERITY.HIGH,
        "title": "Authorization Disabled",
        "description": "Authorization is disabled, which may lead to unauthorized access.",
    },
    ISSUE.LOG_REDACTION_DISABLED: {
        "id": ISSUE.LOG_REDACTION_DISABLED,
        "severity": SEVERITY.MEDIUM,
        "title": "Log Redaction Disabled",
        "description": "Redaction of log is disabled, which may lead to sensitive information exposure.",
    },
    ISSUE.TLS_DISABLED: {
        "id": ISSUE.TLS_DISABLED,
        "severity": SEVERITY.MEDIUM,
        "title": "TLS Disabled",
        "description": "TLS is disabled, which may lead to unencrypted connections.",
    },
    ISSUE.OPTIONAL_TLS: {
        "id": ISSUE.OPTIONAL_TLS,
        "severity": SEVERITY.MEDIUM,
        "title": "Optional TLS",
        "description": "TLS is enabled but not set to `requireTLS`, current mode is `{tls_mode}`.",
    },
    ISSUE.OPEN_BIND_IP: {
        "id": ISSUE.OPEN_BIND_IP,
        "severity": SEVERITY.LOW,
        "title": "Unrestricted Bind IP",
        "description": "Bind IP is set to `0.0.0.0`. Your service may be exposed to the internet. Make sure to restrict it to specific IP addresses.",
    },
    ISSUE.DEFAULT_PORT_USED: {
        "id": ISSUE.DEFAULT_PORT_USED,
        "severity": SEVERITY.LOW,
        "title": "Default Port Used",
        "description": "Default port `27017` is used. Make sure to restrict access to this port.",
    },
    ISSUE.AUDITING_DISABLED: {
        "id": ISSUE.AUDITING_DISABLED,
        "severity": SEVERITY.HIGH,
        "title": "Auditing Disabled",
        "description": "Auditing is disabled, which may lead to unmonitored access.",
    },
    ISSUE.ENCRYPTION_AT_REST_DISABLED: {
        "id": ISSUE.ENCRYPTION_AT_REST_DISABLED,
        "severity": SEVERITY.MEDIUM,
        "title": "Encryption at Rest Disabled",
        "description": "Encryption at rest is disabled, which may lead to data exposure if the storage media is compromised.",
    },
    ISSUE.ENCRYPTION_AT_REST_USING_KEYFILE: {
        "id": ISSUE.ENCRYPTION_AT_REST_USING_KEYFILE,
        "severity": SEVERITY.HIGH,
        "title": "Encryption at Rest Using Keyfile",
        "description": "Encryption at rest is enabled using a keyfile. This is not safe in general. Ensure that the keyfile is securely managed.",
    },
    ISSUE.POOR_QUERY_TARGETING_KEYS: {
        "id": ISSUE.POOR_QUERY_TARGETING_KEYS,
        "severity": SEVERITY.HIGH,
        "title": "Poor Query Targeting (Keys)",
        "description": "Scanned/Returned ratio `{scanned_returned:.2f}` exceeds the threshold `{query_targeting}`.",
    },
    ISSUE.POOR_QUERY_TARGETING_OBJECTS: {
        "id": ISSUE.POOR_QUERY_TARGETING_OBJECTS,
        "severity": SEVERITY.HIGH,
        "title": "Poor Query Targeting (Objects)",
        "description": "Scanned Objects/Returned ratio `{scanned_obj_returned:.2f}` exceeds the threshold `{query_targeting_obj}`.",
    },
    ISSUE.HIGH_CONNECTION_USAGE_RATIO: {
        "id": ISSUE.HIGH_CONNECTION_USAGE_RATIO,
        "severity": SEVERITY.HIGH,
        "title": "High Connection Usage Ratio",
        "description": "Current connections (`{current}`) exceed `{used_connection_ratio:.2f}%` of total available connections (`{total}`).",
    },
    ISSUE.HIGH_SWAPPING: {
        "id": ISSUE.HIGH_SWAPPING,
        "severity": SEVERITY.MEDIUM,
        "title": "High Swapping",
        "description": "Read into cache rate `{read_into} MB/s` exceeds the threshold `{read_into_threshold} MB/s`. This usually indicates insufficient cache size or suboptimal indexes.",
    },
    ISSUE.HIGH_UPDATES_RATIO: {
        "id": ISSUE.HIGH_UPDATES_RATIO,
        "severity": SEVERITY.MEDIUM,
        "title": "High Updates Ratio",
        "description": "Bytes allocated for updates ratio `{update_ratio:.2f}` is approaching the threshold `{updates_ratio_threshold}`. Once the ratio exceeds 10%, all operations will be throttled.",
    },
    ISSUE.CRITICAL_UPDATES_RATIO: {
        "id": ISSUE.CRITICAL_UPDATES_RATIO,
        "severity": SEVERITY.HIGH,
        "title": "Critical Updates Ratio",
        "description": "Bytes allocated for updates ratio `{update_ratio:.2f}` has exceeded the critical threshold `{updates_ratio_threshold}`. All operations are being throttled.",
    },
    ISSUE.HIGH_DIRTY_RATIO: {
        "id": ISSUE.HIGH_DIRTY_RATIO,
        "severity": SEVERITY.MEDIUM,
        "title": "High Dirty Fill Ratio",
        "description": "Dirty fill ratio `{dirty_ratio:.2f}` is approaching the threshold `{dirty_ratio_threshold}`. Once the ratio exceeds 20%, all operations will be throttled.",
    },
    ISSUE.CRITICAL_DIRTY_RATIO: {
        "id": ISSUE.CRITICAL_DIRTY_RATIO,
        "severity": SEVERITY.HIGH,
        "title": "Critical Dirty Fill Ratio",
        "description": "Dirty fill ratio `{dirty_ratio:.2f}` has exceeded the critical threshold `{dirty_ratio_threshold}`. All operations are being throttled.",
    },
    ISSUE.HIGH_CACHE_FILL_RATIO: {
        "id": ISSUE.HIGH_CACHE_FILL_RATIO,
        "severity": SEVERITY.MEDIUM,
        "title": "High Cache Fill Ratio",
        "description": "Cache fill ratio `{fill_ratio:.2f}` is approaching the threshold `{cache_fill_ratio_threshold}`. Once the ratio exceeds 95%, all operations will be throttled.",
    },
    ISSUE.CRITICAL_CACHE_FILL_RATIO: {
        "id": ISSUE.CRITICAL_CACHE_FILL_RATIO,
        "severity": SEVERITY.HIGH,
        "title": "Critical Cache Fill Ratio",
        "description": "Cache fill ratio `{fill_ratio:.2f}` has exceeded the critical threshold `{cache_fill_ratio_threshold}`. All operations are being throttled.",
    },
    ISSUE.IMPROPER_SHARD_KEY: {
        "id": ISSUE.IMPROPER_SHARD_KEY,
        "severity": SEVERITY.INFO,
        "title": "Potential Bad Shard Key",
        "description": "Collection `{ns}` has the shard key set to `{shard_key}`. Make sure the value of `_id` is not monotonically increasing or decreasing.",
    },
    ISSUE.IMBALANCED_SHARDING: {
        "id": ISSUE.IMBALANCED_SHARDING,
        "severity": SEVERITY.MEDIUM,
        "title": "Imbalanced Sharding",
        "description": "Collection `{ns}` is imbalanced across shards. The size difference between the largest and smallest shard is {size_diff} and is more than {imbalance_percentage:.2f}%.",
    },
    ISSUE.HOSTS_DIFFERENT_HARDWARE: {
        "id": ISSUE.HOSTS_DIFFERENT_HARDWARE,
        "severity": SEVERITY.LOW,
        "title": "Hosts with Different Hardware",
        "description": "The hosts in the `{set_name}` are using different hardware. The ones with less resources may become performance bottlenecks.",
    },
    ISSUE.NUMA_ENABLED: {
        "id": ISSUE.NUMA_ENABLED,
        "severity": SEVERITY.HIGH,
        "title": "NUMA Enabled",
        "description": "NUMA is enabled on host `{host}` (MongoDB `{version}`). It is recommended to disable NUMA for database servers running MongoDB <= 7.0 to avoid potential performance issues.",
    },
    ISSUE.NUMA_DISABLED: {
        "id": ISSUE.NUMA_DISABLED,
        "severity": SEVERITY.LOW,
        "title": "NUMA Disabled",
        "description": "NUMA is disabled on host `{host}` (MongoDB `{version}`). It is recommended to enable NUMA for database servers running MongoDB >= 8.0 to improve performance.",
    },
}


def create_issue(issue_id: ISSUE, host: str, params: dict = None) -> dict:
    if issue_id not in ISSUE_MSG_MAP:
        raise ValueError(f"Unknown issue ID: {issue_id}")
    issue_template = ISSUE_MSG_MAP[issue_id]
    issue = issue_template | {
        "host": host,
        "description": issue_template["description"] if not params else issue_template["description"].format(**params),
    }
    return issue
