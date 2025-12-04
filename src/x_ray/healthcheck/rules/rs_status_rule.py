from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue
from x_ray.healthcheck.shared import MEMBER_STATE


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
            issue = create_issue(ISSUE.NO_PRIMARY, host=host)
            result.append(issue)

        # Check member states
        max_delay = self._thresholds.get("replication_lag_seconds", 60)
        set_name = data.get("set", "Unknown Set")
        for member in data["members"]:
            # Check problematic states
            state = member["state"]
            host = member["name"]

            if state in [3, 6, 8, 9, 10]:
                issue = create_issue(
                    ISSUE.UNHEALTHY_MEMBER,
                    host=host,
                    params={"set_name": set_name, "host": host, "state": MEMBER_STATE[state]},
                )
                result.append(issue)
            elif state in [0, 5]:
                issue = create_issue(
                    ISSUE.INITIALIZING_MEMBER,
                    host=host,
                    params={"set_name": set_name, "host": host, "state": MEMBER_STATE[state]},
                )
                result.append(issue)

            # Check replication lag
            if state == 2 and not no_primary:  # SECONDARY
                p_time = primary_member["optime"]["ts"]
                s_time = member["optime"]["ts"]
                lag = p_time.time - s_time.time
                if lag >= max_delay:
                    issue = create_issue(
                        ISSUE.DELAYED_MEMBER, host=host, params={"set_name": set_name, "host": host, "lag": lag}
                    )
                    result.append(issue)
        return result, data
