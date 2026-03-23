from x_ray.healthcheck.parsers.cache_parser import CacheParser  # type: ignore

CACHES: list = [
    {
        "set_name": "shard01",
        "host": "localhost:30018",
        "cache": {
            "cacheSize": 1073741824,
            "inCacheSize": 17934433,
            "readInto": 0.0,
            "writtenFrom": 0.0,
            "forUpdates": -785,
            "dirty": 0,
            "intervalMillis": 5042.0,
        },
    },
    {
        "set_name": "shard01",
        "host": "localhost:30019",
        "cache": {
            "cacheSize": 1073741824,
            "inCacheSize": 13997201,
            "readInto": 0.0,
            "writtenFrom": 0.0,
            "forUpdates": 312,
            "dirty": 4618,
            "intervalMillis": 5048.0,
        },
    },
    {
        "set_name": "shard01",
        "host": "localhost:30020",
        "cache": {
            "cacheSize": 1073741824,
            "inCacheSize": 17967403,
            "readInto": 0.0,
            "writtenFrom": 0.0,
            "forUpdates": -785,
            "dirty": 0,
            "intervalMillis": 5053.0,
        },
    },
]


def test_cache_parser() -> None:
    parser = CacheParser()
    result = parser.parse(CACHES)
    assert len(result) == 2
    assert result[0]["type"] == "table"
    assert result[0]["caption"] == "WiredTiger Cache"
    assert result[0]["header"] == [
        "Component",
        "Host",
        "Cache Size",
        "In-Cache Size",
        "Bytes Dirty",
        "Read Into",
        "Written From",
    ]
    assert len(result[0]["rows"]) == 3
    assert result[0]["rows"][0] == [
        "shard01",
        "localhost:30018",
        "1.00 GB",
        "17.10 MB",
        "0.00 B",
        "0.00 B/s",
        "0.00 B/s",
    ]
    assert result[0]["rows"][1] == [
        "shard01",
        "localhost:30019",
        "1.00 GB",
        "13.35 MB",
        "4.51 KB",
        "0.00 B/s",
        "0.00 B/s",
    ]
    assert result[0]["rows"][2] == [
        "shard01",
        "localhost:30020",
        "1.00 GB",
        "17.14 MB",
        "0.00 B",
        "0.00 B/s",
        "0.00 B/s",
    ]
    assert result[1]["type"] == "chart"
    assert len(result[1]["data"]) == 3
    assert result[1]["data"]["shard01/localhost:30018"] == {
        "cacheSize": 1073741824,
        "inCacheSize": 17934433,
        "readInto": 0.0,
        "forUpdates": -785,
        "dirty": 0,
        "writtenFrom": 0.0,
    }
    assert result[1]["data"]["shard01/localhost:30019"] == {
        "cacheSize": 1073741824,
        "inCacheSize": 13997201,
        "readInto": 0.0,
        "forUpdates": 312,
        "dirty": 4618,
        "writtenFrom": 0.0,
    }
    assert result[1]["data"]["shard01/localhost:30020"] == {
        "cacheSize": 1073741824,
        "inCacheSize": 17967403,
        "readInto": 0.0,
        "forUpdates": -785,
        "dirty": 0,
        "writtenFrom": 0.0,
    }


def test_cache_parser_no_data() -> None:
    parser = CacheParser()
    result = parser.parse(
        [
            {
                "set_name": "shard01",
                "host": "localhost:30018",
                "cache": None,
            }
        ]
    )
    assert len(result) == 2
    assert result[0]["type"] == "table"
    assert result[0]["caption"] == "WiredTiger Cache"
    assert result[0]["header"] == [
        "Component",
        "Host",
        "Cache Size",
        "In-Cache Size",
        "Bytes Dirty",
        "Read Into",
        "Written From",
    ]
    assert len(result[0]["rows"]) == 1
    assert result[0]["rows"][0] == ["shard01", "localhost:30018", "N/A", "N/A", "N/A", "N/A", "N/A"]
    assert result[1]["type"] == "chart"
    assert len(result[1]["data"]) == 1
    assert result[1]["data"]["shard01/localhost:30018"] == {
        "cacheSize": 0,
        "inCacheSize": 0,
        "readInto": 0,
        "forUpdates": 0,
        "dirty": 0,
        "writtenFrom": 0,
    }
