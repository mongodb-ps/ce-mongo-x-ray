from x_ray.gmd_analysis.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown, format_size


class CollStatsParser(BaseParser):
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
            "header": [
                "NS",
                {"text": "Count", "align": "left"},
                {"text": "Data Size", "align": "left"},
                {"text": "Storage Size", "align": "left"},
                {"text": "Avg Object Size", "align": "left"},
                {"text": "Total Index Size", "align": "left"},
                {"text": "Fragmentation Ratio", "align": "left"},
                {"text": "Cached", "align": "left"},
            ],
            "rows": rows,
        }
        output_list.append(stats_table)
        output_list.append({"type": "chart", "data": data_sizes})
        for stats in data:
            ns = stats["ns"]
            count = stats.get("count", 0)
            size = stats.get("size", 0) * 1024**2
            storage_size = stats.get("storageSize", 0) * 1024**2
            avg_obj_size = stats.get("avgObjSize", 0)
            total_index_size = stats.get("totalIndexSize", 0) * 1024**2
            # Calculate fragmentation ratio using WiredTiger block manager stats if available
            wt: dict = stats.get("wiredTiger", {})
            block_manager: dict = wt.get("block-manager", {})
            reusable_bytes = block_manager.get("file bytes available for reuse", 0)
            file_bytes = block_manager.get("file size in bytes", 0)
            frag_ratio = (reusable_bytes / file_bytes) if file_bytes > 0 else 0
            # Calculate cache bytes and ratio if available
            cache: dict = wt.get("cache", {})
            bytes_in_cache = cache.get("bytes currently in the cache", 0)
            cache_ratio = (bytes_in_cache / size) if size > 0 else 0

            # display values
            count_str = f"{count}"
            size_str = format_size(size)
            storage_size_str = format_size(storage_size)
            avg_obj_size_str = format_size(avg_obj_size)
            total_index_size_str = format_size(total_index_size)
            frag_ratio_str = f"{frag_ratio:.2%}"
            cache_sum_str = f"{format_size(bytes_in_cache)} / {cache_ratio:.2%}"
            if stats.get("sharded", False):
                shards = stats.get("shards", {})
                sh_counts = []
                sh_sizes = []
                sh_storage_sizes = []
                sh_avg_obj_sizes = []
                sh_total_index_sizes = []
                sh_fragmentation_ratios = []
                sh_caches = []
                for sh_name, sh_stats in shards.items():
                    sh_count = sh_stats.get("count", 0)
                    sh_size = sh_stats.get("size", 0) * 1024**2
                    sh_avg_obj_size = sh_stats.get("avgObjSize", 0)
                    sh_storage_size = sh_stats.get("storageSize", 0) * 1024**2
                    sh_total_index_size = sh_stats.get("totalIndexSize", 0) * 1024**2
                    sh_wt: dict = sh_stats.get("wiredTiger", {})
                    sh_block_manager: dict = sh_wt.get("block-manager", {})
                    sh_reusable_bytes = sh_block_manager.get("file bytes available for reuse", 0)
                    sh_file_bytes = sh_block_manager.get("file size in bytes", 0)
                    sh_frag_ratio = f"{(sh_reusable_bytes / sh_file_bytes) if sh_file_bytes > 0 else 0:.2%}"
                    sh_cache: dict = sh_wt.get("cache", {})
                    sh_bytes_in_cache = sh_cache.get("bytes currently in the cache", 0)
                    sh_cache_ratio = f"{(sh_bytes_in_cache / sh_size) if sh_size > 0 else 0:.2%}"
                    sh_counts.append(f"{sh_name}: {sh_count}")
                    sh_sizes.append(f"{sh_name}: {format_size(sh_size)}")
                    sh_storage_sizes.append(f"{sh_name}: {format_size(sh_storage_size)}")
                    sh_total_index_sizes.append(f"{sh_name}: {format_size(sh_total_index_size)}")
                    sh_avg_obj_sizes.append(f"{sh_name}: {format_size(sh_avg_obj_size)}")
                    sh_fragmentation_ratios.append(f"{sh_name}: {sh_frag_ratio}")
                    sh_caches.append(f"{sh_name}: {format_size(sh_bytes_in_cache)} / {sh_cache_ratio}")
                count_str = f"{count_str}<pre>" + "<br>".join(sh_counts) + "</pre>"
                size_str = f"{size_str}<pre>" + "<br>".join(sh_sizes) + "</pre>"
                storage_size_str = f"{storage_size_str}<pre>" + "<br>".join(sh_storage_sizes) + "</pre>"
                total_index_size_str = f"{total_index_size_str}<pre>" + "<br>".join(sh_total_index_sizes) + "</pre>"
                avg_obj_size_str = f"{avg_obj_size_str}<pre>" + "<br>".join(sh_avg_obj_sizes) + "</pre>"
                frag_ratio_str = f"{frag_ratio_str}<pre>" + "<br>".join(sh_fragmentation_ratios) + "</pre>"
                cache_sum_str = f"{cache_sum_str}<pre>" + "<br>".join(sh_caches) + "</pre>"
            rows.append(
                [
                    escape_markdown(ns),
                    count_str,
                    size_str,
                    storage_size_str,
                    avg_obj_size_str,
                    total_index_size_str,
                    frag_ratio_str,
                    cache_sum_str,
                ]
            )
            data_sizes[ns] = {"size": size, "index_size": total_index_size}
        return output_list
