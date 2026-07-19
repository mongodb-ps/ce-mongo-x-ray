"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from typing import Optional, Union
import html as html_mod
import os
import logging
from abc import ABC, abstractmethod
import gzip
from bson import json_util
from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.shared import SEVERITY, to_json
from x_ray.utils import env, get_script_path, to_ejson


def colorize_severity(severity: SEVERITY) -> str:
    mapping = {
        SEVERITY.HIGH.name: "red",
        SEVERITY.MEDIUM.name: "orange",
        SEVERITY.LOW.name: "green",
        SEVERITY.INFO.name: "gray",
    }
    return mapping.get(severity.name, "black")


TABLE_ALIGNMENT = {
    "left": ":----------",
    "right": "----------:",
    "center": ":----------:",
}


class BaseItem(ABC):
    _name: str
    _test_result: list
    _config: dict

    def __init__(self, output_folder: str, config: Optional[dict] = None, **kwargs) -> None:
        self._config: dict = config or {}
        self._test_result: list = []
        self._logger = logging.getLogger(self.__class__.__name__)
        self._output_folder: str = output_folder if output_folder.endswith("/") else f"{output_folder}/"
        self._rules: dict[str, BaseRule] = {}

    @abstractmethod
    def test(self, *args, **kwargs) -> None:
        pass

    @property
    def name(self):
        return self._name

    @property
    def description(self) -> str:
        desc: str = ""
        for rule in self._rules.values():
            desc += rule.description_md + "\n"
        return desc

    @property
    def captured_sample(self) -> Optional[Union[dict, list]]:
        try:
            if self.cache_file_name.endswith(".gz"):
                with gzip.open(self.cache_file_name, "rt") as f:
                    return json_util.loads(f.read())
            else:
                with open(self.cache_file_name, "r", encoding="utf-8") as f:
                    return json_util.loads(f.read())
        except FileNotFoundError:
            return None

    @captured_sample.setter
    def captured_sample(self, data: Union[dict, list]) -> None:
        if self.cache_file_name.endswith(".gz"):
            with gzip.open(self.cache_file_name, "wt") as f:
                f.write(to_ejson(data))
        else:
            with open(self.cache_file_name, "w", encoding="utf-8") as f:
                f.write(to_ejson(data))

    @property
    def test_result(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "items": self._test_result,
        }

    @property
    def test_result_markdown(self) -> str:
        result = ""
        if len(self._test_result) == 0:
            result += "<b style='color: green;'>Pass.</b>\n\n"
            return result

        result += (
            '| <span data-sortable="false">\\#</span>{60px}'
            ' | <span data-sortable="true">Host</span>{180px}'
            ' | <span data-sortable="true">Severity</span>{120px}'
            ' | <span data-sortable="true">Category</span>{200px}'
            ' | <span data-sortable="false">Message</span>{*} |\n'
        )
        result += "|:----------:|:----------:|:----------:|---------|---------|\n"
        for idx, item in enumerate(self._test_result):
            severity = item["severity"]
            severity_cell = (
                f'<span data-sort-value="{severity.value}">'
                f"<b style='color: {colorize_severity(severity)}'>"
                f" {severity.name} </b></span>"
            )
            result += (
                f"| **{idx + 1}** "
                f"| `{item['host']}` "
                f"| {severity_cell} "
                f"| {item['title']} "
                f"| {item['message']} |\n"
            )
        result += "\n"
        return result

    @property
    def review_result(self) -> dict:
        return {"name": self.name, "description": self.description, "data": []}

    @property
    def review_result_markdown(self) -> str:
        result_data = self.review_result["data"]
        result = ""
        if len(result_data) == 0:
            result += "(No data)\n\n"
            return result
        i = 0
        for j, block in enumerate(result_data):
            chart_type = block.get("type")
            caption = block.get("caption")
            notes = block.get("notes", "")
            if chart_type == "table":
                result += f"#### ({i + 1}) {caption}\n"
                result += f"{notes}\n"
                columns = block.get("columns", [])
                header_parts = []
                for col in columns:
                    name = col.get("name", "(NOT SET)")
                    sortable = col.get("sortable", True)
                    header_parts.append(f'<span data-sortable="{"true" if sortable else "false"}">{name}</span>')
                align = [TABLE_ALIGNMENT.get(col.get("align", "center"), TABLE_ALIGNMENT["center"]) for col in columns]
                result += f"|{'|'.join(header_parts)}|\n"
                result += f"|{'|'.join(align)}|\n"
                for row in block.get("rows", []):
                    row_text = []
                    for cell in row:
                        if isinstance(cell, tuple):
                            display, sort_value = cell
                            row_text.append(
                                f'<span data-sort-value="{html_mod.escape(str(sort_value), quote=True)}">{display}</span>'
                            )
                        else:
                            row_text.append(str(cell))
                    result += "|" + "|".join(row_text) + "|\n"
                result += "\n"
                i += 1
            elif chart_type == "chart":
                result += f'<div id="container_{self.__class__.__name__}_{j}"></div>'
                result += "<script type='text/javascript'>\n"
                result += "(function() {\n"
                result += f"const container = document.getElementById('container_{self.__class__.__name__}_{j}');\n"
                result += f"let data = {to_json(block.get('data'))};\n"
                file_name = f"{self.__class__.__name__}_{j}.js"
                file_path = os.path.join("templates", "healthcheck", "snippets", file_name)
                file_path = get_script_path(file_path)
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as js_file:
                        for line in js_file:
                            result += line.replace("{name}", self.__class__.__name__)
                result += "})()\n"
                result += "</script>\n"
        return result

    @property
    def cache_file_name(self) -> str:
        if env == "development":
            return f"{self._output_folder}{self.__class__.__name__}_raw.json"
        return f"{self._output_folder}{self.__class__.__name__}_raw.json.gz"

    def append_test_result(self, host: str, severity: SEVERITY, title: str, message: str) -> None:
        self._test_result.append({"host": host, "severity": severity, "title": title, "message": message})

    def append_test_results(self, items: list) -> None:
        for item in items:
            self.append_test_result(item["host"], item["severity"], item["title"], item["description"])
