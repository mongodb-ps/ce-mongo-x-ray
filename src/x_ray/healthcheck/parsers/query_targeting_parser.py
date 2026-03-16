from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown


class QueryTargetingParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        output_list: list = []
        rows: list[list[str]] = []
        qt_table: dict = {
            "type": "table",
            "caption": "Query Targeting",
            "header": ["Component", "Host", "Scanned / Returned", "Scanned Objects / Returned"],
            "rows": rows,
        }
        output_list.append(qt_table)
        for item in data:
            set_name = item.get("set_name", "unknown_set")
            host = item.get("host", "unknown_host")
            query_targeting = item.get("query_targeting", None)
            if not query_targeting:
                qt_table["rows"].append([escape_markdown(set_name), host, "N/A", "N/A"])
                continue
            qt_table["rows"].append(
                [
                    escape_markdown(set_name),
                    host,
                    f"{query_targeting.get('scanned/returned', 0):.2f}",
                    f"{query_targeting.get('scanned_objects/returned', 0):.2f}",
                ]
            )
        return output_list
