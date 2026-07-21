"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from datetime import datetime, timezone
import random
import re
from pathlib import Path
import logging
from typing import Optional
import markdown
from bson import json_util
from x_ray.table_width_extension import TableWidthExtension
from x_ray.log_analysis.log_items.base_item import BaseItem
from x_ray.healthcheck.shared import to_json
from x_ray.utils import load_classes, bold, green, yellow, cyan, get_script_path, html_to_pdf, inject_assets, env

logger = logging.getLogger(__name__)
LOG_CLASSES = load_classes("x_ray.log_analysis.log_items")
SKIP_LINE_MSG = "HEADER INCLUDED, NOW SKIPPING 64728 LINES ACCORDING TO REQUESTED SIZE LIMIT"


class Framework:
    _logset_name = ""

    def __init__(
        self,
        file_path: str,
        config: dict,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        self._file_path = file_path
        self._config = config
        self._start_time = start_time
        self._end_time = end_time
        self._logger = logging.getLogger(__name__)
        self._items: list[BaseItem] = []
        now = str(datetime.now(tz=timezone.utc))
        self._timestamp = re.sub(r"[:\- ]", "", now.split(".", maxsplit=1)[0])
        self._logger.debug(to_json(self._config))
        self._log_start: Optional[datetime] = None
        self._log_end: Optional[datetime] = None
        if env == "development":
            self._logger.info(yellow("Running in development mode."))

    def _get_output_folder(self, output_folder: str):
        if env == "development":
            batch_folder = output_folder
        else:
            batch_folder = f"{output_folder}{self._logset_name}-{self._timestamp}/"
        Path(batch_folder).mkdir(parents=True, exist_ok=True)
        return batch_folder

    def _log_files(self) -> list[Path]:
        """Return a sorted list of log files to process."""
        path = Path(self._file_path)
        if path.is_file():
            return [path]
        # Match mongod.log, mongod.log.2026-06-10T01-58-56, etc.
        files = sorted(path.glob("*.log*"))
        if not files:
            files = sorted(path.glob("*"))
        return files

    @staticmethod
    def _file_time_range(file_path: Path) -> tuple:
        """Read the first and last JSON log line to get the file's time range."""
        first_ts = None
        last_ts = None
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                first_line = f.readline()
                if first_line:
                    try:
                        first_ts = json_util.loads(first_line).get("t")
                    except Exception:
                        pass
                # Scan backwards from end for the last line
                f.seek(0, 2)
                pos = f.tell()
                if pos > 0:
                    pos -= 1
                    while pos > 0:
                        f.seek(pos)
                        if f.read(1) == "\n":
                            break
                        pos -= 1
                    last_line = f.readline()
                    if last_line:
                        try:
                            last_ts = json_util.loads(last_line).get("t")
                        except Exception:
                            pass
        except Exception:
            pass
        return first_ts, last_ts

    def _file_overlaps_range(self, file_path: Path) -> bool:
        """Return False if the file's time range is entirely outside the requested range."""
        if self._start_time is None and self._end_time is None:
            return True
        first_ts, last_ts = self._file_time_range(file_path)
        if first_ts is None or last_ts is None:
            return True  # can't determine, process anyway
        if self._end_time is not None and first_ts > self._end_time:
            return False
        if self._start_time is not None and last_ts < self._start_time:
            return False
        return True

    def run_logs_analysis(self, logset_name: str, *args, **kwargs):
        self._logset_name = logset_name
        # Create output folder if it doesn't exist
        output_folder = kwargs.get("output_folder", "output/")
        batch_folder = self._get_output_folder(output_folder)
        # Dynamically load the log checkset based on the name
        logsets = self._config.get("logsets", {})
        if not logset_name in logsets:
            self._logger.warning(
                yellow(f"Log checkset '{logset_name}' not found in configuration. Using default logset.")
            )
            logset_name = "default"
        ls = logsets[logset_name]
        self._logger.info("Running log checkset: %s", bold(cyan(logset_name)))

        self._items = []
        for item_name in ls.get("items", []):
            item_cls = LOG_CLASSES.get(item_name)
            if not item_cls:
                self._logger.warning(yellow(f"Log item '{item_name}' not found. Skipping."))
                continue
            item_config = self._config.get("item_config", {}).get(item_name, {})
            item = item_cls(batch_folder, item_config)
            self._items.append(item)
            self._logger.info("Log analyze item loaded: %s", bold(cyan(item_name)))

        rate = self._config.get("sample_rate", 1.0)
        log_files = self._log_files()
        log_line: dict = {}
        global_counter: int = 0

        for lf in log_files:
            if not self._file_overlaps_range(lf):
                self._logger.info(
                    "Skipping %s (outside time range %s – %s)",
                    lf.name,
                    self._start_time.isoformat() if self._start_time else "…",
                    self._end_time.isoformat() if self._end_time else "…",
                )
                continue
            self._logger.info("Processing %s", green(str(lf)))

            with open(lf, "r", encoding="utf-8", errors="ignore") as f:
                counter: int = 0
                for line in f:
                    counter += 1
                    global_counter += 1
                    if global_counter % 10000 == 0:
                        self._logger.info("%s lines ingested...", green(str(global_counter)))
                    if random.random() > rate:
                        continue
                    try:
                        if counter == 101 and line.startswith(SKIP_LINE_MSG):
                            self._logger.debug(
                                "Some lines are skipped due to the size limit. This is expected."
                            )
                            continue
                        log_line = json_util.loads(line)
                        line_ts = log_line.get("t")
                        if line_ts is not None:
                            if self._start_time is not None and line_ts < self._start_time:
                                continue
                            if self._end_time is not None and line_ts > self._end_time:
                                continue
                        if self._log_start is None:
                            self._log_start = line_ts
                        for item in self._items:
                            try:
                                item.analyze(log_line)
                            except Exception as e:
                                self._logger.warning(
                                    yellow(f"Log analysis item '{item.name}' failed: {e}")
                                )
                                continue
                    except Exception:
                        self._logger.warning(
                            yellow(f"Failed to parse log line as JSON: {line.strip()}")
                        )
                        continue

        self._log_end = log_line.get("t", None) if log_line else None
        for item in self._items:
            try:
                item.finalize_analysis()
            except Exception as e:
                self._logger.warning(yellow(f"Log analysis item '{item.name}' finalize failed: {e}"))
                continue

    def output_results(self, output_folder: str = "output/", fmt: str = "html"):
        batch_folder = self._get_output_folder(output_folder)
        output_file = f"{batch_folder}report.md"
        template_file = get_script_path(f"templates/{self._config.get('template', 'log/full.html')}")
        self._logger.info("Saving results to: %s", green(output_file))

        with open(output_file, "w", encoding="utf-8") as f:
            assert (
                self._log_start is not None and self._log_end is not None
            ), "Log start and end time should be set after analysis."
            f.write("# Log Analysis Report\n")
            f.write(f"Generated at: `{str(datetime.now(tz=timezone.utc))} UTC`\n\n")
            f.write(f"Log path: `{self._file_path}`\n\n")
            if self._start_time or self._end_time:
                start_str = self._start_time.isoformat() if self._start_time else "…"
                end_str = self._end_time.isoformat() if self._end_time else "…"
                f.write(f"Requested time range: `{start_str}` – `{end_str}`\n\n")
            f.write(f"Log analysis period: `{self._log_start.isoformat()}` to `{self._log_end.isoformat()}`\n\n")
            f.write("Histogram chart instructions:\n\n")
            f.write("- **zoom in/out:** _ctrl+wheel, or pinch_\n")
            f.write("- **pan:** _shift+drag_\n")
            f.write("- **select time frame:** _drag_\n\n")
            for item in self._items:
                try:
                    item.review_results_markdown(f)
                except Exception as e:
                    self._logger.warning(yellow(f"Failed to generate markdown for log item '{item.name}': {e}"))
                    continue

        html_file = f"{batch_folder}report.html"
        if fmt in {"html", "pdf"}:
            self._logger.info("Converting markdown to HTML: %s", green(html_file))
            with open(html_file, "w", encoding="utf-8") as f:
                with open(output_file, "r", encoding="utf-8") as md_file:
                    html_content = markdown.markdown(
                        md_file.read(),
                        extensions=[TableWidthExtension(), "fenced_code", "toc", "md_in_html"],
                    )
                # Load the template file
                with open(template_file, "r", encoding="utf-8") as tf:
                    template_content = inject_assets(tf.read(), "log")
                    # Replace the placeholder with the generated HTML content
                final_html = template_content.replace("{{ content }}", html_content)
                f.write(final_html)

        if fmt == "pdf":
            pdf_file = f"{batch_folder}report.pdf"
            self._logger.info("Converting HTML report to: %s", green(pdf_file))
            html_to_pdf(html_file, pdf_file)
