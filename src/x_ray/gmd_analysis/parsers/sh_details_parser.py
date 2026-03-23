from x_ray.healthcheck.parsers.base_parser import BaseParser


class SHDetailsParser(BaseParser):
    def parse(self, data: dict, **kwargs) -> list:
        """
        Parse sharding detailed information data.

        Args:
            data (dict): Information about shards and config servers.

        Returns:
            list: The parsed sharding detailed information as a list of table items.
        """
        rows: list = []
        for shard in data["shards"]:
            sh_name = shard["_id"]
            hosts = shard["host"].split("/")[1]
            rows.append([sh_name, hosts])
        csrs: list[str] = data["csrs"].split("/")
        rows.append(csrs)

        details_table = {
            "type": "table",
            "caption": "Component Details - `shards/csrs`",
            "header": ["Component Name", "Hosts"],
            "rows": rows,
        }
        return [details_table]
