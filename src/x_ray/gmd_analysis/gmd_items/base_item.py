from abc import abstractmethod
import logging
import os
from typing import Callable, Optional
from bson import json_util
from x_ray.healthcheck.check_items.base_item import colorize_severity
from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.shared import SEVERITY
from x_ray.gmd_analysis.shared import GMD_EVENTS
from x_ray.utils import bold, to_ejson, yellow
from x_ray.version import Version


class BaseItem:  # pylint: disable=too-many-instance-attributes
    def __init__(self, output_folder: str, config, **kwargs) -> None:
        self.config: dict = config
        self._output_file = os.path.join(output_folder, f"{self.__class__.__name__}.json")
        self._logger = logging.getLogger(__name__)
        self._server_version: Optional[Version] = None
        self._hostname: Optional[str] = None
        self._set_name: Optional[str] = None
        self._cluster_type: Optional[str] = None
        self._test_result: list = []
        self._rules: dict[str, BaseRule] = {}
        if os.path.isfile(self._output_file):
            os.remove(self._output_file)

        self._in_complete_flag = False
        # Subscribe some common events that most items care about
        self._cache = None
        self._watched_events: dict[GMD_EVENTS, list[Callable]] = {}
        self._watched_all_events: list[tuple[set[GMD_EVENTS], Callable]] = []
        self._fired_events: set[GMD_EVENTS] = set()

        def get_version(block):
            self._server_version = Version.parse(block.get("output", {}).get("version", ""))

        def get_host(block):
            if self._hostname is None:
                self._hostname = block.get("output", {}).get("system", {}).get("hostname", "unknown")

        def get_cluster_type(block):
            output = block.get("output", {})
            set_name = output.get("setName", None)
            msg = output.get("msg", "")
            if set_name is not None:
                self._cluster_type = "RS"
                self._set_name = set_name
            elif msg == "isdbgrid":
                self._cluster_type = "SH"
                self._set_name = "mongos"
            else:
                self._cluster_type = "STANDALONE"

            # Use hostname in ismaster whenever possible
            if "me" in output:
                self._hostname = output["me"]

        self.watch_one(GMD_EVENTS.SERVER_BUILD_INFO, get_version)
        self.watch_one(GMD_EVENTS.HOST_INFO, get_host)
        self.watch_one(GMD_EVENTS.ISMASTER, get_cluster_type)

    def test(self, block) -> None:
        sub_sec = block.get("subsection", "")
        sub_sec = sub_sec.replace("INCOMPLETE_", "")
        try:
            current_event = GMD_EVENTS(sub_sec)
        except ValueError:
            current_event = GMD_EVENTS.UNKNOWN
        # Fire subscribed single events
        for event, funcs in self._watched_events.items():
            if current_event == event:
                if block.get("subsection", "").startswith("INCOMPLETE_"):
                    self._in_complete_flag = True
                for func in funcs:
                    try:
                        func(block)
                    except Exception as e:
                        self._logger.warning(yellow("Error in subscribed function for event %s: %s"), event.value, e)
                self._fired_events.add(event)

        # Fire subscribed all events
        for events, func in self._watched_all_events:
            if events.issubset(self._fired_events) and current_event in events:
                try:
                    func()
                except Exception as e:
                    self._logger.warning("Error in subscribed all-events function for events %s: %s", events, e)

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value

    @property
    def description(self) -> str:
        desc: str = ""
        for rule in self._rules.values():
            desc += rule.description_md + "\n"
        return desc

    @property
    def test_result(self) -> list:
        return self._test_result

    @property
    def captured_sample(self) -> Optional[dict]:
        try:
            with open(self._output_file, "r", encoding="utf-8") as f:
                return json_util.loads(f.read())
        except FileNotFoundError:
            self._logger.warning(
                "Captured sample file not found: %s. This is probably because the getMongoData output is incomplete.",
                bold(self._output_file),
            )
            return None

    @captured_sample.setter
    def captured_sample(self, data: Optional[dict]) -> None:
        with open(self._output_file, "w", encoding="utf-8") as f:
            f.write(to_ejson(data, indent=None))

    def test_result_markdown(self, output) -> None:
        if len(self._test_result) == 0:
            output.write("<b style='color: green;'>Pass.</b>\n\n")
            return

        output.write(
            '| <span data-sortable="false">\\#</span>{60px}'
            ' | <span data-sortable="true">Host</span>{180px}'
            ' | <span data-sortable="true">Severity</span>{120px}'
            ' | <span data-sortable="true">Category</span>{200px}'
            ' | <span data-sortable="false">Message</span>{*} |\n'
        )
        output.write("|:----------:|:----------:|:----------:|---------|---------|\n")
        for idx, item in enumerate(self._test_result):
            severity = item["severity"]
            severity_cell = (
                f'<span data-sort-value="{severity.value}">'
                f"<b style='color: {colorize_severity(severity)}'>"
                f" {severity.name} </b></span>"
            )
            output.write(
                f"| **{idx + 1}** "
                f"| `{item['host']}` "
                f"| {severity_cell} "
                f"| {item['title']} "
                f"| {item['message']} |\n"
            )
        output.write("\n")

    def finalize_analysis(self) -> None:
        """
        This function will be called after all GMD data is ingested and before generating the report.
        You can do some final analysis here that requires all data to be available.
        """

    @abstractmethod
    def review_results_markdown(self, output) -> None:
        raise NotImplementedError("Subclasses should implement this method.")

    def append_test_result(self, host: str, severity: SEVERITY, title: str, message: str) -> None:
        self._test_result.append({"host": host, "severity": severity, "title": title, "message": message})

    def append_test_results(self, items: list) -> None:
        for item in items:
            self.append_test_result(item["host"], item["severity"], item["title"], item["description"])

    def watch_one(self, event: GMD_EVENTS, func) -> None:
        """
        Fires when the specified event occurs.
        The order of `watch_one` depends on the order of events in the GMD log, not the order of `watch_one` calls.
        """
        if event not in self._watched_events:
            self._watched_events[event] = []
        self._watched_events[event].append(func)

    def watch_all(self, events: set[GMD_EVENTS], func) -> None:
        """
        Fires when all the specified events occured.
        `watch_all` fires after the last `watch_one` fires.
        """
        self._watched_all_events.append((events, func))

    @property
    def all_events_fired(self) -> bool:
        """
        Check if all watched events have been fired.
        If not all events are fired, some data may be missing in the GMD.
        """
        return all(event in self._fired_events for event in self._watched_events)
