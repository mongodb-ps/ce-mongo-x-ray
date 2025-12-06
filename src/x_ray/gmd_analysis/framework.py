from datetime import datetime, timezone
import re
from pathlib import Path
import logging
import markdown
from bson import json_util
from x_ray.healthcheck.shared import to_json
from x_ray.utils import load_classes, bold, green, red, yellow, cyan, get_script_path, env

logger = logging.getLogger(__name__)
LOG_CLASSES = load_classes("x_ray.gmd.gmd_items")


class Framework:
    _gmd_set_name = ""

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
            item_cls = LOG_CLASSES.get(item_name)
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
                objects = json_util.loads(content)
            except Exception:
                self._logger.warning(red("Failed to parse the getMongoData output as JSON."))

            self._logger.info("Ingesting %s objects from getMongoData output...", green(len(objects)))

            for i, obj in enumerate(objects):
                if i % 10000 == 0:
                    self._logger.info("%s objects ingested...", green(i))
                for item in self._items:
                    try:
                        item.analyze(obj)
                    except Exception as e:
                        self._logger.warning(yellow(f"GMD analysis item '{item.name}' failed: {e}"))
                        continue

    def output_results(self, output_folder: str = "output/", fmt: str = "html"):
        batch_folder = self._get_output_folder(output_folder)
        output_file = f"{batch_folder}report.md"
        template_file = get_script_path(f"templates/{self._config.get('template', 'gmd/full.html')}")
        self._logger.info("Saving results to: %s", green(output_file))

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# getMongoData Analysis Report\n")
            f.write(f"Generated at: `{str(datetime.now(tz=timezone.utc))} UTC`\n\n")
            f.write(f"File path: `{self._file_path}`\n\n")
            for item in self._items:
                try:
                    item.review_results_markdown(f)
                except Exception as e:
                    self._logger.warning(yellow(f"Failed to generate markdown for GMD item '{item.name}': {e}"))
                    continue

        if fmt == "html":
            html_file = f"{batch_folder}report.html"
            self._logger.info("Converting markdown to HTML: %s", green(html_file))
            with open(html_file, "w", encoding="utf-8") as f:
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
                f.write(final_html)
