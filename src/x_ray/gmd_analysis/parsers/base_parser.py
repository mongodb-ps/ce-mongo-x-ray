import os

from x_ray.parsers.base_parser import BaseParser as HCBaseParser


class BaseParser(HCBaseParser):
    """
    Base class for GMD analysis items. Inherits from the health check BaseItem and can be extended with GMD-specific functionality if needed.
    """

    TEMPLATE_FOLDER = os.path.join("templates", "gmd", "snippets")
