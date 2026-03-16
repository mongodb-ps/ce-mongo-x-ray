from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown


class ConnParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        rows: list[list[str]] = []
        output_list: list = []
        conn_table = {
            "type": "table",
            "caption": "Connections",
            "notes": "- `Rejected` is only available for MongoDB 6.3 and later.\n"
            + "- `Threaded` is only available for MongoDB 5.0 and later.\n",
            "header": ["Component", "Host", "Current", "Available", "Active", "Created", "Rejected", "Threaded"],
            "rows": rows,
        }
        conn_data: dict = {}
        output_list.append(conn_table)
        output_list.append({"type": "chart", "data": conn_data})
        for item in data:
            set_name = item.get("set_name", "unknown_set")
            host = item.get("host", "unknown_host")
            conns = item.get("connections", None)
            if not conns:
                rows.append([set_name, host, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
                conn_data[f"{set_name}/{host}"] = {
                    "current": 0,
                    "available": 0,
                    "active": 0,
                    "totalCreated": 0,
                    "rejected": 0,
                    "threaded": 0,
                }
                continue
            rows.append(
                [
                    escape_markdown(set_name),
                    host,
                    str(conns.get("current", "0")),
                    str(conns.get("available", "0")),
                    str(conns.get("active", "0")),
                    str(conns.get("created", "0")),
                    str(conns.get("rejected", "N/A")),
                    str(conns.get("threaded", "N/A")),
                ]
            )
            conn_data[f"{set_name}/{host}"] = {
                "current": conns.get("current", 0),
                "available": conns.get("available", 0),
                "active": conns.get("active", 0),
                "totalCreated": conns.get("totalCreated", 0),
                "rejected": conns.get("rejected", 0),
                "threaded": conns.get("threaded", 0),
            }

        return output_list
