from x_ray.healthcheck.parsers.base_parser import BaseParser
from x_ray.utils import escape_markdown


class RSOverviewParser(BaseParser):
    def parse(self, data: list, **kwargs) -> list:
        """
        Parse replica set information data.

        Args:
            data (list): Each element is a tuple: (`RS name`, `RS config dict or None`)

        Returns:
            list: The parsed replica set information as a list of table items.
        """
        overview_table = {
            "type": "table",
            "caption": "Components Overview",
            "header": ["Name", "#Members", "#Voting Members", "#Arbiters", "#Hidden Members"],
            "rows": [],
        }
        for set_name, rs_config in data:
            if rs_config is None:
                overview_table["rows"].append([set_name, "N/A" * 4])
                continue
            members = rs_config["members"]
            num_members = len(members)
            num_voting = sum(1 for m in members if m["votes"] > 0)
            num_arbiters = sum(1 for m in members if m["arbiterOnly"])
            num_hidden = sum(1 for m in members if m["hidden"])
            overview_table["rows"].append(
                [
                    escape_markdown(rs_config["_id"]),
                    num_members,
                    num_voting,
                    num_arbiters,
                    num_hidden,
                ]
            )
        return [overview_table]
