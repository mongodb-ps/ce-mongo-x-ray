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

DB_STATS = {
    "admin": {"db": "admin", "dataSize": 4, "collections": 3, "views": 0, "objects": 5, "indexes": 5},
    "config": {"db": "config", "dataSize": 5, "collections": 8, "views": 0, "objects": 10, "indexes": 10},
    "foo": {"db": "foo", "dataSize": 6, "collections": 12, "views": 0, "objects": 15, "indexes": 15},
    "test": {"db": "test", "dataSize": 7, "collections": 2, "views": 0, "objects": 3, "indexes": 3},
    "test1": {"db": "test1", "dataSize": 8, "collections": 1, "views": 0, "objects": 1, "indexes": 1},
}


def test_db_parser_sharded():
    parser = DBParser()
    result = parser.parse(
        {
            "databases": GMD_DBS,
            "sharded_databases": GMD_SHARDED_DBS,
            "db_stats": DB_STATS,
        }
    )
    assert len(result) == 2
    dbs_table = result[0]
    assert dbs_table["type"] == "table"
    assert dbs_table["caption"] == "Databases"
    assert dbs_table["header"] == [
        {"text": "Database Name", "width": "*"},
        {"text": "Data Size", "align": "left", "width": "120px"},
        {"text": "Storage Size", "align": "left", "width": "150px"},
        {"text": "Is Sharded", "width": "100px"},
        {"text": "Primary Shard", "width": "120px"},
        {"text": "# Colls", "width": "100px"},
        {"text": "# Views", "width": "100px"},
        {"text": "# Objects", "width": "100px"},
        {"text": "# Indexes", "width": "100px"},
    ]
    assert dbs_table["rows"][0][0] == "admin"
    assert dbs_table["rows"][0][1].startswith("4.00 MB")
    assert dbs_table["rows"][0][2].startswith("400.00 KB")
    assert dbs_table["rows"][0][3] == False
    assert dbs_table["rows"][0][4] == "N/A"
    assert dbs_table["rows"][0][5] == 3
    assert dbs_table["rows"][0][6] == 0
    assert dbs_table["rows"][0][7] == 5
    assert dbs_table["rows"][0][8] == 5

    assert dbs_table["rows"][1][0] == "config"
    assert dbs_table["rows"][1][1].startswith("5.00 MB")
    assert dbs_table["rows"][1][2].startswith("3.80 MB")
    assert dbs_table["rows"][1][3] == False
    assert dbs_table["rows"][1][4] == "N/A"
    assert dbs_table["rows"][1][5] == 8
    assert dbs_table["rows"][1][6] == 0
    assert dbs_table["rows"][1][7] == 10
    assert dbs_table["rows"][1][8] == 10

    assert dbs_table["rows"][2][0] == "foo"
    assert dbs_table["rows"][2][1].startswith("6.00 MB")
    assert dbs_table["rows"][2][2].startswith("4.13 MB")
    assert dbs_table["rows"][2][3] == True
    assert dbs_table["rows"][2][4] == "shard02"
    assert dbs_table["rows"][2][5] == 12
    assert dbs_table["rows"][2][6] == 0
    assert dbs_table["rows"][2][7] == 15
    assert dbs_table["rows"][2][8] == 15

    assert dbs_table["rows"][3][0] == "test"
    assert dbs_table["rows"][3][1].startswith("7.00 MB")
    assert dbs_table["rows"][3][2].startswith("136.00 KB")
    assert dbs_table["rows"][3][3] == False
    assert dbs_table["rows"][3][4] == "shard01"
    assert dbs_table["rows"][3][5] == 2
    assert dbs_table["rows"][3][6] == 0
    assert dbs_table["rows"][3][7] == 3
    assert dbs_table["rows"][3][8] == 3

    assert dbs_table["rows"][4][0] == "test1"
    assert dbs_table["rows"][4][1].startswith("8.00 MB")
    assert dbs_table["rows"][4][2].startswith("80.00 KB")
    assert dbs_table["rows"][4][3] == False
    assert dbs_table["rows"][4][4] == "shard01"
    assert dbs_table["rows"][4][5] == 1
    assert dbs_table["rows"][4][6] == 0
    assert dbs_table["rows"][4][7] == 1
    assert dbs_table["rows"][4][8] == 1

    # SUM row
    assert dbs_table["rows"][5][0] == "**(SUM)**"
    assert dbs_table["rows"][5][1].startswith("30.00 MB")
    assert dbs_table["rows"][5][2].startswith("8.53 MB")
    assert dbs_table["rows"][5][3] == "N/A"
    assert dbs_table["rows"][5][4] == "N/A"
    assert dbs_table["rows"][5][5] == 26
    assert dbs_table["rows"][5][6] == 0
    assert dbs_table["rows"][5][7] == 34
    assert dbs_table["rows"][5][8] == 34

    dbs_data = result[1]
    assert dbs_data["type"] == "chart"
    assert len(dbs_data["data"]) == 5
    assert dbs_data["data"][0]["name"] == "admin"
    assert dbs_data["data"][0]["storageSize"] == 409600
    assert dbs_data["data"][1]["name"] == "config"
    assert dbs_data["data"][1]["storageSize"] == 3981312
    assert dbs_data["data"][2]["name"] == "foo"
    assert dbs_data["data"][2]["storageSize"] == 4329472
    assert dbs_data["data"][3]["name"] == "test"
    assert dbs_data["data"][3]["storageSize"] == 139264
    assert dbs_data["data"][4]["name"] == "test1"
    assert dbs_data["data"][4]["storageSize"] == 81920


def test_db_parser_non_sharded():
    parser = DBParser()
    result = parser.parse({"databases": GMD_DBS, "db_stats": DB_STATS})
    assert len(result) == 2
    dbs_table = result[0]
    assert dbs_table["type"] == "table"
    assert dbs_table["caption"] == "Databases"
    assert dbs_table["header"] == [
        {"text": "Database Name", "width": "*"},
        {"text": "Data Size", "align": "left", "width": "120px"},
        {"text": "Storage Size", "align": "left", "width": "150px"},
        {"text": "Is Sharded", "width": "100px"},
        {"text": "Primary Shard", "width": "120px"},
        {"text": "# Colls", "width": "100px"},
        {"text": "# Views", "width": "100px"},
        {"text": "# Objects", "width": "100px"},
        {"text": "# Indexes", "width": "100px"},
    ]
    assert dbs_table["rows"][0][0] == "admin"
    assert dbs_table["rows"][0][1].startswith("4.00 MB")
    assert dbs_table["rows"][0][2].startswith("400.00 KB")
    assert dbs_table["rows"][0][3] == "N/A"
    assert dbs_table["rows"][0][4] == "N/A"
    assert dbs_table["rows"][0][5] == 3
    assert dbs_table["rows"][0][6] == 0
    assert dbs_table["rows"][0][7] == 5
    assert dbs_table["rows"][0][8] == 5

    assert dbs_table["rows"][1][0] == "config"
    assert dbs_table["rows"][1][1].startswith("5.00 MB")
    assert dbs_table["rows"][1][2].startswith("3.80 MB")
    assert dbs_table["rows"][1][3] == "N/A"
    assert dbs_table["rows"][1][4] == "N/A"
    assert dbs_table["rows"][1][5] == 8
    assert dbs_table["rows"][1][6] == 0
    assert dbs_table["rows"][1][7] == 10
    assert dbs_table["rows"][1][8] == 10

    assert dbs_table["rows"][2][0] == "foo"
    assert dbs_table["rows"][2][1].startswith("6.00 MB")
    assert dbs_table["rows"][2][2].startswith("4.13 MB")
    assert dbs_table["rows"][2][3] == "N/A"
    assert dbs_table["rows"][2][4] == "N/A"
    assert dbs_table["rows"][2][5] == 12
    assert dbs_table["rows"][2][6] == 0
    assert dbs_table["rows"][2][7] == 15
    assert dbs_table["rows"][2][8] == 15

    assert dbs_table["rows"][3][0] == "test"
    assert dbs_table["rows"][3][1].startswith("7.00 MB")
    assert dbs_table["rows"][3][2].startswith("136.00 KB")
    assert dbs_table["rows"][3][3] == "N/A"
    assert dbs_table["rows"][3][4] == "N/A"
    assert dbs_table["rows"][3][5] == 2
    assert dbs_table["rows"][3][6] == 0
    assert dbs_table["rows"][3][7] == 3
    assert dbs_table["rows"][3][8] == 3

    assert dbs_table["rows"][4][0] == "test1"
    assert dbs_table["rows"][4][1].startswith("8.00 MB")
    assert dbs_table["rows"][4][2].startswith("80.00 KB")
    assert dbs_table["rows"][4][3] == "N/A"
    assert dbs_table["rows"][4][4] == "N/A"
    assert dbs_table["rows"][4][5] == 1
    assert dbs_table["rows"][4][6] == 0
    assert dbs_table["rows"][4][7] == 1
    assert dbs_table["rows"][4][8] == 1

    # SUM row
    assert dbs_table["rows"][5][0] == "**(SUM)**"
    assert dbs_table["rows"][5][1].startswith("30.00 MB")
    assert dbs_table["rows"][5][2].startswith("8.53 MB")
    assert dbs_table["rows"][5][3] == "N/A"
    assert dbs_table["rows"][5][4] == "N/A"
    assert dbs_table["rows"][5][5] == 26
    assert dbs_table["rows"][5][6] == 0
    assert dbs_table["rows"][5][7] == 34
    assert dbs_table["rows"][5][8] == 34

    dbs_data = result[1]
    assert dbs_data["type"] == "chart"
    assert len(dbs_data["data"]) == 5
    assert dbs_data["data"][0]["name"] == "admin"
    assert dbs_data["data"][0]["dataSize"] == 4
    assert dbs_data["data"][0]["storageSize"] == 409600
