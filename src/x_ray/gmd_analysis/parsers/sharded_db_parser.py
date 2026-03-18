from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown


class ShardedDBParser(BaseParser):
    def parse(self, data: dict, **kwargs) -> list:
        """
        Parse sharded database information.

        Args:
            data (dict): Information about sharded databases.

        Returns:
            list: The parsed sharded database information as a list of table items.
        """
        output_list: list = []
        rows: list = []
        coll_rows: list = []
        sharded_db_table = {
            "type": "table",
            "caption": "Sharded Databases",
            "header": ["Database Name", "Primary Database", "Is Partitioned"],
            "rows": rows,
        }
        sharded_coll_table = {
            "type": "table",
            "caption": "Sharded Collections",
            "header": ["Namespace", "Shard Key"],
            "rows": coll_rows,
        }
        for db in data:
            db_name: str = db["_id"]
            primary: str = db["primary"]
            partitioned: bool = db["partitioned"]
            rows.append([db_name, primary, partitioned])
            for coll in db.get("collections", []):
                coll_name: str = coll["_id"]
                shard_key: dict = escape_markdown(coll["key"])
                coll_rows.append([coll_name, shard_key])

        output_list.append(sharded_db_table)
        output_list.append(sharded_coll_table)
        return output_list
