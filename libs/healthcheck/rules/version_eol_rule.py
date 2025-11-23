from libs.healthcheck.rules.base_rule import BaseRule
from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
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
            issue_id = ISSUE.EOL_VERSION_USED
            test_results.append(
                template
                | {
                    "id": issue_id,
                    "severity": SEVERITY.HIGH,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(
                        version=version, eol_version=self._eol_version
                    ),
                }
            )
        # Check if rapid releases are being used
        if 5 <= version.major_version <= 7 and version.minor_version != 0:
            issue_id = ISSUE.RAPID_RELEASE_VERSION_USED
            test_results.append(
                template
                | {
                    "id": issue_id,
                    "severity": SEVERITY.MEDIUM,
                    "title": ISSUE_MSG_MAP[issue_id]["title"],
                    "description": ISSUE_MSG_MAP[issue_id]["description"].format(version=version),
                }
            )
        # Check if development releases are being used
        if version.major_version >= 8 or version.major_version <= 4:
            if version.minor_version % 2 != 0:
                issue_id = ISSUE.DEVELOPMENT_RELEASE_VERSION_USED
                test_results.append(
                    template
                    | {
                        "id": issue_id,
                        "severity": SEVERITY.MEDIUM,
                        "title": ISSUE_MSG_MAP[issue_id]["title"],
                        "description": ISSUE_MSG_MAP[issue_id]["description"].format(version=version),
                    }
                )
        return test_results
