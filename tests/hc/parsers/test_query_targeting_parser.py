from x_ray.healthcheck.parsers.query_targeting_parser import QueryTargetingParser  # type: ignore

QT_INFOS = [
    {
        "set_name": "shard02",
        "host": "localhost:30022",
        "query_targeting": {"scanned/returned": 0.9633964673334752, "scanned_obj/returned": 0.96451372632475},
    },
    {
        "set_name": "shard02",
        "host": "localhost:30023",
        "query_targeting": {"scanned/returned": 0.9612366104571004, "scanned_obj/returned": 0.9623501962032028},
    },
]


def test_query_targeting_parser():
    parser = QueryTargetingParser()
    result = parser.parse(QT_INFOS)
    assert len(result) == 1
    table = result[0]
    assert table["type"] == "table"
    assert table["caption"] == "Query Targeting"
    assert table["header"] == [
        "Component",
        "Host",
        "Scanned / Returned",
        "Scanned Objects / Returned",
    ]
    assert len(table["rows"]) == 2
    assert table["rows"][0] == ["shard02", "localhost:30022", "0.96", "0.96"]
    assert table["rows"][1] == ["shard02", "localhost:30023", "0.96", "0.96"]


def test_query_targeting_parser_no_data():
    parser = QueryTargetingParser()
    result = parser.parse(
        [
            {
                "set_name": "shard02",
                "host": "localhost:30022",
                "query_targeting": None,
            }
        ]
    )
    assert len(result) == 1
    table = result[0]
    assert table["type"] == "table"
    assert table["caption"] == "Query Targeting"
    assert table["header"] == [
        "Component",
        "Host",
        "Scanned / Returned",
        "Scanned Objects / Returned",
    ]
    assert len(table["rows"]) == 1
    assert table["rows"][0] == ["shard02", "localhost:30022", "N/A", "N/A"]
