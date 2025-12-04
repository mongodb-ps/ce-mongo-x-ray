from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class CacheRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._read_into_threshold = thresholds.get("cache_read_into_mb", 100)
        self._updates_ratio_threshold = thresholds.get("updates_ratio", [0.08, 0.1])
        self._dirty_ratio_threshold = thresholds.get("dirty_ratio", [0.15, 0.2])
        self._cache_fill_ratio_threshold = thresholds.get("cache_fill_ratio", [0.9, 0.95])

    def apply(self, data: object, **kwargs) -> tuple:
        """Check the cache fill ratio for any issues.

        Args:
            data (object): The result from `serverStatus` command.
            extra_info (dict, optional): Extra information such as host.
            extra_info.base_server_status (dict, optional): The previous server status for comparison.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        test_results = []
        base_server_status = kwargs.get("extra_info", {}).get("server_status", {})
        base_wt = base_server_status.get("wiredTiger", {})
        new_wt = data.get("wiredTiger", {})
        base_cache_status = {
            "readInto": base_wt["cache"]["bytes read into cache"],
            "writtenFrom": base_wt["cache"]["bytes written from cache"],
            "forUpdates": base_wt["cache"].get("bytes allocated for updates", 0),
            "dirty": base_wt["cache"]["bytes dirty in the cache cumulative"],
            "uptimeMillis": base_server_status.get("uptimeMillis", 0),
        }
        new_cache_status = {
            "readInto": new_wt["cache"]["bytes read into cache"],
            "writtenFrom": new_wt["cache"]["bytes written from cache"],
            "forUpdates": new_wt["cache"].get("bytes allocated for updates", 0),
            "dirty": new_wt["cache"]["bytes dirty in the cache cumulative"],
            "uptimeMillis": data.get("uptimeMillis", 0),
        }
        interval = (new_cache_status["uptimeMillis"] - base_cache_status["uptimeMillis"]) / 1000
        parsed_data = {
            "cacheSize": new_wt["cache"]["maximum bytes configured"],
            "inCacheSize": new_wt["cache"]["bytes currently in the cache"],
            "readInto": (new_cache_status["readInto"] - base_cache_status["readInto"]) / interval,
            "writtenFrom": (new_cache_status["writtenFrom"] - base_cache_status["writtenFrom"]) / interval,
            "forUpdates": new_cache_status["forUpdates"] - base_cache_status["forUpdates"],
            "dirty": new_cache_status["dirty"] - base_cache_status["dirty"],
            "intervalMillis": interval * 1000,
        }
        if parsed_data["readInto"] >= self._read_into_threshold * 1024 * 1024:
            issue = create_issue(
                ISSUE.HIGH_SWAPPING,
                host=host,
                params={
                    "read_into": parsed_data["readInto"],
                    "read_into_threshold": self._read_into_threshold,
                },
            )
            test_results.append(issue)
        update_ratio = parsed_data["forUpdates"] / parsed_data["cacheSize"] if parsed_data["cacheSize"] > 0 else 0
        dirty_ratio = parsed_data["dirty"] / parsed_data["cacheSize"] if parsed_data["cacheSize"] > 0 else 0
        fill_ratio = parsed_data["inCacheSize"] / parsed_data["cacheSize"] if parsed_data["cacheSize"] > 0 else 0
        if update_ratio > self._updates_ratio_threshold[0]:
            issue = create_issue(
                (
                    ISSUE.HIGH_UPDATES_RATIO
                    if update_ratio <= self._updates_ratio_threshold[1]
                    else ISSUE.CRITICAL_UPDATES_RATIO
                ),
                host=host,
                params={
                    "update_ratio": update_ratio,
                    "updates_ratio_threshold": self._updates_ratio_threshold[1],
                },
            )
            test_results.append(issue)
        if dirty_ratio > self._dirty_ratio_threshold[0]:
            issue = create_issue(
                ISSUE.HIGH_DIRTY_RATIO if dirty_ratio <= self._dirty_ratio_threshold[1] else ISSUE.CRITICAL_DIRTY_RATIO,
                host=host,
                params={
                    "dirty_ratio": dirty_ratio,
                    "dirty_ratio_threshold": self._dirty_ratio_threshold[1],
                },
            )
            test_results.append(issue)
        if fill_ratio > self._cache_fill_ratio_threshold[0]:
            issue = create_issue(
                (
                    ISSUE.HIGH_CACHE_FILL_RATIO
                    if fill_ratio <= self._cache_fill_ratio_threshold[1]
                    else ISSUE.CRITICAL_CACHE_FILL_RATIO
                ),
                host=host,
                params={
                    "fill_ratio": fill_ratio,
                    "cache_fill_ratio_threshold": self._cache_fill_ratio_threshold[1],
                },
            )
            test_results.append(issue)
        return test_results, parsed_data
