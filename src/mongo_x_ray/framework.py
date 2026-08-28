"""
Copyright (c) 2026 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.

Shared lifecycle for the analysis frameworks (ftdc, gmd, healthcheck, log).
Each module's ``Framework`` subclasses :class:`BaseFramework`, keeps its own
``run_*`` command (which populates ``self._items``), implements
:meth:`_render_markdown` for its report body, and declares a
``template_module`` name for its HTML template.
"""

import logging
import re
import webbrowser
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path
from typing import TextIO

import markdown

from mongo_x_ray.table_width_extension import TableWidthExtension
from mongo_x_ray.utils import env, green, html_to_pdf, inject_assets


class BaseFramework(ABC):
    """Coordinate the lifecycle of a set of analysis items.

    Subclasses provide the module-specific parts:
    - ``template_module``: the template directory name (e.g. ``"ftdc"``).
    - ``template_package``: the package whose ``templates/`` directory holds
      this module's templates (defaults to the core ``mongo_x_ray`` package).
    - a ``run_*`` method that loads and runs the configured items.
    - :meth:`_render_markdown`: writes the markdown report body.
    """

    template_module: str = ""
    template_package: str = "mongo_x_ray"

    def __init__(self, config: dict):
        self._config: dict = config
        # Log under the subclass's module so per-module loggers keep working.
        self._logger: logging.Logger = logging.getLogger(type(self).__module__)
        self._items: list = []
        self._set_name: str = "default"
        now = str(datetime.now(tz=timezone.utc))
        self._timestamp: str = re.sub(r"[:\- ]", "", now.split(".", maxsplit=1)[0])

    def _get_output_folder(self, output_folder: str) -> Path:
        """Return the batch output folder, creating it if necessary."""
        if env == "development":
            batch_folder = Path(output_folder)
        else:
            batch_folder = Path(output_folder) / f"{self._set_name}-{self._timestamp}"
        batch_folder.mkdir(parents=True, exist_ok=True)
        return batch_folder

    @abstractmethod
    def _render_markdown(self, output: TextIO) -> None:
        """Write the module-specific markdown report body to *output*."""

    def output_results(self, output_folder: str = "output/", fmt: str = "html", open_browser: bool = True) -> None:
        """Write the markdown report and (optionally) render it to HTML/PDF."""
        batch_folder = self._get_output_folder(output_folder)
        markdown_file = batch_folder / "report.md"
        self._logger.info("Report saved to: %s", green(str(batch_folder)))

        with markdown_file.open("w", encoding="utf-8") as output:
            self._render_markdown(output)

        html_file = batch_folder / "report.html"
        if fmt in {"html", "pdf"}:
            template_root = Path(str(files(self.template_package) / "templates"))
            default_template = f"{self.template_module}/full.html"
            template_file = template_root / self._config.get("template", default_template)
            html_content = markdown.markdown(
                markdown_file.read_text(encoding="utf-8"),
                extensions=[TableWidthExtension(), "fenced_code", "toc", "md_in_html"],
            )
            template_content = inject_assets(
                template_file.read_text(encoding="utf-8"),
                self.template_module,
                template_root=template_root,
            )
            html_file.write_text(template_content.replace("{{ content }}", html_content), encoding="utf-8")

        if fmt in {"html", "pdf"} and open_browser:
            webbrowser.open(f"file://{html_file.resolve()}")

        if fmt == "pdf":
            pdf_file = batch_folder / "report.pdf"
            self._logger.info("Converting HTML report to: %s", green(str(pdf_file)))
            html_to_pdf(html_file, pdf_file)
