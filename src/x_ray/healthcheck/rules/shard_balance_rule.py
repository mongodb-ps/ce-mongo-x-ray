from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue
from x_ray.utils import format_size


class ShardBalanceRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._imbalance_percentage = thresholds.get("sharding_imbalance_percentage", 0.2)

    def apply(self, data: object, **kwargs) -> tuple:
        """Check shard balance for any issues.

        Args:
            data (object): The `collStats` document.
            extra_info (dict, optional): Extra information such as host.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        shards = kwargs.get("extra_info", {}).get("shards", [])
        ns = data["ns"]
        test_results = []
        shard_stats = {
            s_name: {
                "size": s["size"],
                "count": s["count"],
                "avgObjSize": s.get("avgObjSize", 0),
                "storageSize": s["storageSize"],
                "nindexes": s["nindexes"],
                "totalIndexSize": s["totalIndexSize"],
                "totalSize": s["totalSize"],
            }
            for s_name, s in data["shards"].items()
        }
        # Check if collection is imbalanced.
        sizes = [shard_stats.get(s_name, {}).get("size", 0) for s_name in shards]
        max_size = max(sizes)
        min_size = min(sizes)
        if max_size > min_size * (1 + self._imbalance_percentage):
            issue = create_issue(
                ISSUE.IMBALANCED_SHARDING,
                host="cluster",
                params={
                    "ns": ns,
                    "size_diff": format_size(max_size - min_size),
                    "imbalance_percentage": self._imbalance_percentage * 100,
                },
            )
            test_results.append(issue)

        return test_results, shard_stats
