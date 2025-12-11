from abc import abstractmethod
import logging
import os
from bson import json_util
from x_ray.healthcheck.check_items.base_item import colorize_severity
from x_ray.healthcheck.shared import SEVERITY
from x_ray.gmd_analysis.shared import GMD_EVENTS, to_json
from x_ray.utils import get_script_path, to_ejson
from x_ray.version import Version


class BaseItem:
    def __init__(self, output_folder: str, config, **kwargs):
        self.config = config
        self._output_file = os.path.join(output_folder, f"{self.__class__.__name__}.json")
        self._logger = logging.getLogger(__name__)
        self._server_version = None
        self._hostname = None
        self._set_name = None
        self._cluster_type = None
        self._test_result = []
        if os.path.isfile(self._output_file):
            os.remove(self._output_file)

        # Subscribe some common events that most items care about
        self._cache = None
        self._subbed_events = {}
        self._subbed_all_events = []
        self._fired_events = set()

        def get_version(block):
            sub_sec = block.get("subsection", "")
            if sub_sec == "server_build_info":
                self._server_version = Version.parse(block.get("output", {}).get("version", ""))

        def get_host(block):
            sub_sec = block.get("subsection", "")
            if sub_sec == "host_info":
                self._hostname = block.get("output", {}).get("system", {}).get("hostname", "unknown")

        def get_cluster_type(block):
            sub_sec = block.get("subsection", "")
            if sub_sec == "ismaster":
                output = block.get("output", {})
                set_name = output.get("setName", None)
                msg = output.get("msg", "")
                if set_name is not None:
                    self._cluster_type = "RS"
                    self._set_name = set_name
                elif msg == "isdbgrid":
                    self._cluster_type = "SH"
                else:
                    self._cluster_type = "STANDALONE"

        self.subscribe_one(GMD_EVENTS.SERVER_BUILD_INFO, get_version)
        self.subscribe_one(GMD_EVENTS.HOST_INFO, get_host)
        self.subscribe_one(GMD_EVENTS.ISMASTER, get_cluster_type)

    def test(self, block):
        sub_sec = block.get("subsection", "")
        try:
            current_event = GMD_EVENTS(sub_sec)
        except ValueError:
            current_event = GMD_EVENTS.UNKNOWN
        # Fire subscribed single events
        for event, funcs in self._subbed_events.items():
            if current_event == event:
                for func in funcs:
                    try:
                        func(block)
                    except Exception as e:
                        self._logger.warning("Error in subscribed function for event %s: %s", event.value, e)
                self._fired_events.add(event)

        # Fire subscribed all events
        for events, func in self._subbed_all_events:
            if events.issubset(self._fired_events) and current_event in events:
                try:
                    func()
                except Exception as e:
                    self._logger.warning("Error in subscribed all-events function for events %s: %s", events, e)

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

    @abstractmethod
    def review_results_markdown(self, output):
        raise NotImplementedError("Subclasses should implement this method.")

    def append_test_result(self, host: str, severity: SEVERITY, title: str, message: str):
        self._test_result.append({"host": host, "severity": severity, "title": title, "message": message})

    def append_test_results(self, items: list):
        for item in items:
            self.append_test_result(item["host"], item["severity"], item["title"], item["description"])

    def subscribe_one(self, event: GMD_EVENTS, func):
        """Fires when the specified event occurs."""
        if event not in self._subbed_events:
            self._subbed_events[event] = []
        self._subbed_events[event].append(func)

    def subscribe_all(self, events: set[GMD_EVENTS], func):
        """Fires when all the specified events occured."""
        self._subbed_all_events.append((events, func))
