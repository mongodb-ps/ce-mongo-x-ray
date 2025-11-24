import enum


class ISSUE(enum.Enum):
    EOL_VERSION_USED = 100
    RAPID_RELEASE_VERSION_USED = 101
    DEVELOPMENT_RELEASE_VERSION_USED = 102
    NO_PRIMARY = 200
    UNHEALTHY_MEMBER = 201
    INITIALIZING_MEMBER = 202
    DELAYED_MEMBER = 203
    INSUFFICIENT_VOTING_MEMBERS = 300
    EVEN_VOTING_MEMBERS = 301
    DELAYED_VOTING_MEMBER = 302
    DELAYED_ELECTABLE_MEMBER = 303
    DELAYED_NON_HIDDEN_MEMBER = 304
    DELAYED_SECONDARY_MEMBER = 305
    ARBITER_MEMBER = 306
    IRRESPONSIVE_MONGOS = 400
    NO_ACTIVE_MONGOS = 401
    SINGLE_MONGOS = 402
    OPLOG_WINDOW_TOO_SMALL = 403
    COLLECTION_TOO_LARGE = 500
    AVG_OBJECT_SIZE_TOO_LARGE = 501


ISSUE_MSG_MAP = {
    ISSUE.EOL_VERSION_USED: {
        "title": "Server Version EOL",
        "description": "Server version {version} is below EOL version {eol_version}. Consider upgrading to the latest version.",
    },
    ISSUE.RAPID_RELEASE_VERSION_USED: {
        "title": "Rapid Release Version Detected",
        "description": "Server version {version} is a unsupported rapid release version. Consider using release versions for better stability and support.",
    },
    ISSUE.DEVELOPMENT_RELEASE_VERSION_USED: {
        "title": "Development Release Version Detected",
        "description": "Server version {version} appears to be a development release. Consider using stable release versions for production environments.",
    },
    ISSUE.NO_PRIMARY: {
        "title": "No Primary",
        "description": "`{rs}` does not have a primary.",
    },
    ISSUE.UNHEALTHY_MEMBER: {
        "title": "Unhealthy Member",
        "description": "`{rs}` member `{host}` is in `{state}` state.",
    },
    ISSUE.INITIALIZING_MEMBER: {
        "title": "Initializing Member",
        "description": "`{rs}` member `{host}` is being initialized in `{state}` state.",
    },
    ISSUE.DELAYED_MEMBER: {
        "title": "High Replication Lag",
        "description": "`{rs}` member `{host}` has high replication lag of {lag} seconds.",
    },
    ISSUE.INSUFFICIENT_VOTING_MEMBERS: {
        "title": "Insufficient Voting Members",
        "description": "`{set_name}` has only {voting_members} voting members. Consider adding more to ensure fault tolerance.",
    },
    ISSUE.EVEN_VOTING_MEMBERS: {
        "title": "Even Voting Members",
        "description": "`{set_name}` has an even number of voting members, which can lead to split-brain scenarios. Consider adding an additional member.",
    },
    ISSUE.DELAYED_VOTING_MEMBER: {
        "title": "Delayed Voting Member",
        "description": "`{set_name}` member `{host}` is a delayed secondary but is also a voting member. This can lead to performance issues.",
    },
    ISSUE.DELAYED_ELECTABLE_MEMBER: {
        "title": "Delayed Electable Member",
        "description": "`{set_name}` member `{host}` is a delayed secondary but has non-zero priority. This can lead to potential issues.",
    },
    ISSUE.DELAYED_NON_HIDDEN_MEMBER: {
        "title": "Non-Hidden Delayed Member",
        "description": "`{set_name}` member `{host}` is a delayed secondary and should be configured as hidden.",
    },
    ISSUE.DELAYED_SECONDARY_MEMBER: {
        "title": "Delayed Secondary Member",
        "description": "`{set_name}` member `{host}` is a delayed secondary. Delayed secondaries are not recommended in general.",
    },
    ISSUE.ARBITER_MEMBER: {
        "title": "Arbiter Member",
        "description": "`{set_name}` member `{host}` is an arbiter. Arbiters are not recommended.",
    },
    ISSUE.IRRESPONSIVE_MONGOS: {
        "title": "Irresponsive Mongos",
        "description": "Mongos `{host}` is not responsive. Last ping was at `{ping_latency}` seconds ago. This is expected if the mongos has been removed from the cluster.",
    },
    ISSUE.NO_ACTIVE_MONGOS: {
        "title": "No Active Mongos",
        "description": "No active mongos found in the cluster.",
    },
    ISSUE.SINGLE_MONGOS: {
        "title": "Single Mongos",
        "description": "Only one mongos `{host}` is available in the cluster. No failover is possible.",
    },
    ISSUE.OPLOG_WINDOW_TOO_SMALL: {
        "title": "Oplog Window Too Small",
        "description": "`Replica set oplog window is `{retention_hours}` hours, below the recommended minimum `{oplog_window_threshold}` hours.",
    },
    ISSUE.COLLECTION_TOO_LARGE: {
        "title": "Collection Too Large",
        "description": "Collection `{ns}` has size `{size_gb} GB`, which exceeds the recommended maximum of `{collection_size_gb} GB`. Consider sharding the collection.",
    },
    ISSUE.AVG_OBJECT_SIZE_TOO_LARGE: {
        "title": "Average Object Size Too Large",
        "description": "Collection `{ns}` has an average object size of `{avg_obj_size_kb} KB`, which exceeds the recommended maximum of `{obj_size_kb} KB`. Consider optimizing your data schema.",
    },
}
