from bson import json_util  # type: ignore
from x_ray.healthcheck.parsers.index_info_parser import IndexInfoParser  # type: ignore

INDEX_INFOS = """[
    {"ns": "foo._test_", "captureTime": {"$date": "2026-03-17T22:08:34.595"}, "indexStats": []},
    {
        "ns": "test.test",
        "captureTime": {"$date": "2026-03-17T00:01:00Z"},
        "indexStats": [
            {
                "name": "_id_",
                "key": {"_id": 1},
                "host": "M-QTFH0WFXLG:30018",
                "accesses": {"ops": 100, "since": {"$date": "2026-03-17T00:00:00Z"}},
                "shard": "shard01",
                "spec": {"v": 2, "key": {"_id": 1}, "name": "_id_"}
            }
        ]
    }
]"""


def test_index_info_parser():
    parser = IndexInfoParser()
    result = parser.parse(json_util.loads(INDEX_INFOS))
    assert len(result) == 1
    table = result[0]
    assert table["type"] == "table"
    assert table["caption"] == "Index Review"
    assert table["header"] == [
        "Component",
        "Namespace",
        "Name",
        {"text": "Definition", "align": "left"},
        "Access per Hour",
    ]
    assert len(table["rows"]) == 1
    assert table["rows"][0][0] == "shard01"
    assert table["rows"][0][1] == "test.test"
    assert table["rows"][0][2] == "\_id\_"
    assert table["rows"][0][3] == '`{"_id": 1}`'
    assert table["rows"][0][4] == "6000.0000"


def test_index_info_parser_no_data():
    parser = IndexInfoParser()
    result = parser.parse(None, set_name="test_set")
    assert len(result) == 1
    table = result[0]
    assert table["type"] == "table"
    assert table["caption"] == "Index Review"
    assert table["header"] == [
        "Component",
        "Namespace",
        "Name",
        {"text": "Definition", "align": "left"},
        "Access per Hour",
    ]
    assert len(table["rows"]) == 1
    assert table["rows"][0] == ["test_set"] + ["N/A"] * 4
