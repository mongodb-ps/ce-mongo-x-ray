from x_ray.healthcheck.parsers.conn_parser import ConnParser  # type: ignore

CONNS = [
    {
        "set_name": "testSet",
        "host": "testHost",
        "connections": {
            "current": 37,
            "available": 167,
            "totalCreated": 1920,
            "active": 13,
            "threaded": 37,
            "exhaustIsMaster": 8,
            "exhaustHello": 0,
            "awaitingTopologyChanges": 199,
        },
    },
    {
        "set_name": "testSet2",
        "host": "testHost2",
        "connections": {
            "current": 26,
            "available": 178,
            "totalCreated": 2135,
            "active": 10,
            "threaded": 26,
            "exhaustIsMaster": 8,
            "exhaustHello": 0,
            "awaitingTopologyChanges": 192,
        },
    },
]


def test_conn_parser():
    parser = ConnParser()
    output = parser.parse(CONNS)
    assert len(output) == 2
    assert output[0]["type"] == "table"
    assert output[0]["caption"] == "Connections"
    assert output[0]["header"] == [
        "Component",
        "Host",
        "Current",
        "Available",
        "Active",
        "Created",
        "Rejected",
        "Threaded",
    ]
    assert len(output[0]["rows"]) == 2
    assert output[0]["rows"][0][0] == "testSet"
    assert output[0]["rows"][0][1] == "testHost"
    assert output[0]["rows"][0][2] == "37"
    assert output[0]["rows"][0][3] == "167"
    assert output[0]["rows"][0][4] == "13"
    assert output[0]["rows"][0][5] == "1920"
    assert output[0]["rows"][0][6] == "N/A"
    assert output[0]["rows"][0][7] == "37"
    assert output[0]["rows"][1][0] == "testSet2"
    assert output[0]["rows"][1][1] == "testHost2"
    assert output[0]["rows"][1][2] == "26"
    assert output[0]["rows"][1][3] == "178"
    assert output[0]["rows"][1][4] == "10"
    assert output[0]["rows"][1][5] == "2135"
    assert output[0]["rows"][1][6] == "N/A"
    assert output[0]["rows"][1][7] == "26"

    assert output[1]["type"] == "chart"
    assert len(output[1]["data"]) == 2
    assert output[1]["data"]["testSet/testHost"]["current"] == 37
    assert output[1]["data"]["testSet/testHost"]["available"] == 167
    assert output[1]["data"]["testSet/testHost"]["active"] == 13
    assert output[1]["data"]["testSet/testHost"]["totalCreated"] == 1920
    assert output[1]["data"]["testSet/testHost"]["rejected"] == 0
    assert output[1]["data"]["testSet/testHost"]["threaded"] == 37
    assert output[1]["data"]["testSet2/testHost2"]["current"] == 26
    assert output[1]["data"]["testSet2/testHost2"]["available"] == 178
    assert output[1]["data"]["testSet2/testHost2"]["active"] == 10
    assert output[1]["data"]["testSet2/testHost2"]["totalCreated"] == 2135
    assert output[1]["data"]["testSet2/testHost2"]["rejected"] == 0
    assert output[1]["data"]["testSet2/testHost2"]["threaded"] == 26


def test_conn_parser_with_empty_data():
    parser = ConnParser()
    output = parser.parse(
        [
            {
                "set_name": "testSet",
                "host": "testHost",
                "connections": None,
            }
        ]
    )
    assert len(output) == 2
    assert output[0]["type"] == "table"
    assert output[0]["caption"] == "Connections"
    assert output[0]["header"] == [
        "Component",
        "Host",
        "Current",
        "Available",
        "Active",
        "Created",
        "Rejected",
        "Threaded",
    ]
    assert len(output[0]["rows"]) == 1
    assert output[0]["rows"][0][0] == "testSet"
    assert output[0]["rows"][0][1] == "testHost"
    assert output[0]["rows"][0][2] == "N/A"
    assert output[0]["rows"][0][3] == "N/A"
    assert output[0]["rows"][0][4] == "N/A"
    assert output[0]["rows"][0][5] == "N/A"
    assert output[0]["rows"][0][6] == "N/A"
    assert output[0]["rows"][0][7] == "N/A"

    assert output[1]["type"] == "chart"
    assert len(output[1]["data"]) == 1
    assert output[1]["data"]["testSet/testHost"]["current"] == 0
    assert output[1]["data"]["testSet/testHost"]["available"] == 0
    assert output[1]["data"]["testSet/testHost"]["active"] == 0
    assert output[1]["data"]["testSet/testHost"]["totalCreated"] == 0
    assert output[1]["data"]["testSet/testHost"]["rejected"] == 0
    assert output[1]["data"]["testSet/testHost"]["threaded"] == 0
