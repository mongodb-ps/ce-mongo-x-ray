from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class ShardKeyRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check shard key configurations for issues.

        Args:
            data (object): One document from `config.collections`.
            extra_info (dict, optional): Extra information such as host.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        test_results = []
        ns = data["_id"]
        key = data["key"]
        v = key.get("_id", None)
        if v in [-1, 1] and len(key.keys()) == 1:
            issue = create_issue(
                ISSUE.IMPROPER_SHARD_KEY,
                host="cluster",
                params={
                    "ns": ns,
                    "shard_key": f"{{_id: {v}}}",
                },
            )
            test_results.append(issue)
        return test_results, data
