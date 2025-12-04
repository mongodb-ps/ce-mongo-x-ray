from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class DataSizeRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._collection_size_gb = self._thresholds.get("collection_size_gb", 2048) * 1024**3
        self._obj_size_bytes = self._thresholds.get("obj_size_kb", 32) * 1024
        self._index_size_ratio = self._thresholds.get("index_size_ratio", 0.2)

    def apply(self, data: object, **kwargs) -> tuple:
        """Check the data size for any issues.

        Args:
            data (object): The data size status data.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        test_result = []
        storage_stats = data.get("storageStats", {})
        del storage_stats["indexDetails"]
        del storage_stats["wiredTiger"]
        # Check for large collection size
        if storage_stats.get("size", 0) > self._collection_size_gb:
            issue = create_issue(
                ISSUE.COLLECTION_TOO_LARGE,
                host=host,
                params={
                    "ns": data.get("ns", ""),
                    "size_gb": storage_stats.get("size", 0) / 1024**3,
                    "collection_size_gb": self._collection_size_gb / 1024**3,
                },
            )
            test_result.append(issue)
        # Check for average object size
        if storage_stats.get("avgObjSize", 0) > self._obj_size_bytes:
            issue = create_issue(
                ISSUE.AVG_OBJECT_SIZE_TOO_LARGE,
                host=host,
                params={
                    "ns": data.get("ns", ""),
                    "avg_obj_size_kb": storage_stats.get("avgObjSize", 0) / 1024,
                    "obj_size_kb": self._obj_size_bytes / 1024,
                },
            )
            test_result.append(issue)

        return test_result, data
