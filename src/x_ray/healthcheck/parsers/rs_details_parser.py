from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import is_number


class RSDetailsParser(BaseParser):
    def parse(self, data: dict, **kwargs) -> list:
        """
        Parse replica set detailed information data.

        Args:
            data (dict): Information a bout a single replica set, including:
                - set_name: The name of the replica set.
                - rs_config: The `replSetGetConfig` command output.
                - rs_status: The `replSetGetStatus` command output.
                - oplog_info: A dict mapping member hostnames to their oplog retention info.

        Returns:
            list: The parsed replica set detailed information as a list of table items.
        """
        set_name = data["set_name"]
        rs_config = data["rs_config"]
        rs_status = data["rs_status"]
        oplog_info = data["oplog_info"]
        details_table = {
            "type": "table",
            "caption": f"Component Details - `{set_name}`",
            "header": [
                "Host",
                "_id",
                "Arbiter",
                "Build Indexes",
                "Hidden",
                "Priority",
                "Votes",
                "Configured Delay (sec)",
                "Current Delay (sec)",
                "Oplog Window Hours",
            ],
            "rows": [],
        }
        if rs_config is None or rs_status is None:
            details_table["rows"].append(["N/A"] * len(details_table["header"]))
            return [details_table]
        latest_optime = max(m.get("optime", {}).get("ts") for m in rs_status["members"])
        member_delay = {m["name"]: (latest_optime.time - m["optime"]["ts"].time) for m in rs_status["members"]}

        for m in rs_config["members"]:
            host = m["host"]
            configured_retention_hours = oplog_info.get(host, {}).get("configured_retention_hours", "N/A")
            current_retention_hours = oplog_info.get(host, {}).get("current_retention_hours", "N/A")
            if is_number(configured_retention_hours) and is_number(current_retention_hours):
                retention_hours = max(configured_retention_hours, current_retention_hours)
            elif is_number(current_retention_hours):
                retention_hours = current_retention_hours
            else:
                retention_hours = "N/A"
            details_table["rows"].append(
                [
                    host,
                    m["_id"],
                    m["arbiterOnly"],
                    m["buildIndexes"],
                    m["hidden"],
                    m["priority"],
                    m["votes"],
                    m.get("secondaryDelaySecs", m.get("slaveDelay", 0)),
                    (member_delay.get(host, {}) if host in member_delay else "N/A"),
                    retention_hours,
                ]
            )
        return [details_table]
