from x_ray.gmd_analysis.parsers.coll_stats_parser import CollStatsParser  # type: ignore

STATS_DATA: list[dict] = [
    {
        "ns": "foo.unsharded_collection",
        "count": 100000,
        "size": 1024,
        "avgObjSize": 64,
        "storageSize": 512,
        "totalIndexSize": 1,
        "wiredTiger": {
            "block-manager": {
                "file bytes available for reuse": 256 * 1024**2,
                "file size in bytes": 512 * 1024**2,
            },
            "cache": {
                "bytes currently in the cache": 100 * 1024**2,
            },
        },
    },
    {
        "ns": "foo.sharded_collection",
        "count": 100000,
        "size": 1024,
        "avgObjSize": 64,
        "storageSize": 512,
        "totalIndexSize": 512,
        "wiredTiger": {
            "block-manager": {
                "file bytes available for reuse": 256 * 1024**2,
                "file size in bytes": 512 * 1024**2,
            },
            "cache": {"bytes currently in the cache": 200 * 1024**2},
        },
        "sharded": True,
        "shards": {
            "shard1": {
                "count": 49000,
                "size": 512,
                "avgObjSize": 60,
                "storageSize": 250,
                "totalIndexSize": 250,
                "wiredTiger": {
                    "block-manager": {
                        "file bytes available for reuse": 128 * 1024**2,
                        "file size in bytes": 250 * 1024**2,
                    },
                    "cache": {"bytes currently in the cache": 100 * 1024**2},
                },
            },
            "shard2": {
                "count": 51000,
                "size": 512,
                "avgObjSize": 68,
                "storageSize": 262,
                "totalIndexSize": 262,
                "wiredTiger": {
                    "block-manager": {
                        "file bytes available for reuse": 128 * 1024**2,
                        "file size in bytes": 262 * 1024**2,
                    },
                    "cache": {"bytes currently in the cache": 100 * 1024**2},
                },
            },
        },
    },
]


def test_coll_stats_parser() -> None:
    parser = CollStatsParser()
    result = parser.parse(STATS_DATA)
    assert len(result) == 2
    table_item = result[0]
    assert table_item["type"] == "table"
    assert table_item["caption"] == "Storage Stats"
    assert table_item["header"] == [
        "NS",
        {"text": "Count", "align": "left"},
        {"text": "Data Size", "align": "left"},
        {"text": "Storage Size", "align": "left"},
        {"text": "Avg Object Size", "align": "left"},
        {"text": "Total Index Size", "align": "left"},
        {"text": "Fragmentation Ratio", "align": "left"},
        {"text": "Cached", "align": "left"},
    ]
    assert len(table_item["rows"]) == 2
    assert table_item["rows"][0][0] == "foo.unsharded\\_collection"
    assert table_item["rows"][0][1] == "100000"
    assert table_item["rows"][0][2] == "1.00 GB"
    assert table_item["rows"][0][3] == "512.00 MB"
    assert table_item["rows"][0][4] == "64.00 B"
    assert table_item["rows"][0][5] == "1.00 MB"
    assert table_item["rows"][0][6] == "50.00%"
    assert table_item["rows"][0][7] == "100.00 MB / 9.77%"
    assert table_item["rows"][1][0] == "foo.sharded\\_collection"
    assert table_item["rows"][1][1] == "100000<pre>shard1: 49000<br>shard2: 51000</pre>"
    assert table_item["rows"][1][2] == "1.00 GB<pre>shard1: 512.00 MB<br>shard2: 512.00 MB</pre>"
    assert table_item["rows"][1][3] == "512.00 MB<pre>shard1: 250.00 MB<br>shard2: 262.00 MB</pre>"
    assert table_item["rows"][1][4] == "64.00 B<pre>shard1: 60.00 B<br>shard2: 68.00 B</pre>"
    assert table_item["rows"][1][5] == "512.00 MB<pre>shard1: 250.00 MB<br>shard2: 262.00 MB</pre>"
    assert table_item["rows"][1][6] == "50.00%<pre>shard1: 51.20%<br>shard2: 48.85%</pre>"
    assert (
        table_item["rows"][1][7]
        == "200.00 MB / 19.53%<pre>shard1: 100.00 MB / 19.53%<br>shard2: 100.00 MB / 19.53%</pre>"
    )
    chart_item = result[1]
    assert chart_item["type"] == "chart"
    assert chart_item["data"]["foo.unsharded_collection"]["size"] == 1024**3
    assert chart_item["data"]["foo.unsharded_collection"]["index_size"] == 1024**2
    assert chart_item["data"]["foo.sharded_collection"]["size"] == 1024**3
    assert chart_item["data"]["foo.sharded_collection"]["index_size"] == 512 * 1024**2
