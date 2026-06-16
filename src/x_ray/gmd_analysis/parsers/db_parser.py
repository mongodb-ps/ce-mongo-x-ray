from x_ray.gmd_analysis.parsers.base_parser import BaseParser
from x_ray.utils import format_size


class DBParser(BaseParser):
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
        db_table = {
            "type": "table",
            "caption": "Databases",
            "header": [
                "Database Name",
                {"text": "Data Size", "align": "left"},
                {"text": "Storage Size", "align": "left"},
                "Is Sharded",
                "Is Primary",
                "# Collections",
                "# Views",
                "# Objects",
                "# Indexes",
            ],
            "rows": rows,
        }
        db_data: list = []
        dbs: list = data.get("databases", {}).get("databases", [])
        sharded_dbs: list = data.get("sharded_databases", None)
        db_stats: dict = data.get("db_stats", {})
        for db in dbs:
            db_name: str = db["name"]
            stats: dict = db_stats.get(db_name, {})
            data_size: str = format_size(stats.get("dataSize", 0) * 1024 * 1024)
            num_collections: int = stats.get("collections", 0)
            num_views: int = stats.get("views", 0)
            num_objects: int = stats.get("objects", 0)
            num_indexes: int = stats.get("indexes", 0)
            storage_size: str = format_size(db.get("sizeOnDisk", 0))
            sharded_sizes: list = []
            for shard, size in db.get("shards", {}).items():
                sharded_sizes.append(f"{shard}: {format_size(size)}")
            if len(sharded_sizes) > 0:
                storage_size += "<pre>" + "<br>".join(sharded_sizes) + "</pre>"
            if sharded_dbs is None:
                partitioned = "N/A"
                primary_db = "N/A"
            else:
                sharded_db_info = next((item for item in sharded_dbs if item["_id"] == db_name), None)
                partitioned = sharded_db_info["partitioned"] if sharded_db_info else False
                primary_db = sharded_db_info["primary"] if sharded_db_info else "N/A"
            rows.append(
                [
                    db_name,
                    data_size,
                    storage_size,
                    partitioned,
                    primary_db,
                    num_collections,
                    num_views,
                    num_objects,
                    num_indexes,
                ]
            )

            data_line = {}
            data_line["name"] = db_name
            data_line["dataSize"] = stats.get("dataSize", 0)
            data_line["storageSize"] = db.get("sizeOnDisk", 0)
            data_line["collections"] = stats.get("collections", 0)
            data_line["views"] = stats.get("views", 0)
            data_line["objects"] = stats.get("objects", 0)
            data_line["indexes"] = stats.get("indexes", 0)
            db_data.append(data_line)
        output_list.append(db_table)
        output_list.append({"type": "chart", "data": db_data})
        return output_list
