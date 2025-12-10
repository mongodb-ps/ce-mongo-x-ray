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
        output_list = []
        rows, rows_mounts = [], []
        table_hardware = {
            "type": "table",
            "caption": "Host Hardware Information",
            "headers": [
                "Host",
                "CPU Family",
                "CPU Cores",
                "Memory",
                "OS",
                "NUMA Enabled",
            ],
            "rows": rows,
        }

        table_mounts = {
            "type": "table",
            "caption": "Mount Points",
            "headers": [
                "Host",
                "Mount Point",
                "Type",
                "Options",
            ],
            "rows": rows_mounts,
        }
        for host, info in data:
            if not info:
                rows.append([host, "N/A", "N/A", "N/A", "N/A", "N/A"])
                continue
            system = info["system"]
            os = info["os"]
            extra = info["extra"]
            if "extra" in extra:
                # Compatibility for MongoDB 6.0
                extra = extra["extra"]
            rows.append(
                [
                    system["hostname"],
                    f"{extra.get('cpuString', '(Unknown CPU)')} ({system['cpuArch']}) {extra.get('cpuFrequencyMHz', 'n/a')} MHz",
                    f"{system['numCores']}c",
                    format_size(system["memLimitMB"] * 1024**2),
                    f"{os['name']} {os['version']}",
                    system["numaEnabled"],
                ]
            )
            mounts = extra.get("mountInfo", [])
            for mount in mounts:
                rows_mounts.append(
                    [
                        system["hostname"],
                        mount["mountPoint"],
                        mount["type"],
                        mount["options"],
                    ]
                )
        output_list.append(table_hardware)
        output_list.append(table_mounts)
        return output_list
