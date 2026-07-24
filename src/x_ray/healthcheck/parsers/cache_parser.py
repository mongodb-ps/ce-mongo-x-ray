from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown, format_size


class CacheParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        output_list: list = []
        rows: list[list[str]] = []
        cache_table = {
            "type": "table",
            "caption": "WiredTiger Cache",
            "header": [
                {"text": "Component", "width": "120px"},
                {"text": "Host", "width": "*"},
                {"text": "Cache Size", "width": "150px"},
                {"text": "In-Cache Size", "width": "150px"},
                {"text": "Bytes Dirty", "width": "150px"},
                {"text": "Read Into", "width": "150px"},
                {"text": "Written From", "width": "150px"},
            ],
            "rows": rows,
        }
        cache_data: dict = {}
        output_list.append(cache_table)
        output_list.append({"type": "chart", "data": cache_data})
        for item in data:
            set_name = item.get("set_name", "unknown_set")
            host = item.get("host", "unknown_host")
            cache = item.get("cache", None)
            if not cache:
                rows.append([escape_markdown(set_name), host, "N/A", "N/A", "N/A", "N/A", "N/A"])
                cache_data[f"{set_name}/{host}"] = {
                    "cacheSize": 0,
                    "inCacheSize": 0,
                    "readInto": 0,
                    "forUpdates": 0,
                    "dirty": 0,
                    "writtenFrom": 0,
                }
                continue
            rows.append(
                [
                    escape_markdown(set_name),
                    escape_markdown(host),
                    (format_size(cache.get("cacheSize", 0)), cache.get("cacheSize", 0)),
                    (format_size(cache.get("inCacheSize", 0)), cache.get("inCacheSize", 0)),
                    (format_size(cache.get("dirty", 0)), cache.get("dirty", 0)),
                    (f"{format_size(cache.get('readInto', 0))}/s" if cache.get("readInto", 0) != "N/A" else "N/A",
                     cache.get("readInto", 0) if cache.get("readInto", 0) != "N/A" else 0),
                    (f"{format_size(cache.get('writtenFrom', 0))}/s" if cache.get("writtenFrom", 0) != "N/A" else "N/A",
                     cache.get("writtenFrom", 0) if cache.get("writtenFrom", 0) != "N/A" else 0),
                ]
            )
            cache_data[f"{set_name}/{host}"] = {
                "cacheSize": cache.get("cacheSize", 0),
                "inCacheSize": cache.get("inCacheSize", 0),
                "readInto": cache.get("readInto", 0),
                "forUpdates": cache.get("forUpdates", 0),
                "dirty": cache.get("dirty", 0),
                "writtenFrom": cache.get("writtenFrom", 0),
            }
        return output_list
