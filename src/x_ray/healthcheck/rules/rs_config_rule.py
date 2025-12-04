from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class RSConfigRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check the replica set configuration for any issues.

        Args:
            data (object): The replica set configuration data.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        result = []
        set_name = data["config"]["_id"]
        # Check number of voting members
        voting_members = sum(1 for member in data["config"]["members"] if member.get("votes", 0) > 0)
        if voting_members < 3:
            issue = create_issue(
                ISSUE.INSUFFICIENT_VOTING_MEMBERS,
                host="cluster",
                params={"set_name": set_name, "voting_members": voting_members},
            )
            result.append(issue)
        if voting_members % 2 == 0:
            issue = create_issue(
                ISSUE.EVEN_VOTING_MEMBERS,
                host="cluster",
                params={"set_name": set_name},
            )
            result.append(issue)

        for member in data["config"]["members"]:
            delay = member.get("secondaryDelaySecs", member.get("slaveDelay", 0))
            if delay > 0:
                if member.get("votes", 0) > 0:
                    issue = create_issue(
                        ISSUE.DELAYED_VOTING_MEMBER,
                        host=member["host"],
                        params={"set_name": set_name, "host": member["host"]},
                    )
                    result.append(issue)
                if member.get("priority", 0) > 0:
                    issue = create_issue(
                        ISSUE.DELAYED_ELECTABLE_MEMBER,
                        host=member["host"],
                        params={"set_name": set_name, "host": member["host"]},
                    )
                    result.append(issue)
                if not member.get("hidden", False):
                    issue = create_issue(
                        ISSUE.DELAYED_NON_HIDDEN_MEMBER,
                        host=member["host"],
                        params={"set_name": set_name, "host": member["host"]},
                    )
                    result.append(issue)

                issue = create_issue(
                    ISSUE.DELAYED_SECONDARY_MEMBER,
                    host=member["host"],
                    params={"set_name": set_name, "host": member["host"]},
                )
                result.append(issue)
            if member.get("arbiterOnly", False):
                issue = create_issue(
                    ISSUE.ARBITER_MEMBER,
                    host=member["host"],
                    params={"set_name": set_name, "host": member["host"]},
                )
                result.append(issue)
        return result, data
