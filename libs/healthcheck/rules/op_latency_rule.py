from libs.healthcheck.rules.base_rule import BaseRule
from libs.healthcheck.shared import MAX_MONGOS_PING_LATENCY, SEVERITY
from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP


class OpLatencyRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._op_latency_ms = self._thresholds.get("op_latency_ms", 100)  # in milliseconds

    def apply(self, data: dict, result_template=None) -> tuple:
        """Check the operation latency for any issues.

        Args:
            data (object): The collStats data.
            result_template (object, optional): The template for the result. Defaults to None.
        Returns:
            list: A list of operation latency check results.
        """
        template = result_template or {}
        test_result = []
        latency_stats = data.get("latencyStats", {})
        reads, writes, commands, transactions = (
            latency_stats["reads"],
            latency_stats["writes"],
            latency_stats["commands"],
            latency_stats["transactions"],
        )
        r_latency, w_latency, c_latency, t_latency = (
            reads["latency"],
            writes["latency"],
            commands["latency"],
            transactions["latency"],
        )
        r_ops, w_ops, c_ops, t_ops = (
            reads["ops"],
            writes["ops"],
            commands["ops"],
            transactions["ops"],
        )
        avg_r_latency = r_latency / r_ops if r_ops > 0 else 0
        avg_w_latency = w_latency / w_ops if w_ops > 0 else 0
        avg_c_latency = c_latency / c_ops if c_ops > 0 else 0
        avg_t_latency = t_latency / t_ops if t_ops > 0 else 0
        if avg_r_latency > self._op_latency_ms:
            issue_id = ISSUE.HIGH_READ_LATENCY
            test_result.append(
                template
                | {
                    "id": issue_id,
                    "severity": SEVERITY.MEDIUM,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                        ns=data.get("ns", ""),
                        avg_r_latency=avg_r_latency,
                        op_latency_ms=self._op_latency_ms,
                    ),
                }
            )
        if avg_w_latency > self._op_latency_ms:
            issue_id = ISSUE.HIGH_WRITE_LATENCY
            test_result.append(
                template
                | {
                    "id": issue_id,
                    "severity": SEVERITY.MEDIUM,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                        ns=data.get("ns", ""),
                        avg_w_latency=avg_w_latency,
                        op_latency_ms=self._op_latency_ms,
                    ),
                }
            )
        if avg_c_latency > self._op_latency_ms:
            issue_id = ISSUE.HIGH_COMMAND_LATENCY
            test_result.append(
                template
                | {
                    "id": issue_id,
                    "severity": SEVERITY.MEDIUM,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                        ns=data.get("ns", ""),
                        avg_c_latency=avg_c_latency,
                        op_latency_ms=self._op_latency_ms,
                    ),
                }
            )
        if avg_t_latency > self._op_latency_ms:
            issue_id = ISSUE.HIGH_TRANSACTION_LATENCY
            test_result.append(
                template
                | {
                    "id": issue_id,
                    "severity": SEVERITY.MEDIUM,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                        ns=data.get("ns", ""),
                        avg_t_latency=avg_t_latency,
                        op_latency_ms=self._op_latency_ms,
                    ),
                }
            )
        return test_result, {
            "latencyStats": {
                "reads_latency": avg_r_latency,
                "writes_latency": avg_w_latency,
                "commands_latency": avg_c_latency,
                "transactions_latency": avg_t_latency,
            }
        }
