from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown


class OpcounterParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        output_list: list = []
        rows: list[list[str]] = []
        ops_table = {
            "type": "table",
            "caption": "Operation Counters",
            "header": ["Component", "Host", "Inserts", "Queries", "Updates", "Deletes", "Commands", "Getmores"],
            "rows": rows,
        }
        ops_data: dict = {}
        output_list.append(ops_table)
        output_list.append({"type": "chart", "data": ops_data})
        for item in data:
            set_name = item.get("set_name", "unknown_set")
            host = item.get("host", "unknown_host")
            ops = item.get("op_counters", None)
            if not ops:
                rows.append([set_name, host, "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
                ops_data[f"{set_name}/{host}"] = {
                    "insert": 0,
                    "query": 0,
                    "update": 0,
                    "delete": 0,
                    "command": 0,
                    "getmore": 0,
                }
                continue
            rows.append(
                [
                    escape_markdown(set_name),
                    host,
                    ops.get("insert", 0),
                    ops.get("query", 0),
                    ops.get("update", 0),
                    ops.get("delete", 0),
                    ops.get("command", 0),
                    ops.get("getmore", 0),
                ]
            )
            ops_data[f"{set_name}/{host}"] = {
                "insert": ops.get("insert", 0),
                "query": ops.get("query", 0),
                "update": ops.get("update", 0),
                "delete": ops.get("delete", 0),
                "command": ops.get("command", 0),
                "getmore": ops.get("getmore", 0),
            }
        return output_list
