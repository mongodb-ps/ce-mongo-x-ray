from datetime import datetime
from x_ray.utils import to_ejson


def to_json(obj, indent=None):
    cls_maps = [{"class": datetime, "func": lambda o: o.isoformat()}]
    return to_ejson(obj, indent=indent, cls_maps=cls_maps)
