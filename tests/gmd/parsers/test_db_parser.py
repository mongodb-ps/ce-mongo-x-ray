from x_ray.gmd_analysis.parsers.db_parser import DBParser  # type: ignore

GMD_SHARDED_DBS = [
    {
        "_id": "foo",
        "primary": "shard02",
        "partitioned": True,
    },
    {
        "_id": "test",
        "primary": "shard01",
        "partitioned": False,
    },
    {
        "_id": "test1",
        "primary": "shard01",
        "partitioned": False,
    },
]

GMD_DBS = {
    "databases": [
        {"name": "admin", "sizeOnDisk": 409600, "empty": False, "shards": {"config": 409600}},
        {
            "name": "config",
            "sizeOnDisk": 3981312,
            "empty": False,
            "shards": {"shard02": 1003520, "shard01": 917504, "config": 2060288},
        },
        {
            "name": "foo",
            "sizeOnDisk": 4329472,
            "empty": False,
            "shards": {"shard02": 3239936, "shard01": 1089536},
        },
        {"name": "test", "sizeOnDisk": 139264, "empty": False, "shards": {"shard01": 139264}},
        {"name": "test1", "sizeOnDisk": 81920, "empty": False, "shards": {"shard01": 81920}},
    ]
}


def test_db_parser_sharded():
    parser = DBParser()
    result = parser.parse({"databases": GMD_DBS, "sharded_databases": GMD_SHARDED_DBS})
    assert len(result) == 1
    dbs_table = result[0]
    assert dbs_table["type"] == "table"
    assert dbs_table["caption"] == "Databases"
    assert dbs_table["header"] == [
        "Database Name",
        {"text": "Storage Size", "align": "left"},
        "Is Partitioned",
        "Primary Database",
    ]
    assert dbs_table["rows"][0][0] == "foo"
    assert dbs_table["rows"][0][1].startswith("4.13 MB")
    assert dbs_table["rows"][0][2] == True
    assert dbs_table["rows"][0][3] == "shard02"
    assert dbs_table["rows"][1][0] == "test"
    assert dbs_table["rows"][1][1].startswith("136.00 KB")
    assert dbs_table["rows"][1][2] == False
    assert dbs_table["rows"][1][3] == "shard01"
    assert dbs_table["rows"][2][0] == "test1"
    assert dbs_table["rows"][2][1].startswith("80.00 KB")
    assert dbs_table["rows"][2][2] == False
    assert dbs_table["rows"][2][3] == "shard01"


def test_db_parser_non_sharded():
    parser = DBParser()
    result = parser.parse({"databases": GMD_DBS})
    assert len(result) == 1
    dbs_table = result[0]
    assert dbs_table["type"] == "table"
    assert dbs_table["caption"] == "Databases"
    assert dbs_table["header"] == [
        "Database Name",
        {"text": "Storage Size", "align": "left"},
        "Is Partitioned",
        "Primary Database",
    ]
    assert dbs_table["rows"][0][0] == "foo"
    assert dbs_table["rows"][0][1].startswith("4.13 MB")
    assert dbs_table["rows"][0][2] == "N/A"
    assert dbs_table["rows"][0][3] == "N/A"
    assert dbs_table["rows"][1][0] == "test"
    assert dbs_table["rows"][1][1].startswith("136.00 KB")
    assert dbs_table["rows"][1][2] == "N/A"
    assert dbs_table["rows"][1][3] == "N/A"
    assert dbs_table["rows"][2][0] == "test1"
    assert dbs_table["rows"][2][1].startswith("80.00 KB")
    assert dbs_table["rows"][2][2] == "N/A"
    assert dbs_table["rows"][2][3] == "N/A"
