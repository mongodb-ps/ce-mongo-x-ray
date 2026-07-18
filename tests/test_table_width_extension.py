"""Tests for the table_width markdown extension."""

import markdown

from x_ray.table_width_extension import TableWidthExtension


def render(text: str) -> str:
    return markdown.markdown(
        text,
        extensions=[TableWidthExtension(), "fenced_code"],
    )


def test_px_width():
    md = "| Name{120} | Status{80} |\n|---|---|\n| foo | active |"
    html = render(md)
    assert "<colgroup>" in html
    assert '<col style="width:120px" width="120" />' in html
    assert '<col style="width:80px" width="80" />' in html
    assert "Name{120}" not in html
    assert "<th>Name</th>" in html


def test_percent_width():
    md = "| Name{60%} | Desc{40%} |\n|---|---|\n| a | b |"
    html = render(md)
    assert '<col style="width:60%" width="60%" />' in html
    assert '<col style="width:40%" width="40%" />' in html


def test_auto_width():
    md = "| Name{120} | Desc{*} | Status{80} |\n|---|---|---|\n| a | b | c |"
    html = render(md)
    assert '<col style="width:120px" width="120" />' in html
    assert "<col />" in html
    assert '<col style="width:80px" width="80" />' in html


def test_no_width_spec_no_colgroup():
    md = "| Name | Status |\n|---|---|\n| foo | active |"
    html = render(md)
    assert "<colgroup>" not in html


def test_partial_width():
    """Columns without {width} get auto (no style on the <col>)."""
    md = "| Name{120} | Status |\n|---|---|\n| foo | active |"
    html = render(md)
    assert "<colgroup>" in html
    assert '<col style="width:120px" width="120" />' in html
    assert html.count("<col />") == 1


def test_header_text_preserved():
    md = "| Collection Name{120} | Description{*} |\n|---|---|\n| test.foo | bar |"
    html = render(md)
    assert "<th>Collection Name</th>" in html
    assert "<th>Description</th>" in html


def test_table_without_borders():
    md = "Name{120} | Status\n--- | ---\nfoo | active"
    html = render(md)
    assert '<col style="width:120px"' in html


def test_data_rows_unchanged():
    md = "| Name{120} | Status |\n|---|---|\n| foo | active |\n| bar | inactive |"
    html = render(md)
    assert html.count("<td>") == 4
    assert "<td>foo</td>" in html
    assert "<td>active</td>" in html


def test_decimal_percent_width():
    md = "| A{33.5%} | B{66.5%} |\n|---|---|\n| 1 | 2 |"
    html = render(md)
    assert '<col style="width:33.5%" width="33.5%" />' in html
    assert '<col style="width:66.5%" width="66.5%" />' in html


def test_explicit_px_unit():
    md = "| A{120px} | B{80px} |\n|---|---|\n| 1 | 2 |"
    html = render(md)
    assert '<col style="width:120px" width="120" />' in html
    assert '<col style="width:80px" width="80" />' in html


def test_em_unit():
    md = "| A{10em} | B{15rem} |\n|---|---|\n| 1 | 2 |"
    html = render(md)
    assert '<col style="width:10em" />' in html
    assert '<col style="width:15rem" />' in html
    # Non-px/%-units don't get a `width` attr on <col>.
    assert 'width="10em"' not in html


# --- Table-width computation ---


def test_table_width_all_px():
    md = "| A{120} | B{80} |\n|---|---|\n| 1 | 2 |"
    html = render(md)
    assert 'style="width:200px"' in html  # 120 + 80 = 200


def test_table_width_all_pct():
    md = "| A{30%} | B{20%} |\n|---|---|\n| 1 | 2 |"
    html = render(md)
    assert 'style="width:50.0%"' in html  # 30 + 20 = 50


def test_table_width_star():
    md = "| A{120} | B{*} |\n|---|---|\n| 1 | 2 |"
    html = render(md)
    assert 'style="width:100%"' in html


def test_table_width_mixed_skip():
    """Mixed px and % → no table-level width."""
    md = "| A{120} | B{50%} |\n|---|---|\n| 1 | 2 |"
    html = render(md)
    assert "<colgroup>" in html
    assert 'style="width:' not in html.split("<colgroup>")[0]


def test_table_width_partial_skip():
    """A column without a {width} spec → no table width computed."""
    md = "| A{120} | B |\n|---|---|\n| 1 | 2 |"
    html = render(md)
    assert "<colgroup>" in html
    assert 'style="width:' not in html.split("<colgroup>")[0]
