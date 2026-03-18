from bson import json_util
from x_ray.gmd_analysis.parsers.sharded_db_parser import ShardedDBParser  # type: ignore

GMD_ITEM = json_util.loads(
    """{
    "section": "shard_info",
    "subsection": "sharded_databases",
    "output": [
        {
            "_id": "foo",
            "primary": "shard02",
            "partitioned": true,
            "version": {
                "uuid": {
                    "$binary": {
                        "base64": "fwLsAAJBRWCslVjXfqvMng==",
                        "subType": "04"
                    }
                },
                "timestamp": {
                    "$timestamp": {
                        "t": 1754906345,
                        "i": 1
                    }
                },
                "lastMod": {
                    "$numberInt": "1"
                }
            },
            "collections": [
                {
                    "_id": "foo.bar",
                    "key": {
                        "_id": "hashed"
                    },
                    "unique": false,
                    "distribution": [
                        {
                            "shard": "shard01",
                            "nChunks": {
                                "$numberInt": "2"
                            }
                        },
                        {
                            "shard": "shard02",
                            "nChunks": {
                                "$numberInt": "2"
                            }
                        }
                    ],
                    "tags": []
                },
                {
                    "_id": "foo.bar2",
                    "key": {
                        "x": {
                            "$numberInt": "1"
                        }
                    },
                    "unique": false,
                    "distribution": [
                        {
                            "shard": "shard02",
                            "nChunks": {
                                "$numberInt": "1"
                            }
                        }
                    ],
                    "tags": []
                },
                {
                    "_id": "foo.bar3",
                    "key": {
                        "_id": {
                            "$numberInt": "1"
                        }
                    },
                    "unique": false,
                    "distribution": [
                        {
                            "shard": "shard02",
                            "nChunks": {
                                "$numberInt": "1"
                            }
                        }
                    ],
                    "tags": []
                }
            ]
        },
        {
            "_id": "test",
            "primary": "shard01",
            "partitioned": false,
            "version": {
                "uuid": {
                    "$binary": {
                        "base64": "wx7n3YzlT2eAPF8QbOLnYw==",
                        "subType": "04"
                    }
                },
                "timestamp": {
                    "$timestamp": {
                        "t": 1755249463,
                        "i": 2
                    }
                },
                "lastMod": {
                    "$numberInt": "1"
                }
            }
        },
        {
            "_id": "test1",
            "primary": "shard01",
            "partitioned": false,
            "version": {
                "uuid": {
                    "$binary": {
                        "base64": "j8qZx2VhQLCYJRGkz2Ri+w==",
                        "subType": "04"
                    }
                },
                "timestamp": {
                    "$timestamp": {
                        "t": 1755249833,
                        "i": 1
                    }
                },
                "lastMod": {
                    "$numberInt": "1"
                }
            }
        }
    ]
}"""
)


def test_sharded_db_parser():
    parser = ShardedDBParser()
    result = parser.parse(GMD_ITEM["output"])
    assert len(result) == 2
    sharded_db_table = result[0]
    sharded_coll_table = result[1]
    assert sharded_db_table["type"] == "table"
    assert sharded_db_table["caption"] == "Sharded Databases"
    assert sharded_db_table["header"] == ["Database Name", "Primary Database", "Is Partitioned"]
    assert sharded_db_table["rows"] == [
        ["foo", "shard02", True],
        ["test", "shard01", False],
        ["test1", "shard01", False],
    ]
    assert sharded_coll_table["type"] == "table"
    assert sharded_coll_table["caption"] == "Sharded Collections"
    assert sharded_coll_table["header"] == ["Namespace", "Shard Key", "Is Unique", "Chunk Distribution"]
    assert sharded_coll_table["rows"] == [
        ["foo.bar", '{"\\_id": "hashed"}', False, "<pre>shard01: 2<br/>shard02: 2</pre>"],
        ["foo.bar2", '{"x": 1}', False, "<pre>shard02: 1</pre>"],
        ["foo.bar3", '{"\\_id": 1}', False, "<pre>shard02: 1</pre>"],
    ]
