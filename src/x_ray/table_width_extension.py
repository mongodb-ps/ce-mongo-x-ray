"""Markdown extension adding column-width support to pipe tables.

Drop-in replacement for the built-in ``tables`` extension. Register instead of
``tables`` — it recognises a trailing ``{width}`` spec on header cells:

    | Name{120}   | Description{*} | Status{50%} |
    |-------------|----------------|-------------|
    | foo         | bar            | active      |

Width specs:
    {N}   -> N pixels                (e.g. {120} -> 120px)
    {Npx} -> explicit pixels         (e.g. {120px} -> 120px)
    {N%}  -> percentage              (e.g. {50%})
    {Nem} -> any valid CSS unit      (e.g. {10em} -> 10em)
    {*}   -> auto                    (no constraint on the column)

The spec is stripped from the rendered header text and a ``<colgroup>`` of
``<col>`` elements is inserted as the first child of the ``<table>``.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as etree

from markdown.extensions.tables import TableExtension, TableProcessor

PIPE_LEFT = 1
PIPE_RIGHT = 2

# Matches a {width} spec at the end of a header cell (before the next pipe or EOL).
RE_CELL_WIDTH = re.compile(r"\{(\*|\d+(?:\.\d+)?[a-z%]*)\}\s*$")
# Splits a header row on unescaped pipes.
RE_SPLIT_PIPE = re.compile(r"(?<!\\)\|")

_HAS_CSS_UNIT = re.compile(r"[a-z]")
_RE_STRIP_UNIT = re.compile(r"[a-z%]+$")


def _spec_to_width(spec: str) -> str:
    """Convert a width spec to a CSS width value (empty string for auto)."""
    if spec == "*":
        return ""
    if spec.endswith("%") or _HAS_CSS_UNIT.search(spec):
        return spec
    return f"{spec}px"


def _compute_table_style(specs: list[str]) -> str:
    """Compute a ``style`` attribute value for the ``<table>`` from raw specs.

    Returns an empty string when the table width should not be set.
    """
    if not specs or "" in specs:
        return ""
    if "*" in specs:
        return "width:100%"

    px_sum = 0.0
    pct_sum = 0.0
    has_px = False
    has_pct = False

    for s in specs:
        if s.endswith("%"):
            pct_sum += float(s[:-1])
            has_pct = True
        else:
            # bare number or explicit px/em/... — treat numeric part as px
            px_sum += float(_RE_STRIP_UNIT.sub("", s))
            has_px = True

    if has_px and has_pct:
        return ""  # mixed units — skip
    if has_px:
        val = round(px_sum)
        return f"width:{val}px"
    if has_pct:
        val = round(pct_sum, 1)
        return f"width:{val}%"
    return ""


def _split_header(header: str, border: int) -> list[str]:
    """Split a header row into raw cells (simplified — no code-span handling).

    For header rows with width specs, code spans containing pipes are not
    a practical concern.
    """
    row = header.strip()
    if border & PIPE_LEFT and row.startswith("|"):
        row = row[1:]
    if border & PIPE_RIGHT and row.endswith("|"):
        row = row[:-1]
    return RE_SPLIT_PIPE.split(row)


class WidthTableProcessor(TableProcessor):
    """Table processor that parses ``{width}`` specs from header cells."""

    def run(self, parent: etree.Element, blocks: list[str]) -> None:
        block = blocks[0].split("\n")
        header = block[0]

        cells = _split_header(header, self.border)
        widths: list[str] = []
        specs: list[str] = []  # raw specs for table-width computation
        has_width = False
        cleaned: list[str] = []
        for cell in cells:
            text = cell.strip(" ")
            m = RE_CELL_WIDTH.search(text)
            if m:
                raw = m.group(1)
                specs.append(raw)
                w = _spec_to_width(raw)
                widths.append(w)
                if w:
                    has_width = True
                text = RE_CELL_WIDTH.sub("", text).rstrip()
            else:
                specs.append("")
                widths.append("")
            cleaned.append(text)

        if has_width:
            # Rebuild the header without specs so rendered <th> text is clean.
            new_header = " | ".join(cleaned)
            if self.border & PIPE_LEFT:
                new_header = "| " + new_header
            if self.border & PIPE_RIGHT:
                new_header = new_header + " |"
            block[0] = new_header
            blocks[0] = "\n".join(block)

        super().run(parent, blocks)

        table = parent[-1] if len(parent) else None
        if table is not None and table.tag == "table" and has_width:
            table_style = _compute_table_style(specs)
            if table_style:
                existing = table.get("style", "")
                table.set("style", f"{existing};{table_style}".strip(";"))
            colgroup = etree.Element("colgroup")
            for w in widths:
                col = etree.SubElement(colgroup, "col")
                if w:
                    col.set("style", f"width:{w}")
                    if w.endswith("%"):
                        col.set("width", w)
                    elif w.endswith("px"):
                        col.set("width", w[:-2])
            table.insert(0, colgroup)


class TableWidthExtension(TableExtension):
    """Drop-in replacement for the ``tables`` extension with ``{width}`` support."""

    def extendMarkdown(self, md) -> None:
        if "|" not in md.ESCAPED_CHARS:
            md.ESCAPED_CHARS.append("|")
        processor = WidthTableProcessor(md.parser, self.getConfigs())
        md.parser.blockprocessors.register(processor, "table", 75)


def makeExtension(**kwargs):
    return TableWidthExtension(**kwargs)
