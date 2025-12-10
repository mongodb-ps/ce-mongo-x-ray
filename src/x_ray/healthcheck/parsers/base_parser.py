"""Base parser for healthcheck results."""

from abc import ABC, abstractmethod
from x_ray.healthcheck.check_items.base_item import TABLE_ALIGNMENT


class BaseParser(ABC):
    @abstractmethod
    def parse(self, data: object, **kwargs) -> str:
        raise NotImplementedError("Subclasses must implement the parse method")

    def parse_table(self, headers: list, rows: list, **kwargs) -> str:
        """
        Parse a table represented by header and rows into a list of dictionaries.

        Args:
            headers (list): List of column names. Accepts strings or dicts {"text": str, "align": "center" | "left" | "right"}.
            rows (list): List of rows, where each row is a list of values.
        Returns:
            str: Parsed table as a markdown string.
        """
        caption = kwargs.get("caption", None)
        output = f"#### {caption}\n\n" if caption else ""
        header_text = [h["text"] if isinstance(h, dict) else h for h in headers]
        alignments = [h.get("align", "center") if isinstance(h, dict) else "center" for h in headers]
        align_md = [TABLE_ALIGNMENT[a] for a in alignments]
        output += f"|{'|'.join(header_text)}|\n"
        output += f"|{'|'.join(align_md)}|\n"
        for row in rows:
            row_text = [str(cell) for cell in row]
            output += f"|{'|'.join(row_text)}|\n"

        return output
