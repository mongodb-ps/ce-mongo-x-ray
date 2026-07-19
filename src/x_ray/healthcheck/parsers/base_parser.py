"""Base parser for healthcheck results."""

from abc import ABC, abstractmethod
import html as html_mod
import os
from typing import Any
from uuid import uuid4
from x_ray.log_analysis.shared import to_json
from x_ray.utils import get_script_path
from x_ray.healthcheck.check_items.base_item import TABLE_ALIGNMENT


class BaseParser(ABC):
    TEMPLATE_FOLDER = os.path.join("templates", "healthcheck", "snippets")

    @abstractmethod
    def parse(self, data: Any, **kwargs) -> list:
        """
        Parse the given data into tables and charts.
        Args:
            data (Any): The data to be parsed.
        Returns:
            list (dict): The parsed list. Each element can be either
                        {"type": "table", "caption": str (optional), "header": list, "rows": list} or
                        {"type": "chart", "chart_type": str, "data": dict}
        """
        raise NotImplementedError("Subclasses must implement the parse method")

    def format_table(self, item, i) -> str:
        """
        Parse a table represented by header and rows into markdown.

        Args:
            item (dict): The table item containing
                caption (str, optional): The table caption.
                header (list): List of column names. Accepts strings or dicts
                    {"text": str, "align": "center"|"left"|"right", "width": str,
                     "sortable": bool}.
                    The optional ``width`` key sets the column width using the
                    ``{width}`` markdown syntax (e.g. ``"200"``, ``"50%"``, ``"*"``).
                    The optional ``sortable`` key controls whether the column
                    can be sorted (defaults to ``true``).
                rows (list): List of rows, where each row is a list of values.
                    A cell can be a plain string or a ``(display, sort_value)``
                    tuple to provide an explicit sort key.
            i (int): The index of the table in the output list, used for generating unique IDs if needed.
        Returns:
            str: Parsed table as a markdown string.
        """
        header = item.get("header", [])
        rows = item.get("rows", [])
        caption = item.get("caption", None)
        notes = item.get("notes", None)
        output = f"#### {caption}\n\n" if caption else ""
        if notes:
            output += notes + "\n\n"
        if rows is None or len(rows) == 0:
            output += "_No data available._\n"
            return output
        header_text_parts = []
        for h in header:
            if isinstance(h, dict):
                text = h["text"]
                width = h.get("width", "")
                sortable = h.get("sortable", True)
                span = f'<span data-sortable="{"true" if sortable else "false"}">{text}</span>'
                header_text_parts.append(f"{span}{{{width}}}" if width else span)
            else:
                header_text_parts.append(f'<span data-sortable="true">{h}</span>')
        alignments = [h.get("align", "center") if isinstance(h, dict) else "center" for h in header]
        align_md = [TABLE_ALIGNMENT[a] for a in alignments]
        output += f"|{'|'.join(header_text_parts)}|\n"
        output += f"|{'|'.join(align_md)}|\n"
        for row in rows:
            row_text = []
            for cell in row:
                if isinstance(cell, tuple):
                    display, sort_value = cell
                    escaped_sort = html_mod.escape(str(sort_value), quote=True)
                    row_text.append(
                        f'<span data-sort-value="{escaped_sort}">{display}</span>'
                    )
                else:
                    row_text.append(str(cell))
            output += f"|{'|'.join(row_text)}|\n"

        return output

    def format_chart(self, item, i) -> str:
        """
        Format chart data into markdown. For charts, the parsed data is usually rendered as a javascript block.
        The chart rendering is handled by the frontend `snippets` in the `templates` folder.

        Args:
            data (dict): The data for the chart.
            i (int): The index of the chart in the output list.
        Returns:
            str: Parsed chart as a markdown string.
        """
        uniq_name: str = f"{uuid4().hex}"
        output = ""
        output += f'<div id="{uniq_name}"></div>'
        output += "<script type='text/javascript'>\n"
        output += f"// {self.__class__.__name__}\n"
        output += "(function() {\n"
        output += f"const container = document.getElementById('{uniq_name}');\n"
        output += f"let data = {to_json(item.get('data'))};\n"
        file_name = f"{self.__class__.__name__}_{i}.js"
        file_path = os.path.join(self.TEMPLATE_FOLDER, file_name)
        file_path = get_script_path(file_path)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as js_file:
                for line in js_file:
                    output += line.replace("{name}", self.__class__.__name__)
        output += "})()\n"
        output += "</script>\n"
        return output

    def format_code(self, item, i) -> str:
        """
        Format code block into markdown.

        Args:
            item (dict): The code item containing
                caption (str, optional): The code block caption.
                language (str): The programming language for syntax highlighting.
                code (str): The code content.
            i (int): The index of the code block in the output list.
        Returns:
            str: Parsed code block as a markdown string.
        """
        caption = item.get("caption", None)
        language = item.get("language", "")
        code = item.get("code", "")
        output = f"#### {caption}\n\n" if caption else ""
        output += f"```{language}\n{code}\n```\n"
        return output

    def markdown(self, data: object, **kwargs) -> str:
        """
        Parse the data and return as markdown.
        Args:
            data (object): The data to be parsed.
        Returns:
            str: The parsed data in markdown format.
        """
        output_list: list = self.parse(data, **kwargs)
        output = ""
        for i, item in enumerate(output_list):
            if item["type"] == "table":
                output += self.format_table(item, i)
            elif item["type"] == "chart":
                output += self.format_chart(item, i)
            elif item["type"] == "code":
                output += self.format_code(item, i)
            output += "\n\n"
        return output
