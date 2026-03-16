from typing import Any
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown


class SecurityParser(BaseParser):
    def parse(self, data: Any, **kwargs) -> list:
        rows: list = []
        table: dict = {
            "type": "table",
            "caption": "Security Information",
            "header": [
                "Component",
                "Host",
                "Listen",
                "TLS",
                "Authorization",
                "Cluster Auth",
                "Log Redaction",
                "EAR",
                "Auditing",
            ],
            "rows": rows,
        }
        for item in data:
            raw_result = item.get("rawResult")
            host = item.get("host")
            set_name = item.get("set_name", "")
            if raw_result is None:
                rows.append(
                    [
                        escape_markdown(set_name),
                        host,
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                        "N/A",
                    ]
                )
                continue
            parsed = raw_result.get("parsed", {})
            net = parsed.get("net", {})
            security = parsed.get("security", {})
            audit_log = parsed.get("auditLog", {})
            port = net.get("port", 27017)
            tls = net.get("tls", {}).get("mode", "disabled")
            authorization = security.get("authorization", "disabled")
            log_redaction = security.get("redactClientLogData", "disabled")
            eat = security.get("enableEncryption", "false")
            bind_ip = net.get("bindIp", "127.0.0.1")
            cluster_auth = security.get("clusterAuthMode", "disabled")
            audit = "enabled" if audit_log.get("destination", None) is not None else "disabled"
            rows.append(
                [
                    escape_markdown(set_name),
                    host,
                    f"{bind_ip}:{port}",
                    tls,
                    authorization,
                    cluster_auth,
                    log_redaction,
                    eat,
                    audit,
                ]
            )
        return [table]
