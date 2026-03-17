from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown, format_size


class CollOverviewParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        """
        Parse collection information data.

        Args:
            data (list): The collInfo command output of all collections.

        Returns:
            list: The parsed collection information as a list of table items.
        """
        output_list: list[dict] = []
        rows: list[list[str]] = []
        data_sizes: dict[str, dict[str, int]] = {}
        stats_table = {
            "type": "table",
            "caption": "Storage Stats",
            "header": ["Namespace", "Size", "Storage Size", "Avg Object Size", "Total Index Size", "Index / Storage"],
            "rows": rows,
        }
        output_list.append(stats_table)
        output_list.append({"type": "chart", "data": data_sizes})
        if data is None:
            rows.append(["N/A", "N/A", "N/A", "N/A", "N/A", "N/A"])
            return output_list
        for stats in data:
            ns = stats["ns"]
            storage_stats = stats.get("storageStats", {})
            size = storage_stats.get("size", 0)
            storage_size = storage_stats.get("storageSize", 0)
            avg_obj_size = storage_stats.get("avgObjSize", 0)
            total_index_size = storage_stats.get("totalIndexSize", 0)
            index_data_ratio = round(total_index_size / storage_size, 4) if size > 0 else 0
            rows.append(
                [
                    escape_markdown(ns),
                    format_size(size),
                    format_size(storage_size),
                    format_size(avg_obj_size),
                    format_size(total_index_size),
                    f"{index_data_ratio:.2%}",
                ]
            )
            data_sizes[ns] = {"size": size, "index_size": total_index_size}
        return output_list
