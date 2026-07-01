"""Base class for FTDC result parsers."""

import os

from x_ray.healthcheck.parsers.base_parser import BaseParser as HCBaseParser


class BaseParser(HCBaseParser):
    """Render FTDC results using the common table/chart format."""

    TEMPLATE_FOLDER = os.path.join("templates", "ftdc", "snippets")
