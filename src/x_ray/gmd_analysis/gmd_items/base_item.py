import logging
import os
from bson import json_util
from x_ray.healthcheck.check_items.base_item import colorize_severity
from x_ray.healthcheck.shared import SEVERITY
from x_ray.gmd_analysis.shared import to_json
from x_ray.utils import get_script_path, to_ejson
from x_ray.version import Version


def get_version(block):
    """
    Extract and parse the version information from a log line.
    """
    sub_sec = block.get("subsection", "")
    if sub_sec != "server_build_info":
        return None
    ver_str = block.get("output", {}).get("version", "")
    return Version.parse(ver_str)


class BaseItem:
    _cache = None

    def __init__(self, output_folder: str, config, **kwargs):
        self.config = config
        self._output_file = os.path.join(output_folder, f"{self.__class__.__name__}.json")
        self._logger = logging.getLogger(__name__)
        self._server_version = None
        self._test_result = []
        if os.path.isfile(self._output_file):
            os.remove(self._output_file)

    def test(self, block):
        version = get_version(block)
        if version is not None:
            self._server_version = version

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    @property
    def captured_sample(self):
        try:
            with open(self._output_file, "r", encoding="utf-8") as f:
                return json_util.loads(f.read())
        except FileNotFoundError:
            return None

    @captured_sample.setter
    def captured_sample(self, data):
        with open(self._output_file, "w", encoding="utf-8") as f:
            f.write(to_ejson(data, indent=None))

    def test_result_markdown(self, output):
        if len(self._test_result) == 0:
            output.write("<b style='color: green;'>Pass.</b>\n\n")
            return

        output.write("| \\# | Host | Severity | Category | Message |\n")
        output.write("|:----------:|:----------:|:----------:|---------|---------|\n")
        for idx, item in enumerate(self._test_result):
            output.write(
                f"| **{idx + 1}** | `{item['host']}` | <b style='color: {colorize_severity(item['severity'])}'> {item['severity'].name} </b> | {item['title']} | {item['message']} |\n"
            )
        output.write("\n")

    def review_results_markdown(self, output):
        # Write JS snippet to the file
        file_name = f"{self.__class__.__name__}.js"
        file_path = os.path.join("templates", "gmd", "snippets", file_name)
        file_path = get_script_path(file_path)
        self._logger.debug("Using JS snippet file: %s", file_path)

        output.write('<script type="text/javascript">\n')
        output.write("document.addEventListener('DOMContentLoaded', function() {\n")
        output.write("let data = [\n")
        with open(self._output_file, "r", encoding="utf-8") as data:
            for line in data:
                # The data is in EJSON format, convert it to JSON
                line_json = json_util.loads(line)
                output.write(to_json(line_json))
                output.write(", \n")
        output.write("];\n")
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as js:
                for line in js:
                    output.write(line.replace("{name}", self.__class__.__name__))
        output.write("});\n")
        output.write("</script>\n")

    def _write_output(self):
        # Open file steam and write the cache to file
        # Even if the cache is None, we still write to indicate no data
        with open(self._output_file, "a", encoding="utf-8") as f:
            if self._cache is None:
                self._logger.debug("Cache is empty, nothing to write for %s", self.__class__.__name__)
                return
            if isinstance(self._cache, list):
                for item in self._cache:
                    f.write(to_ejson(item, indent=None))
                    f.write("\n")
                    self._row_count += 1
                self._logger.debug(
                    "Wrote %d records to %s for %s",
                    len(self._cache),
                    self._output_file,
                    self.__class__.__name__,
                )
            else:
                f.write(to_ejson(self._cache, indent=None))
                f.write("\n")
                self._row_count += 1
                self._logger.debug(
                    "Wrote 1 record to %s for %s",
                    self._output_file,
                    self.__class__.__name__,
                )

    def append_test_result(self, host: str, severity: SEVERITY, title: str, message: str):
        self._test_result.append({"host": host, "severity": severity, "title": title, "message": message})

    def append_test_results(self, items: list):
        for item in items:
            self.append_test_result(item["host"], item["severity"], item["title"], item["description"])
