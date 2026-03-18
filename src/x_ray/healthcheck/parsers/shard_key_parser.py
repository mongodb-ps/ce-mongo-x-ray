from typing import Any

from x_ray.utils import format_json_md, format_size
from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown


class ShardKeyParser(BaseParser):
    def parse(self, data: Any, **kwargs) -> list:
        output_list: list = []
        rows: list[list[str]] = []
        table: dict = {
            "type": "table",
            "caption": "Shard Keys",
            "header": [
                "Namespace",
                "Shard Key",
                {"text": "Data Size", "align": "left"},
                {"text": "Storage Size", "align": "left"},
                {"text": "Index Size", "align": "left"},
                {"text": "Docs Count", "align": "left"},
            ],
            "rows": rows,
        }
        output_list.append(table)
        if data is None:
            rows.append(["N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
            return output_list

        collections = data["shardedCollections"]
        all_stats = data["stats"]
        for coll in collections:
            ns = coll["_id"]
            key = coll["key"]
            key_md = escape_markdown(format_json_md(key, indent=None))
            stats = all_stats.get(ns, {})
            data_size = sum(s["size"] for s in stats.values())
            data_size_detail = "<br/>".join(
                [f"{escape_markdown(s_name)}: {format_size(s['size'])}" for s_name, s in stats.items()]
            )
            storage_size = sum(s["storageSize"] for s in stats.values())
            storage_size_detail = "<br/>".join(
                [f"{escape_markdown(s_name)}: {format_size(s['storageSize'])}" for s_name, s in stats.items()]
            )
            index_size = sum(s["totalIndexSize"] for s in stats.values())
            index_size_detail = "<br/>".join(
                [f"{escape_markdown(s_name)}: {format_size(s['totalIndexSize'])}" for s_name, s in stats.items()]
            )
            docs_count = sum(s["count"] for s in stats.values())
            docs_count_detail = "<br/>".join(
                [f"{escape_markdown(s_name)}: {s['count']}" for s_name, s in stats.items()]
            )
            rows.append(
                [
                    escape_markdown(ns),
                    key_md,
                    f"{format_size(data_size)}<br/><pre>{data_size_detail}</pre>",
                    f"{format_size(storage_size)}<br/><pre>{storage_size_detail}</pre>",
                    f"{format_size(index_size)}<br/><pre>{index_size_detail}</pre>",
                    f"{docs_count}<br/><pre>{docs_count_detail}</pre>",
                ]
            )
        return output_list
