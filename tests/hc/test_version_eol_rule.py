from libs.healthcheck.rules.version_eol_rule import VersionEOLRule

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
    rule = VersionEOLRule(EOL_VERSION)

    # Test with EOL version
    result = rule.apply(EOL_BUILD_INFO, result_template={"host": "localhost"})
    assert result is not None
    assert result[0]["severity"] == "HIGH"
    assert result[0]["title"] == "Server Version EOL"
    assert result[0]["host"] == "localhost"


def test_upd_version():
    rule = VersionEOLRule(EOL_VERSION)

    # Test with up-to-date version
    result = rule.apply(UPD_BUILD_INFO, result_template={"host": "localhost"})
    assert result == []


def test_rapid_version():
    rule = VersionEOLRule(EOL_VERSION)

    # Test with rapid release version
    result = rule.apply(RAPID_BUILD_INFO, result_template={"host": "localhost"})
    assert len(result) == 2
    assert result[0]["severity"] == "HIGH"
    assert result[0]["title"] == "Server Version EOL"
    assert result[0]["host"] == "localhost"
    assert result[1]["severity"] == "MEDIUM"
    assert result[1]["title"] == "Rapid Release Version Detected"
    assert result[1]["host"] == "localhost"


def test_dev_version():
    rule = VersionEOLRule(EOL_VERSION)

    # Test with development release version
    result = rule.apply(DEV_BUILD_INFO, result_template={"host": "localhost"})
    assert result[0]["severity"] == "MEDIUM"
    assert result[0]["title"] == "Development Release Version Detected"
    assert result[0]["host"] == "localhost"
