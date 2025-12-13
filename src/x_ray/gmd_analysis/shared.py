from datetime import datetime
import enum
import json
from bson.json_util import object_hook
from bson.timestamp import Timestamp
from x_ray.utils import to_ejson


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
    UNKNOWN = "unknown"
