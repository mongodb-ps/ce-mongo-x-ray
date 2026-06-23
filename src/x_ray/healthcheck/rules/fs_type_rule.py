"""
Copyright (c) 2025 MongoDB Inc.

DISCLAIMER: THESE CODE SAMPLES ARE PROVIDED FOR EDUCATIONAL AND ILLUSTRATIVE PURPOSES ONLY,
TO DEMONSTRATE THE FUNCTIONALITY OF SPECIFIC MONGODB FEATURES.
THEY ARE NOT PRODUCTION-READY AND MAY LACK THE SECURITY HARDENING, ERROR HANDLING, AND TESTING REQUIRED FOR A LIVE ENVIRONMENT.
YOU ARE RESPONSIBLE FOR TESTING, VALIDATING, AND SECURING THIS CODE WITHIN YOUR OWN ENVIRONMENT BEFORE IMPLEMENTATION.
THIS MATERIAL IS PROVIDED "AS IS" WITHOUT WARRANTY OR LIABILITY.
"""

from x_ray.healthcheck.rules.base_rule import BaseRule
from x_ray.healthcheck.issues import ISSUE, create_issue


class FSTypeRule(BaseRule):
    def __init__(self, thresholds=None):
        super().__init__(thresholds)
        self._rule_desc.append("Checks if the filesystem type is supported.")

    def apply(self, data: dict, **kwargs) -> tuple:
        """Check the filesystem type for any issues.

        Args:
            data (dict):
                - The `hostInfo` command result.
                - The `serverCmdLineOpts` command result.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        extra_info = kwargs.get("extra_info", {})
        host = extra_info.get("host", "unknown")
        host_info = data.get("hostInfo", {})
        mongo_conf = data.get("serverCmdLineOpts", {}).get("parsed", {})
        issues: list = []
        db_path = mongo_conf.get("storage", {}).get("dbPath", None)
        if not db_path:
            return issues, data
        extra = host_info.get("extra", {})
        if "extra" in extra:
            # Compatibility for MongoDB 6.0
            extra = extra["extra"]
        mounts = extra.get("mountInfo", [])
        mounts = sorted(mounts, key=lambda x: len(x.get("mountPoint", "")), reverse=True)
        for mount in mounts:
            mount_point = mount.get("mountPoint")
            if db_path.startswith(mount_point):
                fs_type = mount.get("type", "").lower()
                if fs_type == "ext4":
                    issue = create_issue(
                        ISSUE.FS_TYPE_EXT4,
                        host,
                        params={"fs_type": fs_type, "mount_point": mount_point, "db_path": db_path},
                    )
                    issues.append(issue)
                    if "noatime" not in mount.get("options", ""):
                        issue = create_issue(
                            ISSUE.FS_TYPE_EXT4_NOATIME,
                            host,
                            params={"fs_type": fs_type, "mount_point": mount_point, "db_path": db_path},
                        )
                        issues.append(issue)
                elif fs_type != "xfs":
                    issue = create_issue(
                        ISSUE.FS_TYPE,
                        host,
                        params={"fs_type": fs_type, "mount_point": mount_point, "db_path": db_path},
                    )
                    issues.append(issue)
                break
        return issues, data
