"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

import logging
import random
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TextIO

from bson import json_util

from x_ray.framework import BaseFramework
from x_ray.log_analysis.log_items.info_item import InfoItem
from x_ray.log_analysis.log_items.state_trace_item import StateTraceItem
from x_ray.shared import to_json
from x_ray.utils import bold, cyan, env, green, load_classes, yellow

logger = logging.getLogger(__name__)
LOG_CLASSES = load_classes("x_ray.log_analysis.log_items")
SKIP_LINE_MSG = "HEADER INCLUDED, NOW SKIPPING 64728 LINES ACCORDING TO REQUESTED SIZE LIMIT"
_SANITIZE_DATE_RE = re.compile(r'\{\s*"\$date"\s*:\s*\{\s*"\$numberLong"\s*:\s*"-?\d{16,}"\s*\}\s*\}')


def _sanitize_date_numberlong(line: str) -> str:
    """Replace out-of-range $date.$numberLong sentinel values with null."""
    return _SANITIZE_DATE_RE.sub("null", line)


def _safe_json_loads(line: str) -> dict:
    """Parse a JSON log line, sanitising out-of-range dates on failure only.
    Also ensures all datetime values are timezone-aware (UTC).
    """
    try:
        parsed = json_util.loads(line)
        _normalise_datetimes(parsed)
        return parsed
    except Exception as exc:  # pylint: disable=broad-exception-caught
        try:
            parsed = json_util.loads(_sanitize_date_numberlong(line))
            _normalise_datetimes(parsed)
            return parsed
        except Exception:  # pylint: disable=broad-exception-caught
            logger.debug("JSON parse failed (first error: %s): %s", exc, line.strip()[:200])
            return {}


def _normalise_datetimes(obj: dict) -> None:
    """Ensure all datetime values in *obj* are UTC-aware (in place)."""
    for key, value in obj.items():
        if isinstance(value, datetime) and value.tzinfo is None:
            obj[key] = value.replace(tzinfo=timezone.utc)


class Framework(BaseFramework):
    template_module = "log"

    def __init__(
        self,
        file_path: str,
        config: dict,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        super().__init__(config)
        self._file_path = file_path
        self._start_time = start_time
        self._end_time = end_time
        self._logger.debug(to_json(self._config))
        self._log_start: Optional[datetime] = None
        self._log_end: Optional[datetime] = None
        self._hostname: Optional[str] = None
        if env == "development":
            self._logger.info(yellow("Running in development mode."))

    @property
    def hostname(self) -> Optional[str]:
        """The hostname from the Process Info log item, or from log lines."""
        for item in self._items:
            if isinstance(item, InfoItem):
                host = item._cache.get("process", {}).get("host")  # pylint: disable=protected-access
                if host and host != "Unknown":
                    return host
                break
        return self._hostname

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
        """Read the first and last valid JSON log line to get the file's time range."""
        first_ts = None
        last_ts = None
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                # Skip preamble lines (e.g. Atlas download header)
                for line in f:
                    parsed = _safe_json_loads(line)
                    if parsed:
                        first_ts = parsed.get("t")
                        break
                # Scan backwards from end for the last non-empty line
                f.seek(0, 2)
                pos = f.tell()
                last_line = ""
                while pos > 0:
                    pos -= 1
                    f.seek(pos)
                    if f.read(1) == "\n":
                        candidate = f.readline().strip()
                        if candidate:
                            last_line = candidate
                            break
                if last_line:
                    last_ts = _safe_json_loads(last_line).get("t")
        except Exception as exc:  # pylint: disable=broad-exception-caught
            logger.warning("Failed to read time range from %s: %s", file_path.name, exc)
        logger.debug(
            "File %s time range: %s – %s",
            file_path.name,
            first_ts.isoformat() if first_ts else "?",
            last_ts.isoformat() if last_ts else "?",
        )
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

    def _any_file_fully_covered(self, files: list[Path]) -> bool:
        """Return True if at least one file is fully within [start_time, end_time]."""
        if self._start_time is None and self._end_time is None:
            return True
        for fp in files:
            first_ts, last_ts = self._file_time_range(fp)
            if first_ts is None or last_ts is None:
                continue
            if (self._start_time is None or first_ts >= self._start_time) and (
                self._end_time is None or last_ts <= self._end_time
            ):
                return True
        return False

    def run_logs_analysis(self, logset_name: str, *_args, **kwargs):
        self._set_name = logset_name
        # Create output folder if it doesn't exist
        output_folder = kwargs.get("output_folder", "output/")
        batch_folder = self._get_output_folder(output_folder)
        # Dynamically load the log checkset based on the name
        logsets = self._config.get("logsets", {})
        if logset_name not in logsets:
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
            item = item_cls(str(batch_folder), item_config)
            self._items.append(item)
            self._logger.info("Log analyze item loaded: %s", bold(cyan(item_name)))

        rate = self._config.get("sample_rate", 1.0)
        log_files = self._log_files()
        partial_only = (self._start_time is not None or self._end_time is not None) and not self._any_file_fully_covered(
            log_files
        )
        if partial_only:
            self._logger.info(
                "No log file is fully covered by the requested time range. "
                "InfoItem and StateTraceItem will receive all lines."
            )
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
                            self._logger.debug("Some lines are skipped due to the size limit. This is expected.")
                            continue
                        log_line = _safe_json_loads(line)
                        if not log_line:
                            self._logger.warning(yellow(f"Failed to parse log line as JSON: {line.strip()}"))
                            continue
                        if self._hostname is None:
                            hostname = log_line.get("hostname")
                            if isinstance(hostname, str) and hostname.strip():
                                self._hostname = hostname.strip()
                        line_ts = log_line.get("t")
                        out_of_range = False
                        if line_ts is not None:
                            if self._start_time is not None and line_ts < self._start_time:
                                out_of_range = True
                            elif self._end_time is not None and line_ts > self._end_time:
                                out_of_range = True

                        if out_of_range and not partial_only:
                            continue

                        if self._log_start is None:
                            self._log_start = line_ts

                        if out_of_range:
                            # partial_only: dispatch only to InfoItem and StateTraceItem
                            for item in self._items:
                                if isinstance(item, (InfoItem, StateTraceItem)):
                                    try:
                                        item.analyze(log_line)
                                    except Exception as e:  # pylint: disable=broad-exception-caught
                                        self._logger.warning(
                                            yellow(f"Log analysis item '{item.name}' failed: {e}")
                                        )
                            continue

                        for item in self._items:
                            try:
                                item.analyze(log_line)
                            except Exception as e:  # pylint: disable=broad-exception-caught
                                self._logger.warning(yellow(f"Log analysis item '{item.name}' failed: {e}"))
                                continue
                    except Exception as exc:  # pylint: disable=broad-exception-caught
                        self._logger.warning(yellow(f"Unexpected error processing log line: {exc}"))
                        continue

        self._log_end = log_line.get("t", None) if log_line else None
        for item in self._items:
            try:
                item.finalize_analysis()
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.warning(yellow(f"Log analysis item '{item.name}' finalize failed: {e}"))
                continue

    def _render_markdown(self, output: TextIO) -> None:
        assert (
            self._log_start is not None and self._log_end is not None
        ), "Log start and end time should be set after analysis."
        output.write("# Log Analysis Report\n")
        output.write(f"Generated at: `{str(datetime.now(tz=timezone.utc))} UTC`\n\n")
        output.write(f"Log path: `{self._file_path}`\n\n")
        if self._start_time or self._end_time:
            start_str = self._start_time.isoformat() if self._start_time else "…"
            end_str = self._end_time.isoformat() if self._end_time else "…"
            output.write(f"Requested time range: `{start_str}` – `{end_str}`\n\n")
        output.write(f"Log analysis period: `{self._log_start.isoformat()}` to `{self._log_end.isoformat()}`\n\n")
        output.write("Histogram chart instructions:\n\n")
        output.write("- **zoom in/out:** _ctrl+wheel, or pinch_\n")
        output.write("- **pan:** _shift+drag_\n")
        output.write("- **select time frame:** _drag_\n\n")
        for item in self._items:
            try:
                item.review_results_markdown(output)
            except Exception as e:  # pylint: disable=broad-exception-caught
                self._logger.warning(yellow(f"Failed to generate markdown for log item '{item.name}': {e}"))
                continue
