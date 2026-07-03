"""Framework for MongoDB FTDC analysis."""

from datetime import datetime, timezone
import logging
from pathlib import Path
import re
from typing import Optional

import markdown
from bson import decode_file_iter
from bson.errors import InvalidBSON

from x_ray.ftdc_analysis.ftdc_items.base_item import BaseItem
from x_ray.utils import bold, cyan, env, get_script_path, green, load_classes, yellow

FTDC_CLASSES = load_classes("x_ray.ftdc_analysis.ftdc_items")


class Framework:
    """Load configured FTDC analysis items and coordinate their lifecycle."""

    _ftdcset_name = "default"

    _FILE_TIME = re.compile(r"^metrics\.(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}[-:]\d{2}[-:]\d{2}Z)(?:-\d+)?$")

    def __init__(
        self,
        input_path: str,
        config: dict,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        image_format: str = "png",
    ):
        self._input_path = Path(input_path)
        self._config = config
        self._start_time = start_time
        self._end_time = end_time
        self._image_format = image_format
        self._logger = logging.getLogger(__name__)
        self._items: list[BaseItem] = []
        now = str(datetime.now(tz=timezone.utc))
        self._timestamp = re.sub(r"[:\- ]", "", now.split(".", maxsplit=1)[0])

    def _get_output_folder(self, output_folder: str) -> Path:
        if env == "development":
            batch_folder = Path(output_folder)
        else:
            batch_folder = Path(output_folder) / f"{self._ftdcset_name}-{self._timestamp}"
        batch_folder.mkdir(parents=True, exist_ok=True)
        return batch_folder

    def _input_files(self) -> list[Path]:
        files = sorted(
            (path for path in self._input_path.glob("metrics.*") if path.is_file() and not path.name.endswith(".tmp")),
            key=lambda path: (self._file_end_time(path) or datetime.max.replace(tzinfo=timezone.utc), path.name),
        )
        if self._start_time is None and self._end_time is None:
            return files

        if self._filenames_are_start_times(files):
            return self._select_start_named_files(files)

        selected: list[Path] = []
        for path in files:
            file_end = self._file_end_time(path)
            if file_end is None:
                selected.append(path)
                continue
            if self._start_time is not None and file_end < self._start_time:
                continue
            selected.append(path)
            # Filename timestamps are final data points. Once this file covers
            # the requested end, later files cannot contribute to the range.
            if self._end_time is not None and file_end >= self._end_time:
                break
        return selected

    def _select_start_named_files(self, files: list[Path]) -> list[Path]:
        """Select files from archives whose names contain their first point."""
        selected: list[Path] = []
        file_times = [self._file_end_time(path) for path in files]
        for index, path in enumerate(files):
            file_start = file_times[index]
            next_start = file_times[index + 1] if index + 1 < len(files) else None
            if self._end_time is not None and file_start is not None and file_start > self._end_time:
                break
            if self._start_time is not None and next_start is not None and next_start <= self._start_time:
                continue
            selected.append(path)
        return selected

    def _filenames_are_start_times(self, files: list[Path]) -> bool:
        """Detect the alternate naming used by the bundled MongoDB files."""
        for path in files:
            filename_time = self._file_end_time(path)
            if filename_time is None:
                continue
            try:
                with path.open("rb") as stream:
                    first_metric = next(document for document in decode_file_iter(stream) if document.get("type") == 1)
                first_time = first_metric.get("_id")
                if not isinstance(first_time, datetime):
                    return False
                if first_time.tzinfo is None:
                    first_time = first_time.replace(tzinfo=timezone.utc)
                return abs((first_time - filename_time).total_seconds()) <= 60
            except (InvalidBSON, OSError, StopIteration):
                return False
        return False

    @classmethod
    def _file_end_time(cls, path: Path) -> Optional[datetime]:
        match = cls._FILE_TIME.match(path.name)
        if not match:
            return None
        value = match.group("timestamp")
        date_part, time_part = value[:-1].split("T", maxsplit=1)
        return datetime.fromisoformat(f"{date_part}T{time_part.replace('-', ':')}+00:00").astimezone(timezone.utc)

    def run_ftdc_analysis(self, ftdcset_name: str, *args, **kwargs) -> None:
        """Run a configured set of FTDC analysis items."""
        ftdcsets = self._config.get("ftdcsets", {})
        if ftdcset_name not in ftdcsets:
            self._logger.warning(yellow(f"FTDC checkset '{ftdcset_name}' not found. Using default."))
            ftdcset_name = "default"
        if ftdcset_name not in ftdcsets:
            raise ValueError("Default FTDC checkset is missing from configuration.")

        self._ftdcset_name = ftdcset_name
        batch_folder = self._get_output_folder(kwargs.get("output_folder", "output/"))
        self._logger.info("Running FTDC checkset: %s", bold(cyan(ftdcset_name)))

        input_files = self._input_files()
        self._logger.info("Ingesting %s FTDC file(s).", green(str(len(input_files))))

        self._items = []
        for item_name in ftdcsets[ftdcset_name].get("items", []):
            item_cls = FTDC_CLASSES.get(item_name)
            if not item_cls:
                self._logger.warning(yellow(f"FTDC item '{item_name}' not found. Skipping."))
                continue
            item_config = self._config.get("item_config", {}).get(item_name, {})
            self._items.append(
                item_cls(
                    str(batch_folder),
                    item_config,
                    start_time=self._start_time,
                    end_time=self._end_time,
                    total_ingest_files=len(input_files),
                    image_format=self._image_format,
                )
            )
            self._logger.info("FTDC analysis item loaded: %s", bold(cyan(item_name)))

        for file_path in input_files:
            for item in self._items:
                try:
                    item.analyze(file_path)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    self._logger.warning(yellow(f"FTDC item '{item.name}' failed for '{file_path}': {exc}"))

        for item in self._items:
            try:
                item.finalize_analysis()
            except Exception as exc:  # pylint: disable=broad-exception-caught
                self._logger.warning(yellow(f"FTDC item '{item.name}' finalization failed: {exc}"))

    def output_results(self, output_folder: str = "output/", fmt: str = "html") -> None:
        """Write the FTDC analysis report."""
        batch_folder = self._get_output_folder(output_folder)
        markdown_file = batch_folder / "report.md"
        self._logger.info("Saving results to: %s", green(str(markdown_file)))

        with markdown_file.open("w", encoding="utf-8") as output:
            output.write("# FTDC Analysis Report\n\n")
            output.write(f"Generated at: `{datetime.now(tz=timezone.utc)} UTC`\n\n")
            output.write(f"Input path: `{self._input_path}`\n\n")
            if not self._items:
                output.write("_No FTDC analysis items are configured._\n")
            for section_number, item in enumerate(self._items, start=1):
                try:
                    item.review_results_markdown(output, section_number)
                except Exception as exc:  # pylint: disable=broad-exception-caught
                    self._logger.warning(yellow(f"Failed to render FTDC item '{item.name}': {exc}"))

        html_file = batch_folder / "report.html"
        if fmt in {"html", "pdf"}:
            template_file = get_script_path(f"templates/{self._config.get('template', 'ftdc/full.html')}")
            html_content = markdown.markdown(
                markdown_file.read_text(encoding="utf-8"),
                extensions=["tables", "fenced_code", "toc", "md_in_html"],
            )
            template_content = Path(template_file).read_text(encoding="utf-8")
            html_file.write_text(template_content.replace("{{ content }}", html_content), encoding="utf-8")

        if fmt == "pdf":
            # Import only when requested so Markdown and HTML output do not load
            # WeasyPrint or its native rendering dependencies.
            from weasyprint import HTML  # pylint: disable=import-outside-toplevel

            logging.getLogger("weasyprint").setLevel(logging.ERROR)
            logging.getLogger("fontTools.subset").setLevel(logging.WARNING)
            pdf_file = batch_folder / "report.pdf"
            self._logger.info("Converting HTML report to: %s", green(str(pdf_file)))
            HTML(filename=str(html_file), base_url=str(batch_folder)).write_pdf(str(pdf_file))
