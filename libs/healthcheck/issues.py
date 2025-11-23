import enum


class ISSUE(enum.Enum):
    EOL_VERSION_USED = 100
    RAPID_RELEASE_VERSION_USED = 101
    DEVELOPMENT_RELEASE_VERSION_USED = 102


ISSUE_MSG_MAP = {
    ISSUE.EOL_VERSION_USED: {
        "title": "Server Version EOL",
        "description": "Server version {version} is below EOL version {eol_version}. Consider upgrading to the latest version.",
    },
    ISSUE.RAPID_RELEASE_VERSION_USED: {
        "title": "Rapid Release Version Detected",
        "description": "Server version {version} is a unsupported rapid release version. Consider using release versions for better stability and support.",
    },
    ISSUE.DEVELOPMENT_RELEASE_VERSION_USED: {
        "title": "Development Release Version Detected",
        "description": "Server version {version} appears to be a development release. Consider using stable release versions for production environments.",
    },
}
