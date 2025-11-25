from libs.healthcheck.rules.base_rule import BaseRule
from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from libs.healthcheck.shared import MEMBER_STATE, SEVERITY


class RSStatusRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check the replica set status for any issues.

        Args:
            data (object): The result from `replSetGetStatus` command.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        result = []
        # Find primary in members
        primary_member = next(iter(m for m in data["members"] if m["state"] == 1), None)

        no_primary = False
        if not primary_member:
            no_primary = True
            issue_id = ISSUE.NO_PRIMARY
            result.append(
                {
                    "id": issue_id,
                    "host": "cluster",
                    "severity": SEVERITY.HIGH,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(rs=data["set"]),
                }
            )

        # Check member states
        max_delay = self._thresholds.get("replication_lag_seconds", 60)
        set_name = data.get("set", "Unknown Set")
        for member in data["members"]:
            # Check problematic states
            state = member["state"]
            host = member["name"]

            if state in [3, 6, 8, 9, 10]:
                issue_id = ISSUE.UNHEALTHY_MEMBER
                result.append(
                    {
                        "id": issue_id,
                        "host": host,
                        "severity": SEVERITY.HIGH,
                        "title": ISSUE_MSG_MAP[issue_id]["title"],
                        "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                            rs=set_name, host=host, state=MEMBER_STATE[state]
                        ),
                    }
                )
            elif state in [0, 5]:
                issue_id = ISSUE.INITIALIZING_MEMBER
                result.append(
                    {
                        "id": issue_id,
                        "host": host,
                        "severity": SEVERITY.LOW,
                        "title": ISSUE_MSG_MAP[issue_id]["title"],
                        "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                            rs=set_name, host=host, state=MEMBER_STATE[state]
                        ),
                    }
                )

            # Check replication lag
            if state == 2 and not no_primary:  # SECONDARY
                p_time = primary_member["optime"]["ts"]
                s_time = member["optime"]["ts"]
                lag = p_time.time - s_time.time
                if lag >= max_delay:
                    issue_id = ISSUE.DELAYED_MEMBER
                    result.append(
                        {
                            "id": issue_id,
                            "host": host,
                            "severity": SEVERITY.HIGH,
                            "title": ISSUE_MSG_MAP[issue_id]["title"],
                            "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                                rs=set_name, host=host, lag=lag
                            ),
                        }
                    )
        return result, data
