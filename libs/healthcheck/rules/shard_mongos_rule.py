from libs.healthcheck.rules.base_rule import BaseRule
from libs.healthcheck.shared import MAX_MONGOS_PING_LATENCY, SEVERITY
from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP


class ShardMongosRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check the sharded cluster mongos nodes for any issues.

        Args:
            data (object): The sharded cluster status data.
            extra_info (dict, optional): Extra information such as host. Defaults to None.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        test_result = []
        active_mongos = []
        for mongos in data:
            if mongos.get("pingLatencySec", 0) > MAX_MONGOS_PING_LATENCY:
                issue_id = ISSUE.IRRESPONSIVE_MONGOS
                test_result.append(
                    {
                        "id": issue_id,
                        "host": mongos["host"],
                        "severity": SEVERITY.LOW,
                        "title": ISSUE_MSG_MAP[issue_id]["title"],
                        "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                            host=mongos["host"],
                            ping_latency=round(mongos["pingLatencySec"]),
                        ),
                    }
                )
            else:
                active_mongos.append(mongos["host"])

        if len(active_mongos) == 0:
            issue_id = ISSUE.NO_ACTIVE_MONGOS
            test_result.append(
                {
                    "id": issue_id,
                    "host": "cluster",
                    "severity": SEVERITY.HIGH,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"],
                }
            )
        if len(active_mongos) == 1:
            issue_id = ISSUE.SINGLE_MONGOS
            test_result.append(
                {
                    "id": issue_id,
                    "host": "cluster",
                    "severity": SEVERITY.HIGH,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(host=active_mongos[0]),
                }
            )
        return test_result, data
