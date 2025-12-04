from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class OplogWindowRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check the oplog window for any issues.

        Args:
            data (object): The oplog status data.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        test_result = []
        server_status = data.get("serverStatus", {})
        first_oplog = data.get("firstOplogEntry", {})
        last_oplog = data.get("lastOplogEntry", {})
        delta = last_oplog - first_oplog
        current_retention_hours = delta / 3600  # Convert seconds to hours
        configured_retention_hours = server_status.get("oplogTruncation", {}).get("oplogMinRetentionHours", 0)
        oplog_window_threshold = self._thresholds.get("oplog_window_hours", 48)

        # Check oplog information
        retention_hours = max(configured_retention_hours, current_retention_hours)
        if retention_hours < oplog_window_threshold:
            issue = create_issue(
                ISSUE.OPLOG_WINDOW_TOO_SMALL,
                host=host,
                params={
                    "retention_hours": retention_hours,
                    "oplog_window_threshold": oplog_window_threshold,
                },
            )
            test_result.append(issue)

        return test_result, {
            "configured_retention_hours": configured_retention_hours,
            "current_retention_hours": current_retention_hours,
            "effective_retention_hours": retention_hours,
        }
