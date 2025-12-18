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
from x_ray.version import Version


class VersionEOLRule(BaseRule):
    def apply(self, data: object, **kwargs) -> tuple:
        """Check if the given build info represents a version that is end-of-life (EOL).

        Args:
            data (object): The result from `buildInfo` command.
            extra_info (dict): Additional information such as host.
        Returns:
            tuple: (list of issues found, list of parsed data)
        """
        host = kwargs.get("extra_info", {}).get("host", "unknown")
        test_results = []
        version = Version(data.get("versionArray", [0, 0, 0]))
        eol_version = Version(self._thresholds.get("eol_version", [6, 3, 0]))
        # Check if the version is below EOL version
        if version < eol_version:
            issue = create_issue(
                ISSUE.EOL_VERSION_USED, host=host, params={"version": version, "eol_version": eol_version}
            )
            test_results.append(issue)
        # Check if rapid releases are being used
        if 5 <= version.major_version <= 7 and version.minor_version != 0:
            issue = create_issue(ISSUE.RAPID_RELEASE_VERSION_USED, host=host, params={"version": version})
            test_results.append(issue)
        # Check if development releases are being used
        if version.major_version >= 8 or version.major_version <= 4:
            if version.minor_version % 2 != 0:
                issue = create_issue(ISSUE.DEVELOPMENT_RELEASE_VERSION_USED, host=host, params={"version": version})
                test_results.append(issue)
        return test_results, data
