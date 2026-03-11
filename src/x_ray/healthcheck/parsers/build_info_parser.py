from x_ray.healthcheck.parsers.base_parser import BaseParser


class BuildInfoParser(BaseParser):
    def parse(self, data, **kwargs) -> list:
        """
        Parse build information data.

        Args:
            data (list): The buildInfo command output of all hosts.

        Returns:
            list: The parsed build information as a list of table items.
        """
        output_list: list[dict] = []
        rows: list[list[str]] = []
        table_build_info: dict = {
            "type": "table",
            "caption": "Server Build Information",
            "header": ["Component", "Host", "Version", "OpenSSL", "Target Arch", "Target OS"],
            "rows": rows,
        }

        build_infos: list = data
        ver_count: dict[str, int] = {}
        for name, host, raw_result in build_infos:
            if raw_result is None:
                rows.append([name, host, "N/A", "N/A", "N/A", "N/A"])
                ver_count["N/A"] = ver_count.get("N/A", 0) + 1
                continue
            build_env = raw_result.get("buildEnvironment", {})
            v = raw_result.get("version", "")
            ver_count[v] = ver_count.get(v, 0) + 1
            rows.append(
                [
                    name,
                    host,
                    v,
                    raw_result.get("openssl", {}).get("running", ""),
                    build_env.get("target_arch", ""),
                    build_env.get("target_os", ""),
                ]
            )
        output_list.append(table_build_info)
        output_list.append({"type": "chart", "data": ver_count})
        return output_list
