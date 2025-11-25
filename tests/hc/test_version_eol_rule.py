from libs.healthcheck.issues import ISSUE, ISSUE_MSG_MAP
from libs.healthcheck.rules.version_eol_rule import VersionEOLRule
from libs.healthcheck.shared import SEVERITY

EOL_BUILD_INFO = {
    "versionArray": [4, 2, 8],
}
UPD_BUILD_INFO = {
    "versionArray": [8, 0, 6],
}
RAPID_BUILD_INFO = {
    "versionArray": [5, 2, 0],
}
DEV_BUILD_INFO = {
    "versionArray": [8, 1, 0],
}
EOL_VERSION = [6, 3, 0]


def test_eol_version():
    rule = VersionEOLRule({"eol_version": EOL_VERSION})

    # Test with EOL version
    result, _ = rule.apply(EOL_BUILD_INFO, extra_info={"host": "localhost"})
    assert result is not None
    assert result[0]["id"] == ISSUE.EOL_VERSION_USED
    assert result[0]["severity"] == SEVERITY.HIGH
    assert result[0]["title"] == "Server Version EOL"
    assert result[0]["host"] == "localhost"
    assert _ == EOL_BUILD_INFO


def test_upd_version():
    rule = VersionEOLRule({"eol_version": EOL_VERSION})

    # Test with up-to-date version
    result, _ = rule.apply(UPD_BUILD_INFO, extra_info={"host": "localhost"})
    assert result == []
    assert _ == UPD_BUILD_INFO


def test_rapid_version():
    rule = VersionEOLRule({"eol_version": EOL_VERSION})

    # Test with rapid release version
    result, _ = rule.apply(RAPID_BUILD_INFO, extra_info={"host": "localhost"})
    assert len(result) == 2
    assert result[0]["id"] == ISSUE.EOL_VERSION_USED
    assert result[0]["severity"] == SEVERITY.HIGH
    assert result[0]["title"] == "Server Version EOL"
    assert result[0]["host"] == "localhost"
    assert result[1]["id"] == ISSUE.RAPID_RELEASE_VERSION_USED
    assert result[1]["severity"] == SEVERITY.MEDIUM
    assert result[1]["title"] == ISSUE_MSG_MAP[ISSUE.RAPID_RELEASE_VERSION_USED]["title"]
    assert result[1]["host"] == "localhost"
    assert _ == RAPID_BUILD_INFO


def test_dev_version():
    rule = VersionEOLRule({"eol_version": EOL_VERSION})

    # Test with development release version
    result, _ = rule.apply(DEV_BUILD_INFO, extra_info={"host": "localhost"})
    assert result[0]["id"] == ISSUE.DEVELOPMENT_RELEASE_VERSION_USED
    assert result[0]["severity"] == SEVERITY.MEDIUM
    assert result[0]["title"] == ISSUE_MSG_MAP[ISSUE.DEVELOPMENT_RELEASE_VERSION_USED]["title"]
    assert result[0]["host"] == "localhost"
    assert _ == DEV_BUILD_INFO
