from libs.healthcheck.rules.base_rule import BaseRule
from libs.healthcheck.shared import MAX_MONGOS_PING_LATENCY, SEVERITY
from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP


class OplogWindowRule(BaseRule):
    def apply(self, data: dict, result_template=None) -> tuple:
        """Check the oplog window for any issues.

        Args:
            data (object): The oplog status data.
            result_template (object, optional): The template for the result. Defaults to None.
        Returns:
            list: A list of oplog window check results.
        """
        template = result_template or {}
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
            issue_id = ISSUE.OPLOG_WINDOW_TOO_SMALL
            test_result.append(
                template
                | {
                    "id": issue_id,
                    "severity": SEVERITY.HIGH,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                        retention_hours=retention_hours,
                        oplog_window_threshold=oplog_window_threshold,
                    ),
                }
            )

        return test_result, {
            "configured_retention_hours": configured_retention_hours,
            "current_retention_hours": current_retention_hours,
            "effective_retention_hours": retention_hours,
        }
