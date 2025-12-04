from datetime import datetime
from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class IndexRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._max_num_indexes = thresholds.get("num_indexes", 10)
        self._unused_index_days = thresholds.get("unused_index_days", 7)

    def apply(self, data: object, **kwargs) -> tuple:
        """Check the index fragmentation for any issues.

        Args:
            data (object): The indexStats data.
            extra_info (dict): Additional information such as host.
            check_items (list): List of checks to perform: "num_indexes", "unused_indexes", "redundant_indexes".
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        ns = kwargs.get("extra_info", {}).get("ns", "unknown")
        check_items = kwargs.get("check_items", ["num_indexes", "unused_indexes", "redundant_indexes"])
        test_result = []
        unique_indexes = set()
        for index in data:
            unique_indexes.add(index.get("name"))
            # Check for unused indexes
            if "unused_indexes" in check_items:
                if index.get("accesses", {}).get("ops", 0) == 0:
                    last_used = index.get("accesses", {}).get("since", None)
                    if last_used:
                        if (datetime.now() - last_used).days > self._unused_index_days:
                            issue = create_issue(
                                ISSUE.UNUSED_INDEX,
                                host=host,
                                params={
                                    "index_name": index.get("name"),
                                    "ns": ns,
                                    "unused_index_days": self._unused_index_days,
                                },
                            )
                            test_result.append(issue)
        # Check number of indexes
        num_indexes = len(unique_indexes)
        if "num_indexes" in check_items and num_indexes > self._max_num_indexes:
            issue = create_issue(
                ISSUE.TOO_MANY_INDEXES,
                host=host,
                params={
                    "ns": ns,
                    "max_num_indexes": self._max_num_indexes,
                    "num_indexes": num_indexes,
                },
            )
            test_result.append(issue)
        # Check for redundant indexes
        if "redundant_indexes" in check_items:
            indexes = [index["spec"] for i, index in enumerate(data)]
            reverse_indexes = []
            for index in indexes:
                reverse_index = {k: v for k, v in index.items() if k != "key"}
                reverse_index["key"] = {
                    k: (v * -1 if isinstance(v, (int, float)) else v) for k, v in index["key"].items()
                }
                reverse_indexes.append(reverse_index)
            index_targets = indexes + reverse_indexes
            for index in indexes:
                for target in index_targets:
                    if is_redundant(index, target):
                        issue = create_issue(
                            ISSUE.REDUNDANT_INDEX,
                            host=host,
                            params={
                                "index1": index.get("name"),
                                "ns": ns,
                                "index2": target.get("name"),
                            },
                        )
                        test_result.append(issue)
                        break
        return test_result, data


def is_redundant(index1, index2):
    # These options must be identical for indexes to be considered redundant
    OPTIONS = [
        "unique",
        "sparse",
        "partialFilterExpression",
        "collation",
        "hidden",
    ]
    for o in OPTIONS:
        if index1.get(o) != index2.get(o):
            return False
    # Check if the keys are identical or if one is a prefix of the other
    key1 = "_".join([f"{k}_{v}" for k, v in index1["key"].items()])
    key2 = "_".join([f"{k}_{v}" for k, v in index2["key"].items()])

    # If key1 == key2, it's being compared to itself, so skip
    return key1 != key2 and key2.startswith(key1)
