from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import format_size


class HostInfoParser(BaseParser):
    def parse(self, data: object, **kwargs) -> str:
        """
        Parse host information data.

        Args:
            data (list): The hostInfo command output.

        Returns:
            str: The parsed host information in markdown.
        """
        headers = ["Host", "CPU Family", "CPU Cores", "Memory", "OS", "NUMA Enabled"]
        rows = []
        for info in data:
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
                    format_size(system["memSizeMB"] * 1024**2),
                    f"{os['name']} {os['version']}",
                    system["numaEnabled"],
                ]
            )
        return self.parse_table(headers, rows)
