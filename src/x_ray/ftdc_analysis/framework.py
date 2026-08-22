"""Framework for MongoDB FTDC analysis."""

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TextIO

from bson import decode_file_iter
from bson.errors import InvalidBSON

from x_ray.framework import BaseFramework
from x_ray.utils import bold, cyan, green, load_classes, yellow

FTDC_CLASSES = load_classes("x_ray.ftdc_analysis.ftdc_items")


class Framework(BaseFramework):
    """Load configured FTDC analysis items and coordinate their lifecycle."""

    template_module = "ftdc"

    _FILE_TIME = re.compile(r"^metrics\.(?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}[-:]\d{2}[-:]\d{2}Z)(?:-\d+)?$")

    def __init__(
        self,
        input_path: str,
        config: dict,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        image_format: str = "png",
    ):
        super().__init__(config)
        self._input_path = Path(input_path)
        self._start_time = start_time
        self._end_time = end_time
        self._image_format = image_format

    @property
    def hostname(self) -> Optional[str]:
        """The hostname extracted from FTDC files, or None."""
        for item in self._items:
            hostname = getattr(item, "_hostname", None)
            if hostname:
                return hostname
        return None

    def _input_files(self) -> list[Path]:
        files = sorted(
            (path for path in self._input_path.glob("metrics.*")
             if path.is_file()
             and not path.name.endswith(".tmp")
             and not path.name.endswith(".interim")),
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

    def run_ftdc_analysis(self, ftdcset_name: str, *_args, **kwargs) -> None:
        """Run a configured set of FTDC analysis items."""
        ftdcsets = self._config.get("ftdcsets", {})
        if ftdcset_name not in ftdcsets:
            self._logger.warning(yellow(f"FTDC checkset '{ftdcset_name}' not found. Using default."))
            ftdcset_name = "default"
        if ftdcset_name not in ftdcsets:
            raise ValueError("Default FTDC checkset is missing from configuration.")

        self._set_name = ftdcset_name
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

    def _render_markdown(self, output: TextIO) -> None:
        """Write the FTDC analysis report body."""
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
