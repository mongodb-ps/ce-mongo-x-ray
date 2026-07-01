"""Metadata inspection item for FTDC analysis reports."""

import json
from pathlib import Path
from typing import Any, Optional

from pyftdc import FTDCError, FTDCReader

from x_ray.ftdc_analysis.ftdc_items.base_item import BaseItem

_METADATA_TABS: list[tuple[str, str, str]] = [
    ("mongodb-config", "MongoDB Configuration", "getCmdLineOpts.parsed"),
    ("startup-args", "Start-up Arguments", "getCmdLineOpts.argv"),
    ("build-info", "Build Information", "buildInfo"),
    ("host-info", "Host Information", "hostInfo"),
    ("ulimits", "Process Resource Limits", "ulimits"),
    ("sys-open-files", "System Max Open Files", "sysMaxOpenFiles"),
]

_STYLE = """<style>
.metadata-tabs{border:1px solid var(--borderColor-default,#d0d7de);border-radius:6px;overflow:hidden;margin:16px 0}
.metadata-tab-bar{display:flex;flex-wrap:wrap;background:var(--bgColor-muted,#f6f8fa);border-bottom:1px solid var(--borderColor-default,#d0d7de)}
.metadata-tab-btn{padding:8px 16px;font-size:13px;cursor:pointer;border:none;background:none;color:var(--fgColor-muted,#656d76);border-bottom:2px solid transparent;transition:color .15s,border-color .15s}
.metadata-tab-btn:hover{color:var(--fgColor-default,#1f2328)}
.metadata-tab-btn.active{color:var(--fgColor-accent,#0969da);border-bottom-color:var(--fgColor-accent,#0969da);font-weight:600}
.metadata-tab-pane{display:none;padding:16px}
.metadata-tab-pane.active{display:block}
.metadata-tab-pane pre{margin:0}
</style>"""

_SCRIPT = """<script>
(function(){var t=document.currentScript.previousElementSibling.querySelectorAll(".metadata-tab-btn"),e=document.currentScript.previousElementSibling.querySelectorAll(".metadata-tab-pane");t.forEach(function(n){n.addEventListener("click",function(){var i=this.dataset.tab;t.forEach(function(t){t.classList.toggle("active",t===n)}),e.forEach(function(t){t.classList.toggle("active",t.id===i)})})})})();
</script>"""


def _resolve_path(metadata: dict[str, Any], dotted: str) -> Any:
    for key in dotted.split("."):
        if not isinstance(metadata, dict) or key not in metadata:
            return None
        metadata = metadata[key]
    return metadata


class MetadataReviewItem(BaseItem):
    """Display all FTDC metadata in tabbed code blocks."""

    def __init__(self, output_folder: str, config: dict, **kwargs) -> None:
        super().__init__(output_folder, config, **kwargs)
        self._raw_metadata: Optional[dict[str, Any]] = None

    def analyze(self, file_path: Path) -> None:
        if self._raw_metadata is not None:
            return
        try:
            reader = FTDCReader(file_path)
            self._raw_metadata = reader.get_metadata()
        except FTDCError:
            self._logger.debug("Metadata not found in FTDC file: %s", file_path)

    def finalize_analysis(self) -> None:
        pass

    def review_results_markdown(self, output, section_number: int = 1) -> None:
        output.write(f"## {section_number} Metadata Review\n\n")
        if self._raw_metadata is None:
            output.write("_No metadata available._\n")
            return

        tab_id = "metadata-tabs"
        output.write(_STYLE)
        output.write(f'<div class="metadata-tabs" id="{tab_id}">\n')
        output.write('<div class="metadata-tab-bar">\n')
        for idx, (tab_key, label, _dotted_path) in enumerate(_METADATA_TABS):
            active_class = " active" if idx == 0 else ""
            output.write(
                f'<button class="metadata-tab-btn{active_class}"'
                f' data-tab="{tab_id}-{tab_key}">{label}</button>\n'
            )
        output.write("</div>\n")

        for idx, (tab_key, _label, dotted_path) in enumerate(_METADATA_TABS):
            active_class = " active" if idx == 0 else ""
            value = _resolve_path(self._raw_metadata, dotted_path)
            if value is None:
                content = "_Not available._"
            else:
                escaped = json.dumps(value, indent=2, sort_keys=True, default=str)
                content = f"<pre><code class=\"language-json\">{escaped}</code></pre>"
            output.write(f'<div class="metadata-tab-pane{active_class}" id="{tab_id}-{tab_key}">\n')
            output.write(f"{content}\n")
            output.write("</div>\n")

        output.write("</div>\n")
        output.write(_SCRIPT)
        output.write("\n\n")
