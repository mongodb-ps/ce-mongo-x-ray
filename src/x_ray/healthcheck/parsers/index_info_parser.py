from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown, format_json_md


class IndexInfoParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        set_name = kwargs.get("set_name", "Unknown")
        output_list: list[dict] = []
        rows: list[list[str]] = []
        table = {
            "type": "table",
            "caption": "Index Review",
            "header": ["Component", "Namespace", "Name", {"text": "Definition", "align": "left"}, "Access per Hour"],
            "rows": rows,
        }
        output_list.append(table)
        if data is None:
            rows.append([set_name] + ["N/A"] * 4)
            return output_list
        for item in data:
            ns = item["ns"]
            capture_time = item["captureTime"]
            for stats in item["indexStats"]:
                component = stats.get("shard", set_name)
                key_md = format_json_md(stats["key"], indent=None)
                access = stats["accesses"]
                ops = access.get("ops", 0)
                since = access.get("since", None)
                spec = stats.get("spec", {})
                options = get_index_options(spec)
                options_md = f"<pre>{format_json_md(options)}</pre>" if len(options) > 0 else ""
                access_per_hour = ops / (capture_time - since).total_seconds() * 3600
                rows.append(
                    [
                        escape_markdown(component),
                        escape_markdown(ns),
                        escape_markdown(stats["name"]),
                        f"`{key_md}`{options_md}",
                        f"{access_per_hour:.4f}",
                    ]
                )
        return output_list


def get_index_options(spec):
    options = {}
    for key, value in spec.items():
        if key not in ["key", "name", "v"]:
            options[key] = value
    return options
