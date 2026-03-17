from x_ray.healthcheck.parsers.coll_overview_parser import CollOverviewParser  # type: ignore

STATS: list = [
    {
        "ns": "foo.bar",
        "storageStats": {
            "size": 145058,
            "count": 5002,
            "avgObjSize": 29,
            "storageSize": 237568,
            "freeStorageSize": 118784,
            "capped": False,
            "nindexes": 4,
            "indexBuilds": [],
            "totalIndexSize": 851968,
            "totalSize": 1089536,
            "indexSizes": {"_id_": 368640, "_id_hashed": 372736, "$**_1": 102400, "pos_2d": 8192},
            "scaleFactor": 1,
        },
    },
    {
        "ns": "test.test",
        "storageStats": {
            "size": 35,
            "count": 1,
            "avgObjSize": 35,
            "storageSize": 20480,
            "freeStorageSize": 0,
            "capped": False,
            "indexBuilds": [],
            "totalIndexSize": 20480,
            "totalSize": 40960,
            "indexSizes": {"_id_": 20480},
            "scaleFactor": 1,
        },
    },
]


def test_coll_overview_parser() -> None:
    parser = CollOverviewParser()
    result = parser.parse(STATS)
    assert len(result) == 2
    assert result[0]["type"] == "table"
    assert result[0]["caption"] == "Storage Stats"
    assert result[0]["header"] == [
        "Namespace",
        "Size",
        "Storage Size",
        "Avg Object Size",
        "Total Index Size",
        "Index / Storage",
    ]
    assert result[0]["rows"][0] == [
        "foo.bar",
        "141.66 KB",
        "232.00 KB",
        "29.00 B",
        "832.00 KB",
        "358.62%",
    ]
    assert result[0]["rows"][1] == [
        "test.test",
        "35.00 B",
        "20.00 KB",
        "35.00 B",
        "20.00 KB",
        "100.00%",
    ]
