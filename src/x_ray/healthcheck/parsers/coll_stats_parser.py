from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown, format_size


class CollStatsParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        """
        Parse collection information data.

        Args:
            data (list): The collStats command output of all collections.

        Returns:
            list: The parsed collection information as a list of table items.
        """
        host: str = kwargs.get("host", "unknown_host")
        set_name: str = kwargs.get("set_name", "unknown_set")
        output_list: list[dict] = []
        frag_rows: list[list[str]] = []
        lat_rows: list[list[str]] = []
        data_frag: list[dict] = []
        data_latency: list[dict] = []
        frag_table = {
            "type": "table",
            "caption": "Storage Fragmentation",
            "header": [
                "Component",
                "Host",
                "Namespace",
                "Collection Fragmentation",
                {"text": "Index Fragmentation", "align": "left"},
            ],
            "rows": frag_rows,
        }
        latency_table = {
            "type": "table",
            "caption": "Operation Latency",
            "header": [
                "Component",
                "Host",
                "Namespace",
                "Read Latency",
                "Write Latency",
                "Command Latency",
                "Transaction Latency",
            ],
            "rows": lat_rows,
        }
        output_list.append(frag_table)
        output_list.append({"type": "chart", "data": data_frag})
        output_list.append(latency_table)
        output_list.append({"type": "chart", "data": data_latency})
        if data is None:
            frag_rows.append([host, "n/a", "n/a", "n/a"])
            lat_rows.append([host, "n/a", "n/a", "n/a", "n/a", "n/a", "n/a"])
            return output_list
        for stats in data:
            ns = stats["ns"]
            # Fragmentation visualization
            coll_frag = stats.get("collFragmentation", {}).get("fragmentation", 0)
            index_frags = stats.get("indexFragmentations", [])
            total_reusable_size = 0
            total_index_size = 0
            index_details = []
            for index in index_frags:
                total_reusable_size += index.get("reusable", 0)
                total_index_size += index.get("totalSize", 0)
                index_name = escape_markdown(index.get("indexName", ""))
                fragmentation = index.get("fragmentation", 0)
                index_details.append(f"{index_name}: {fragmentation:.2%}")
            index_frag = round(total_reusable_size / total_index_size, 4) if total_index_size > 0 else 0
            frag_rows.append(
                [
                    escape_markdown(set_name),
                    host,
                    escape_markdown(ns),
                    f"{coll_frag:.2%}",
                    f"{index_frag:.2%}<br/><pre>{'<br/>'.join(index_details)}</pre>",
                ]
            )
            label = f"{set_name}/{host}"
            data_frag.append(
                {
                    "label": label,
                    "ns": ns,
                    "collFrag": coll_frag,
                    "indexFrag": index_frag,
                }
            )
            # Latency visualization
            avg_reads_latency = stats.get("latencyStats", {}).get("reads_latency", 0)
            avg_writes_latency = stats.get("latencyStats", {}).get("writes_latency", 0)
            avg_commands_latency = stats.get("latencyStats", {}).get("commands_latency", 0)
            avg_transactions_latency = stats.get("latencyStats", {}).get("transactions_latency", 0)
            lat_rows.append(
                [
                    escape_markdown(set_name),
                    host,
                    escape_markdown(ns),
                    f"{avg_reads_latency:.2f}ms",
                    f"{avg_writes_latency:.2f}ms",
                    f"{avg_commands_latency:.2f}ms",
                    f"{avg_transactions_latency:.2f}ms",
                ]
            )
            data_latency.append(
                {
                    "label": label,
                    "ns": ns,
                    "readsLatency": avg_reads_latency,
                    "writesLatency": avg_writes_latency,
                    "commandsLatency": avg_commands_latency,
                    "transactionsLatency": avg_transactions_latency,
                }
            )
        return output_list
