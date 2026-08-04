from datetime import datetime
import enum
import json
from typing import Iterable
from bson.json_util import object_hook
from bson.timestamp import Timestamp
from x_ray.utils import to_ejson


class ShardNameMapper:
    """
    Maps long shard names to short aliases so that tables stay readable.
    The config server replica set (``config``) is mapped to ``c``; real
    shards get s0/s1/... aliases assigned in sorted shard-name order,
    keeping the mapping deterministic across runs.
    """

    def __init__(self, shard_names: Iterable[str] = ()) -> None:
        names = set(shard_names)
        self._mapping: dict[str, str] = {}
        if "config" in names:
            self._mapping["config"] = "c"
        shards = sorted(
            (name for name in names if name != "config"),
            key=lambda name: (name.casefold(), name),
        )
        self._mapping.update({name: f"s{i}" for i, name in enumerate(shards)})

    def map(self, shard_name: str) -> str:
        """Return the short alias for a shard name, unchanged if not mapped."""
        return self._mapping.get(shard_name, shard_name)

    def notes(self) -> str:
        """Bulleted mapping list to render before a table, or an empty string."""
        if not self._mapping:
            return ""
        return "\n".join(f"- {short}: {long}" for long, short in self._mapping.items())


def to_json(obj, indent=None):
    cls_maps = [{"class": datetime, "func": lambda o: o.isoformat()}]
    return to_ejson(obj, indent=indent, cls_maps=cls_maps)


def load_json(json_str: str):
    # Custom object hook to handle legacy $timestamp format
    def custom_hook(obj):
        if "$timestamp" in obj:
            ts_str = obj["$timestamp"]
            if isinstance(ts_str, str):
                ts = int(ts_str)
                t = ts >> 32
                i = ts & 0xFFFFFFFF
                return Timestamp(t, i)
        obj = object_hook(obj)
        return obj

    return json.loads(json_str, object_hook=custom_hook)


class GMD_EVENTS(enum.Enum):
    SERVER_BUILD_INFO = "server_build_info"
    HOST_INFO = "host_info"
    ISMASTER = "ismaster"
    REPLICA_STATUS = "replica_status"
    REPLICA_SET_CONFIG = "replica_set_config"
    REPLICA_INFO = "replica_info"
    SERVER_STATUS_INFO = "server_status_info"
    ROUTERS = "routers"
    SHARDS = "shards"
    SERVER_PARAMETERS = "server_parameters"
    UNKNOWN = "unknown"
    COMMAND_LINE_INFO = "command_line_info"
    SHARDED_DATABASES = "sharded_databases"
    LIST_OF_DATABASES = "list_of_databases"
    COLLECTION_STATS = "collection_stats_(mb)"
    DATABASE_STATS = "database_stats_(mb)"
    INDEXES = "indexes"
    INDEX_STATS = "index_stats"
