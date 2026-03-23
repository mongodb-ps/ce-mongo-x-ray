from bson import json_util  # type: ignore
from x_ray.healthcheck.parsers.shard_key_parser import ShardKeyParser  # type: ignore

SHARD_KEY_INFOS = json_util.loads(
    """{
    "rawResult": {
    "shardedCollections": [
      {
        "_id": "foo.bar",
        "key": {
          "_id": "hashed"
        },
        "unique": false,
        "noBalance": false
      },
      {
        "_id": "foo.bar2",
        "key": {
          "x": 1
        },
        "unique": false,
        "noBalance": false
      },
      {
        "_id": "foo.bar3",
        "key": {
          "_id": 1
        },
        "unique": false,
        "noBalance": false
      }
    ],
    "stats": {
      "foo.bar": {
        "shard01": {
          "size": 145058,
          "count": 5002,
          "avgObjSize": 29,
          "storageSize": 241664,
          "nindexes": 4,
          "totalIndexSize": 806912,
          "totalSize": 1048576
        },
        "shard02": {
          "size": 144942,
          "count": 4998,
          "avgObjSize": 29,
          "storageSize": 245760,
          "nindexes": 4,
          "totalIndexSize": 811008,
          "totalSize": 1056768
        }
      },
      "foo.bar2": {
        "shard02": {
          "size": 290000,
          "count": 10000,
          "avgObjSize": 29,
          "storageSize": 446464,
          "nindexes": 5,
          "totalIndexSize": 1515520,
          "totalSize": 1961984
        }
      },
      "foo.bar3": {
        "shard02": {
          "size": 29,
          "count": 1,
          "avgObjSize": 29,
          "storageSize": 20480,
          "nindexes": 1,
          "totalIndexSize": 20480,
          "totalSize": 40960
        }
      }
    }
  }
}
"""
)


def test_shard_key_parser():
    parser = ShardKeyParser()
    output = parser.parse(SHARD_KEY_INFOS["rawResult"])
    assert len(output) == 1
    table = output[0]
    assert table["type"] == "table"
    assert table["caption"] == "Shard Keys"
    assert table["header"] == [
        "Namespace",
        "Shard Key",
        {"text": "Data Size", "align": "left"},
        {"text": "Storage Size", "align": "left"},
        {"text": "Index Size", "align": "left"},
        {"text": "Docs Count", "align": "left"},
    ]
    assert len(table["rows"]) == 3
    assert table["rows"][0][0] == "foo.bar"
    assert table["rows"][0][1] == '{"\\_id": "hashed"}'
    assert table["rows"][0][2].startswith("283.20 KB")
    assert table["rows"][0][3].startswith("476.00 KB")
    assert table["rows"][0][4].startswith("1.54 MB")
    assert table["rows"][0][5].startswith("10000")

    assert table["rows"][1][0] == "foo.bar2"
    assert table["rows"][1][1] == '{"x": 1}'
    assert table["rows"][1][2].startswith("283.20 KB")
    assert table["rows"][1][3].startswith("436.00 KB")
    assert table["rows"][1][4].startswith("1.45 MB")
    assert table["rows"][1][5].startswith("10000")

    assert table["rows"][2][0] == "foo.bar3"
    assert table["rows"][2][1] == '{"\\_id": 1}'
    assert table["rows"][2][2].startswith("29.00 B")
    assert table["rows"][2][3].startswith("20.00 KB")
    assert table["rows"][2][4].startswith("20.00 KB")
    assert table["rows"][2][5].startswith("1")


def test_shard_key_parser_with_none():
    parser = ShardKeyParser()
    output = parser.parse(None)
    assert len(output) == 1
    table = output[0]
    assert table["type"] == "table"
    assert table["caption"] == "Shard Keys"
    assert table["header"] == [
        "Namespace",
        "Shard Key",
        {"text": "Data Size", "align": "left"},
        {"text": "Storage Size", "align": "left"},
        {"text": "Index Size", "align": "left"},
        {"text": "Docs Count", "align": "left"},
    ]
    assert len(table["rows"]) == 1
    assert table["rows"][0][0] == "N/A"
    assert table["rows"][0][1] == "N/A"
    assert table["rows"][0][2] == "N/A"
    assert table["rows"][0][3] == "N/A"
    assert table["rows"][0][4] == "N/A"
    assert table["rows"][0][5] == "N/A"
