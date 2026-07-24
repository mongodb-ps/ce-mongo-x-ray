from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import format_size


class HostInfoParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        """
        Parse host information data.

        Args:
            data (list): The hostInfo command output of all hosts.

        Returns:
            list: The parsed host information as a list of table items.
        """
        output_list: list[dict] = []
        rows: list[list[str]] = []
        rows_mounts: list[list[str]] = []
        table_hardware: dict = {
            "type": "table",
            "caption": "Host Hardware Information",
            "header": [
                {"text": "Host", "width": "*"},
                {"text": "CPU Family", "width": "350px"},
                {"text": "CPU Cores", "width": "100px"},
                {"text": "Memory", "width": "100px"},
                {"text": "OS", "width": "150px"},
                {"text": "NUMA Enabled", "width": "100px"},
            ],
            "rows": rows,
        }

        table_mounts: dict = {
            "type": "table",
            "caption": "Mount Points",
            "header": [
                {"text": "Host", "width": "*"},
                {"text": "Mount Point", "width": "550px"},
                {"text": "Type", "width": "100px"},
                {"text": "Options", "width": "200px"},
            ],
            "rows": rows_mounts,
        }
        for host, info in data:
            if not info:
                rows.append([host, "N/A", "N/A", "N/A", "N/A", "N/A"])
                continue
            system: dict = info["system"]
            os: dict = info["os"]
            extra: dict = info["extra"]
            if "extra" in extra:
                # Compatibility for MongoDB 6.0
                extra = extra["extra"]
            mem_bytes = system["memLimitMB"] * 1024**2
            rows.append(
                [
                    system["hostname"],
                    f"{extra.get('cpuString', '(Unknown CPU)')} ({system['cpuArch']}) {extra.get('cpuFrequencyMHz', 'n/a')} MHz",
                    f"{system['numCores']}c",
                    (format_size(mem_bytes), mem_bytes),
                    f"{os['name']} {os['version']}",
                    system["numaEnabled"],
                ]
            )
            mounts: list[dict] = extra.get("mountInfo", [])
            for mount in mounts:
                rows_mounts.append(
                    [
                        system["hostname"],
                        mount.get("mountPoint", "N/A"),
                        mount.get("type", "N/A"),
                        mount.get("options", "N/A"),
                    ]
                )
        output_list.append(table_hardware)
        output_list.append(table_mounts)
        return output_list
