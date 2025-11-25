from libs.healthcheck.rules.base_rule import BaseRule
from libs.healthcheck.shared import SEVERITY
from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP


class RSConfigRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check the replica set configuration for any issues.

        Args:
            data (object): The replica set configuration data.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            list: A list of replica set configuration check results.
        """
        result = []
        set_name = data["config"]["_id"]
        # Check number of voting members
        voting_members = sum(1 for member in data["config"]["members"] if member.get("votes", 0) > 0)
        if voting_members < 3:
            issue_id = ISSUE.INSUFFICIENT_VOTING_MEMBERS
            result.append(
                {
                    "id": issue_id,
                    "host": "cluster",
                    "severity": SEVERITY.HIGH,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                        set_name=set_name, voting_members=voting_members
                    ),
                }
            )
        if voting_members % 2 == 0:
            issue_id = ISSUE.EVEN_VOTING_MEMBERS
            result.append(
                {
                    "id": issue_id,
                    "host": "cluster",
                    "severity": SEVERITY.HIGH,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(set_name=set_name),
                }
            )

        for member in data["config"]["members"]:
            delay = member.get("secondaryDelaySecs", member.get("slaveDelay", 0))
            if delay > 0:
                if member.get("votes", 0) > 0:
                    issue_id = ISSUE.DELAYED_VOTING_MEMBER
                    result.append(
                        {
                            "id": issue_id,
                            "host": member["host"],
                            "severity": SEVERITY.HIGH,
                            "title": ISSUE_MSG_MAP[issue_id]["title"],
                            "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                                set_name=set_name, host=member["host"]
                            ),
                        }
                    )
                if member.get("priority", 0) > 0:
                    issue_id = ISSUE.DELAYED_ELECTABLE_MEMBER
                    result.append(
                        {
                            "id": issue_id,
                            "host": member["host"],
                            "severity": SEVERITY.HIGH,
                            "title": ISSUE_MSG_MAP[issue_id]["title"],
                            "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                                set_name=set_name, host=member["host"]
                            ),
                        }
                    )
                if not member.get("hidden", False):
                    issue_id = ISSUE.DELAYED_NON_HIDDEN_MEMBER
                    result.append(
                        {
                            "id": issue_id,
                            "host": member["host"],
                            "severity": SEVERITY.HIGH,
                            "title": ISSUE_MSG_MAP[issue_id]["title"],
                            "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                                set_name=set_name, host=member["host"]
                            ),
                        }
                    )

                issue_id = ISSUE.DELAYED_SECONDARY_MEMBER
                result.append(
                    {
                        "id": issue_id,
                        "host": member["host"],
                        "severity": SEVERITY.LOW,
                        "title": ISSUE_MSG_MAP[issue_id]["title"],
                        "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                            set_name=set_name, host=member["host"]
                        ),
                    }
                )
            if member.get("arbiterOnly", False):
                issue_id = ISSUE.ARBITER_MEMBER
                result.append(
                    {
                        "id": issue_id,
                        "host": member["host"],
                        "severity": SEVERITY.HIGH,
                        "title": ISSUE_MSG_MAP[issue_id]["title"],
                        "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                            set_name=set_name, host=member["host"]
                        ),
                    }
                )
        return result, data
