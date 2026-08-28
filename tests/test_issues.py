"""Tests for the shared issue catalog (mongo_x_ray.issues)."""

import pytest

from mongo_x_ray.issues import ISSUE, ISSUE_MSG_MAP, create_issue


def test_issue_enum_covers_message_map():
    # every defined issue has a message template
    assert set(ISSUE) == set(ISSUE_MSG_MAP)
    # and every template carries the metadata the report needs
    for issue_id, template in ISSUE_MSG_MAP.items():
        assert template["id"] is issue_id
        assert {"severity", "title", "description"} <= set(template)


def test_create_issue_formats_description():
    issue = create_issue(ISSUE.EOL_VERSION_USED, host="db1", params={"version": "4.4", "eol_version": "5.0"})
    assert issue["id"] is ISSUE.EOL_VERSION_USED
    assert issue["host"] == "db1"
    assert issue["title"] == "Server Version EOL"
    assert "4.4" in issue["description"] and "5.0" in issue["description"]


def test_create_issue_without_params_keeps_placeholders():
    issue = create_issue(ISSUE.NO_PRIMARY, host="db1")
    assert "{set_name}" in issue["description"]


def test_create_issue_rejects_unknown_id():
    with pytest.raises(ValueError):
        create_issue("NOT_AN_ISSUE", host="db1")  # type: ignore[arg-type]
