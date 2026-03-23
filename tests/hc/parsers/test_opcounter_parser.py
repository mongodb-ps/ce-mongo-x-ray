from x_ray.healthcheck.parsers.opcounter_parser import OpcounterParser  # type: ignore

OPCOUNTER_INFOS = [
    {
        "set_name": "shard01",
        "host": "localhost:30018",
        "op_counters": {
            "set_name": "shard01",
            "host": "localhost:30018",
            "insert": 0,
            "query": 0,
            "update": 0,
            "delete": 0,
            "command": 23,
            "getmore": 0,
        },
    },
    {
        "set_name": "shard01",
        "host": "localhost:30019",
        "op_counters": {
            "set_name": "shard01",
            "host": "localhost:30019",
            "insert": 0,
            "query": 0,
            "update": 0,
            "delete": 0,
            "command": 22,
            "getmore": 3,
        },
    },
    {
        "set_name": "shard02",
        "host": "localhost:30021",
        "op_counters": {
            "set_name": "shard02",
            "host": "localhost:30021",
            "insert": 0,
            "query": 0,
            "update": 0,
            "delete": 0,
            "command": 32,
            "getmore": 2,
        },
    },
]


def test_opcounter_parser():
    parser = OpcounterParser()
    result = parser.parse(OPCOUNTER_INFOS)
    assert len(result) == 2
    table = result[0]
    assert table["type"] == "table"
    assert table["caption"] == "Operation Counters"
    assert table["header"] == [
        "Component",
        "Host",
        "Inserts/s",
        "Queries/s",
        "Updates/s",
        "Deletes/s",
        "Commands/s",
        "Getmores/s",
    ]
    assert len(table["rows"]) == 3
    assert table["rows"][0][0] == "shard01"
    assert table["rows"][0][1] == "localhost:30018"
    assert table["rows"][0][2] == 0
    assert table["rows"][0][3] == 0
    assert table["rows"][0][4] == 0
    assert table["rows"][0][5] == 0
    assert table["rows"][0][6] == 23
    assert table["rows"][0][7] == 0

    assert table["rows"][1][0] == "shard01"
    assert table["rows"][1][1] == "localhost:30019"
    assert table["rows"][1][2] == 0
    assert table["rows"][1][3] == 0
    assert table["rows"][1][4] == 0
    assert table["rows"][1][5] == 0
    assert table["rows"][1][6] == 22
    assert table["rows"][1][7] == 3

    assert table["rows"][2][0] == "shard02"
    assert table["rows"][2][1] == "localhost:30021"
    assert table["rows"][2][2] == 0
    assert table["rows"][2][3] == 0
    assert table["rows"][2][4] == 0
    assert table["rows"][2][5] == 0
    assert table["rows"][2][6] == 32
    assert table["rows"][2][7] == 2

    data = result[1]
    assert data["type"] == "chart"
    assert data["data"] == {
        "shard01/localhost:30018": {
            "insert": 0,
            "query": 0,
            "update": 0,
            "delete": 0,
            "command": 23,
            "getmore": 0,
        },
        "shard01/localhost:30019": {
            "insert": 0,
            "query": 0,
            "update": 0,
            "delete": 0,
            "command": 22,
            "getmore": 3,
        },
        "shard02/localhost:30021": {
            "insert": 0,
            "query": 0,
            "update": 0,
            "delete": 0,
            "command": 32,
            "getmore": 2,
        },
    }


def test_opcounter_parser_no_data():
    parser = OpcounterParser()
    result = parser.parse(
        [
            {
                "set_name": "shard01",
                "host": "localhost:30018",
                "op_counters": None,
            }
        ]
    )
    assert len(result) == 2
    table = result[0]
    assert table["type"] == "table"
    assert table["caption"] == "Operation Counters"
    assert table["header"] == [
        "Component",
        "Host",
        "Inserts/s",
        "Queries/s",
        "Updates/s",
        "Deletes/s",
        "Commands/s",
        "Getmores/s",
    ]
    assert len(table["rows"]) == 1
    assert table["rows"][0][0] == "shard01"
    assert table["rows"][0][1] == "localhost:30018"
    assert table["rows"][0][2] == "N/A"
    assert table["rows"][0][3] == "N/A"
    assert table["rows"][0][4] == "N/A"
    assert table["rows"][0][5] == "N/A"
    assert table["rows"][0][6] == "N/A"
    assert table["rows"][0][7] == "N/A"
    data = result[1]
    assert data["type"] == "chart"
    assert data["data"] == {
        "shard01/localhost:30018": {
            "insert": 0,
            "query": 0,
            "update": 0,
            "delete": 0,
            "command": 0,
            "getmore": 0,
        }
    }
