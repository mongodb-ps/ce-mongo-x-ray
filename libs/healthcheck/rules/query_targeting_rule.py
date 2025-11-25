from libs.healthcheck.rules.base_rule import BaseRule
from libs.healthcheck.issues import ISSUE, create_issue
from libs.healthcheck.shared import MEMBER_STATE


class QueryTargetingRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._max_query_targeting = thresholds.get("query_targeting", 0.1)
        self._max_query_targeting_obj = thresholds.get("query_targeting_obj", 0.1)

    def apply(self, data: object, **kwargs) -> tuple:
        """Check query targeting efficiency.

        Args:
            data (object): The result from `serverStatus` command.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        test_result = []
        query_executor = data["metrics"].get("queryExecutor", {})
        document = data["metrics"].get("document", {})
        scanned_returned = (
            (query_executor["scanned"] / document["returned"])
            if document["returned"] > 0
            else query_executor["scanned"]
        )
        scanned_obj_returned = (
            (query_executor["scannedObjects"] / document["returned"])
            if document["returned"] > 0
            else query_executor["scannedObjects"]
        )
        if scanned_returned > self._max_query_targeting:
            issue = create_issue(
                ISSUE.POOR_QUERY_TARGETING_KEYS,
                host=host,
                params={
                    "scanned_returned": f"{scanned_returned:.2f}",
                    "query_targeting": f"{self._max_query_targeting:.2f}",
                },
            )
            test_result.append(issue)
        if scanned_obj_returned > self._max_query_targeting_obj:
            issue = create_issue(
                ISSUE.POOR_QUERY_TARGETING_OBJECTS,
                host=host,
                params={
                    "scanned_obj_returned": f"{scanned_obj_returned:.2f}",
                    "query_targeting_obj": f"{self._max_query_targeting_obj:.2f}",
                },
            )
            test_result.append(issue)

        return test_result, {"scanned/returned": scanned_returned, "scanned_obj/returned": scanned_obj_returned}
