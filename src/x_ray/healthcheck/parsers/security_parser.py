from typing import Any
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown, to_ejson


class SecurityParser(BaseParser):
    def parse(self, data: Any, **kwargs) -> list:
        rows: list = []
        table: dict = {
            "type": "table",
            "caption": "Security Information",
            "header": [
                {"text": "Component", "width": "120px"},
                {"text": "Host", "width": "*"},
                {"text": "Listen", "width": "150px"},
                {"text": "TLS", "width": "100px"},
                {"text": "Auth", "width": "120px"},
                {"text": "Cluster Auth", "width": "120px"},
                {"text": "Log Redaction", "width": "120px"},
                {"text": "EAR", "width": "80px"},
                {"text": "Auditing", "width": "120px"},
            ],
            "rows": rows,
        }
        cfgs: list[dict] = []
        for item in data:
            raw_result = item.get("command_line_opts")
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
            authorization = "enabled" if security.get("keyFile", None) is not None else "disabled"
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
            cfgs.append(
                {
                    "type": "code",
                    "language": "json",
                    "caption": f"Raw Config for `{host}`",
                    "code": to_ejson(raw_result),
                }
            )
        return [table] + cfgs
