"""Base parser for healthcheck results."""

from abc import ABC, abstractmethod
import os
from x_ray.log_analysis.shared import to_json
from x_ray.utils import get_script_path
from x_ray.healthcheck.check_items.base_item import TABLE_ALIGNMENT


class BaseParser(ABC):
    @abstractmethod
    def parse(self, data: object, **kwargs) -> list:
        """
        Parse the given data into tables and charts.
        Args:
            data (object): The data to be parsed.
        Returns:
            list (dict): The parsed list. Each element can be either
                        {"type": "table", "caption": str (optional), "headers": list, "rows": list} or
                        {"type": "chart", "chart_type": str, "data": dict}
        """
        raise NotImplementedError("Subclasses must implement the parse method")

    def format_table(self, item, index, caller=None) -> str:
        """
        Parse a table represented by header and rows into markdown.

        Args:
            item (dict): The table item containing
                caption (str, optional): The table caption.
                headers (list): List of column names. Accepts strings or dicts {"text": str, "align": "center" | "left" | "right"}.
                rows (list): List of rows, where each row is a list of values.
        Returns:
            str: Parsed table as a markdown string.
        """
        if item is None or item.get("type", None) != "table":
            raise ValueError("Invalid table item")
        headers = item.get("headers", [])
        rows = item.get("rows", [])
        caption = item.get("caption", None)
        output = f"#### {caption}\n\n" if caption else ""
        if rows is None or len(rows) == 0:
            output += "_No data available._\n"
            return output
        header_text = [h["text"] if isinstance(h, dict) else h for h in headers]
        alignments = [h.get("align", "center") if isinstance(h, dict) else "center" for h in headers]
        align_md = [TABLE_ALIGNMENT[a] for a in alignments]
        output += f"|{'|'.join(header_text)}|\n"
        output += f"|{'|'.join(align_md)}|\n"
        for row in rows:
            row_text = [str(cell) for cell in row]
            output += f"|{'|'.join(row_text)}|\n"

        return output

    def format_chart(self, item, index, caller=None) -> str:
        """
        Format chart data into markdown. For charts, the parsed data is usually rendered as a javascript block.
        The chart rendering is handled by the frontend `snippets` in the `templates` folder.

        Args:
            data (dict): The data for the chart.
        Returns:
            str: Parsed chart as a markdown string.
        """
        if item is None or item.get("type", None) != "chart":
            raise ValueError("Invalid chart item")
        output = ""
        output += f'<div id="container_{caller}_{index}"></div>'
        output += "<script type='text/javascript'>\n"
        output += "(function() {\n"
        output += f"const container = document.getElementById('container_{caller}_{index}');\n"
        output += f"let data = {to_json(item.get('data'))};\n"
        file_name = f"{caller}_{index}.js"
        file_path = os.path.join("templates", "healthcheck", "snippets", file_name)
        file_path = get_script_path(file_path)
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as js_file:
                for line in js_file:
                    output += line.replace("{name}", self.__class__.__name__)
        output += "})()\n"
        output += "</script>\n"
        return output

    def markdown(self, data: object, **kwargs) -> str:
        """
        Parse the data and return as markdown.
        Args:
            data (object): The data to be parsed.
        Returns:
            str: The parsed data in markdown format.
        """
        caller = kwargs.get("caller", None)
        output_list = self.parse(data, **kwargs)
        output = ""
        for i, item in enumerate(output_list):
            if item["type"] == "table":
                output += self.format_table(item, i, caller)
            elif item["type"] == "chart":
                output += self.format_chart(item, i, caller)
            output += "\n\n"
        return output
