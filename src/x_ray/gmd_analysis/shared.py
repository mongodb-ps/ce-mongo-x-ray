from datetime import datetime
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
