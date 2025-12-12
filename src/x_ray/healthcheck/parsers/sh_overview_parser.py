from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.healthcheck.shared import MAX_MONGOS_PING_LATENCY


class SHOverviewParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        """
        Parse cluster information data.

        Args:
            data (list): The clusterInfo command output of all hosts.

        Returns:
            list: The parsed cluster information as a list of table items.
        """
        raw_result = data.get("rawResult", None)
        output_list = []
        overview_table = {
            "type": "table",
            "caption": "Sharded Cluster Overview",
            "header": ["#Shards", "#Mongos", "#Active mongos"],
            "rows": [],
        }
        mongos_table = {
            "type": "table",
            "caption": "Component Details - `mongos`",
            "header": ["Host", "Ping Latency (sec)", "Last Ping"],
            "rows": [],
        }

        if raw_result is None:
            mongos_table["rows"].append(["n/a", "n/a", "n/a"])
            return
        component_names = data["map"].keys()
        shards = sum(1 for name in component_names if name not in ["mongos", "config"])
        mongos = len(data["map"]["mongos"]["members"])
        active_mongos = 0
        for host, info in raw_result.items():
            ping_latency = info.get("pingLatencySec", 0)
            last_ping = info.get("lastPing", False)
            mongos_table["rows"].append([host, ping_latency, last_ping])
            if ping_latency < MAX_MONGOS_PING_LATENCY:
                active_mongos += 1
        overview_table["rows"].append([shards, mongos, active_mongos])
        output_list.append(overview_table)
        output_list.append(mongos_table)
        return output_list
