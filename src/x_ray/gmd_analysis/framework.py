from datetime import datetime, timezone
import re
from pathlib import Path
import logging
import markdown
from x_ray.gmd_analysis.shared import load_json
from x_ray.healthcheck.shared import str_to_md_id, to_json
from x_ray.utils import load_classes, bold, green, red, yellow, cyan, get_script_path, env

logger = logging.getLogger(__name__)
GMD_CLASSES = load_classes("x_ray.gmd_analysis.gmd_items")


class Framework:
    _gmd_set_name = "default"

    def __init__(self, file_path: str, config: dict):
        self._file_path = file_path
        self._config = config
        self._logger = logging.getLogger(__name__)
        self._items = []
        now = str(datetime.now(tz=timezone.utc))
        self._timestamp = re.sub(r"[:\- ]", "", now.split(".", maxsplit=1)[0])
        self._logger.debug(to_json(self._config))
        self._log_start = None
        self._log_end = None
        if env == "development":
            self._logger.info(yellow("Running in development mode."))

    def _get_output_folder(self, output_folder: str):
        if env == "development":
            batch_folder = output_folder
        else:
            batch_folder = f"{output_folder}{self._gmd_set_name}-{self._timestamp}/"
        Path(batch_folder).mkdir(parents=True, exist_ok=True)
        return batch_folder

    def run_gmd_analysis(self, gmd_set_name: str, *args, **kwargs):
        self._gmd_set_name = gmd_set_name
        # Create output folder if it doesn't exist
        output_folder = kwargs.get("output_folder", "output/")
        batch_folder = self._get_output_folder(output_folder)
        # Dynamically load the gmd checkset based on the name
        gmdsets = self._config.get("gmdsets", {})
        if not gmd_set_name in gmdsets:
            self._logger.warning(yellow(f"GMD checkset '{gmd_set_name}' not found in configuration. Using default."))
            gmd_set_name = "default"
        gmdset = gmdsets[gmd_set_name]
        self._logger.info("Running GMD checkset: %s", bold(cyan(gmd_set_name)))

        self._items = []
        for item_name in gmdset.get("items", []):
            item_cls = GMD_CLASSES.get(item_name)
            if not item_cls:
                self._logger.warning(yellow(f"GMD item '{item_name}' not found. Skipping."))
                continue
            # The config for the item can be specified in the `item_config` section, under the item class name.
            item_config = self._config.get("item_config", {}).get(item_name, {})
            item = item_cls(batch_folder, item_config)
            self._items.append(item)
            self._logger.info("GMD analyze item loaded: %s", bold(cyan(item_name)))
        gmd_output = self._file_path

        # Read the getMongoData output and parse the whole content.
        with open(gmd_output, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            try:
                objects = load_json(content)
            except Exception as ex:
                self._logger.error(red(f"Failed to parse the getMongoData output as JSON: {ex}"))
                return

            self._logger.info("Ingesting %s objects from getMongoData output...", green(len(objects)))

            for i, obj in enumerate(objects):
                if (i + 1) % 10000 == 0:
                    self._logger.info("%s objects ingested...", green(i + 1))
                for item in self._items:
                    try:
                        item.test(obj)
                    except Exception as e:
                        self._logger.warning(yellow(f"GMD analysis item '{item.name}' failed: {e}"))
                        continue

    def output_results(self, output_folder: str = "output/", fmt: str = "html"):
        batch_folder = self._get_output_folder(output_folder)
        output_file = f"{batch_folder}report.md"
        template_file = get_script_path(f"templates/{self._config.get('template', 'gmd/full.html')}")
        self._logger.info("Saving results to: %s", green(output_file))

        with open(output_file, "w", encoding="utf-8") as output:
            output.write("# getMongoData Analysis Report\n")
            output.write(f"Generated at: `{str(datetime.now(tz=timezone.utc))} UTC`\n\n")
            output.write(f"File path: `{self._file_path}`\n\n")
            output.write("## 1 Review Test Results\n\n")
            for i, item in enumerate(self._items):
                try:
                    title = f"1.{i + 1} {item.name}"
                    review_title = f"2.{i + 1} Review {item.name}"
                    review_title_id = str_to_md_id(review_title)
                    output.write(f"### {title}\n\n")
                    output.write(f"{item.description}\n\n")
                    output.write(f"[Review Raw Results &rarr;](#{review_title_id})\n\n")
                    item.test_result_markdown(output)
                except Exception as e:
                    self._logger.warning(yellow(f"Failed to generate markdown for GMD item '{item.name}': {e}"))
                    continue

            output.write("## 2 Review Raw Results\n\n")
            for i, item in enumerate(self._items):
                try:
                    title = f"1.{i + 1} {item.name}"
                    title_id = str_to_md_id(title)
                    review_title = f"2.{i + 1} Review {item.name}"
                    output.write(f"### {review_title}\n\n")
                    output.write(f"[&larr; Review Test Results](#{title_id})\n\n")
                    item.review_results_markdown(output)
                except Exception as e:
                    self._logger.warning(yellow(f"Failed to generate review markdown for GMD item '{item.name}': {e}"))
                    continue

        if fmt == "html":
            html_file = f"{batch_folder}report.html"
            self._logger.info("Converting markdown to HTML: %s", green(html_file))
            with open(html_file, "w", encoding="utf-8") as output:
                with open(output_file, "r", encoding="utf-8") as md_file:
                    html_content = markdown.markdown(
                        md_file.read(),
                        extensions=["tables", "fenced_code", "toc", "md_in_html"],
                    )
                # Load the template file
                with open(template_file, "r", encoding="utf-8") as tf:
                    template_content = tf.read()
                    # Replace the placeholder with the generated HTML content
                final_html = template_content.replace("{{ content }}", html_content)
                output.write(final_html)
