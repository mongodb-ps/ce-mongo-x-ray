from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class FragmentationRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._fragmentation_ratio = self._thresholds.get("fragmentation_ratio", 0.5)

    def apply(self, data: object, **kwargs) -> tuple:
        """Check the fragmentation ratio for any issues.

        Args:
            data (object): The collStats data.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        ns = data["ns"]
        test_result = []
        # Check for fragmentation
        storage_stats = data.get("storageStats", {})
        storage_size = storage_stats["storageSize"]
        coll_reusable = storage_stats["wiredTiger"]["block-manager"]["file bytes available for reuse"]
        coll_frag_ratio = round(coll_reusable / storage_size if storage_size else 0, 4)
        if coll_frag_ratio > self._fragmentation_ratio:
            issue = create_issue(
                ISSUE.HIGH_COLLECTION_FRAGMENTATION, host=host, params={"ns": ns, "fragmentation": coll_frag_ratio}
            )
            test_result.append(issue)
        index_frags = []
        for index_name, s in storage_stats["indexDetails"].items():
            reusable = s["block-manager"]["file bytes available for reuse"]
            total_size = s["block-manager"]["file size in bytes"]
            index_frag_ratio = round(reusable / total_size if total_size > 0 else 0, 4)
            index_frags.append(
                {
                    "indexName": index_name,
                    "reusable": reusable,
                    "totalSize": total_size,
                    "fragmentation": index_frag_ratio,
                }
            )
            if index_frag_ratio > self._fragmentation_ratio:
                issue = create_issue(
                    ISSUE.HIGH_INDEX_FRAGMENTATION,
                    host=host,
                    params={"ns": ns, "index_name": index_name, "fragmentation": index_frag_ratio},
                )
                test_result.append(issue)
        return test_result, {
            "collFragmentation": {
                "reusable": coll_reusable,
                "totalSize": storage_size,
                "fragmentation": coll_frag_ratio,
            },
            "indexFragmentations": index_frags,
        }
