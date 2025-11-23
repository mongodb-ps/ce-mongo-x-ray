from libs.healthcheck.rules.base_rule import BaseRule
from libs.healthcheck.shared import SEVERITY
from libs.version import Version


class VersionEOLRule(BaseRule):
    def __init__(self, eol_version: list = None):
        super().__init__(eol_version)
        self._eol_version = Version(eol_version)

    def apply(self, data: object, result_template=None) -> object:
        """Check if the given build info represents a version that is end-of-life (EOL).

        Args:
            build_info (object): The result from `buildInfo` command.
        Returns:
            list: A list of EOL check results.
        """
        test_results = []
        template = result_template or {}
        version = Version(data.get("versionArray", [0, 0, 0]))
        # Check if the version is below EOL version
        if version < self._eol_version:
            test_results.append(
                template
                | {
                    "severity": SEVERITY.HIGH,
                    "title": "Server Version EOL",
                    "description": f"Server version {version} is below EOL version {self._eol_version}. Consider upgrading to the latest version.",
                }
            )
        # Check if rapid releases are being used
        if 5 <= version.major_version <= 7 and version.minor_version != 0:
            test_results.append(
                template
                | {
                    "severity": SEVERITY.MEDIUM,
                    "title": "Rapid Release Version Detected",
                    "description": f"Server version {version} is a unsupported rapid release version. Consider using release versions for better stability and support.",
                }
            )
        # Check if development releases are being used
        if version.major_version >= 8 or version.major_version <= 4:
            if version.minor_version % 2 != 0:
                test_results.append(
                    template
                    | {
                        "severity": SEVERITY.MEDIUM,
                        "title": "Development Release Version Detected",
                        "description": f"Server version {version} appears to be a development release. Consider using stable release versions for production environments.",
                    }
                )
        return test_results
