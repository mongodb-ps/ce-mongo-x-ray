from x_ray.healthcheck.parsers.coll_stats_parser import CollStatsParser  # type: ignore

STATS: list = [
    {
        "collFragmentation": {"reusable": 118784, "totalSize": 237568, "fragmentation": 0.5},
        "indexFragmentations": [
            {"indexName": "_id_", "reusable": 184320, "totalSize": 368640, "fragmentation": 0.5},
            {"indexName": "_id_hashed", "reusable": 188416, "totalSize": 372736, "fragmentation": 0.5055},
            {"indexName": "$**_1", "reusable": 0, "totalSize": 102400, "fragmentation": 0.0},
            {"indexName": "pos_2d", "reusable": 0, "totalSize": 8192, "fragmentation": 0.0},
        ],
        "latencyStats": {
            "reads_latency": 740.8371040723982,
            "writes_latency": 0,
            "commands_latency": 0,
            "transactions_latency": 0,
        },
        "ns": "foo.bar",
    },
    {
        "collFragmentation": {"reusable": 0, "totalSize": 20480, "fragmentation": 0.0},
        "indexFragmentations": [{"indexName": "_id_", "reusable": 0, "totalSize": 20480, "fragmentation": 0.0}],
        "latencyStats": {
            "reads_latency": 811.493670886076,
            "writes_latency": 0,
            "commands_latency": 0,
            "transactions_latency": 0,
        },
        "ns": "test.test",
    },
]


def test_coll_stats_parser():
    parser = CollStatsParser()
    output = parser.parse(STATS, set_name="testSet", host="testHost")
    assert len(output) == 4
    assert output[0]["type"] == "table"
    assert output[0]["caption"] == "Storage Fragmentation"
    assert output[0]["header"] == [
        "Component",
        "Host",
        "Namespace",
        "Collection Fragmentation",
        {"text": "Index Fragmentation", "align": "left"},
    ]
    assert len(output[0]["rows"]) == 2
    assert output[0]["rows"][0][0] == "testSet"
    assert output[0]["rows"][0][1] == "testHost"
    assert output[0]["rows"][0][2] == "foo.bar"
    assert output[0]["rows"][0][3] == "50.00%"
    assert output[0]["rows"][0][4].startswith("43.75%")
    assert output[0]["rows"][1][2] == "test.test"
    assert output[0]["rows"][1][3] == "0.00%"
    assert output[0]["rows"][1][4].startswith("0.00%")

    assert output[1]["type"] == "chart"
    assert len(output[1]["data"]) == 2
    assert output[1]["data"][0]["ns"] == "foo.bar"
    assert output[1]["data"][0]["collFrag"] == 0.5
    assert output[1]["data"][0]["indexFrag"] == 0.4375
    assert output[1]["data"][1]["ns"] == "test.test"
    assert output[1]["data"][1]["collFrag"] == 0.0
    assert output[1]["data"][1]["indexFrag"] == 0.0

    assert output[2]["type"] == "table"
    assert output[2]["caption"] == "Operation Latency"
    assert output[2]["header"] == [
        "Component",
        "Host",
        "Namespace",
        "Read Latency",
        "Write Latency",
        "Command Latency",
        "Transaction Latency",
    ]
    assert len(output[2]["rows"]) == 2
    assert output[2]["rows"][0][0] == "testSet"
    assert output[2]["rows"][0][1] == "testHost"
    assert output[2]["rows"][0][2] == "foo.bar"
    assert output[2]["rows"][0][3] == "740.84ms"
    assert output[2]["rows"][0][4] == "0.00ms"
    assert output[2]["rows"][0][5] == "0.00ms"
    assert output[2]["rows"][0][6] == "0.00ms"
    assert output[2]["rows"][1][2] == "test.test"
    assert output[2]["rows"][1][3] == "811.49ms"
    assert output[2]["rows"][1][4] == "0.00ms"
    assert output[2]["rows"][1][5] == "0.00ms"
    assert output[2]["rows"][1][6] == "0.00ms"

    assert output[3]["type"] == "chart"
    assert len(output[3]["data"]) == 2
    assert output[3]["data"][0]["ns"] == "foo.bar"
    assert output[3]["data"][0]["readsLatency"] == 740.8371040723982
    assert output[3]["data"][0]["writesLatency"] == 0
    assert output[3]["data"][0]["commandsLatency"] == 0
    assert output[3]["data"][0]["transactionsLatency"] == 0
    assert output[3]["data"][1]["ns"] == "test.test"
    assert output[3]["data"][1]["readsLatency"] == 811.493670886076
    assert output[3]["data"][1]["writesLatency"] == 0
    assert output[3]["data"][1]["commandsLatency"] == 0
    assert output[3]["data"][1]["transactionsLatency"] == 0


def test_coll_stats_parser_with_empty_data():
    parser = CollStatsParser()
    output = parser.parse(None, set_name="testSet", host="testHost")
    assert len(output) == 4
    assert output[0]["type"] == "table"
    assert output[0]["caption"] == "Storage Fragmentation"
    assert output[0]["header"] == [
        "Component",
        "Host",
        "Namespace",
        "Collection Fragmentation",
        {"text": "Index Fragmentation", "align": "left"},
    ]
    assert len(output[0]["rows"]) == 1
    assert output[0]["rows"][0][0] == "testSet"
    assert output[0]["rows"][0][1] == "testHost"
    assert output[0]["rows"][0][2] == "N/A"
    assert output[0]["rows"][0][3] == "N/A"
    assert output[0]["rows"][0][4] == "N/A"

    assert output[1]["type"] == "chart"
    assert len(output[1]["data"]) == 0

    assert output[2]["type"] == "table"
    assert output[2]["caption"] == "Operation Latency"
    assert output[2]["header"] == [
        "Component",
        "Host",
        "Namespace",
        "Read Latency",
        "Write Latency",
        "Command Latency",
        "Transaction Latency",
    ]
    assert len(output[2]["rows"]) == 1
    assert output[2]["rows"][0][0] == "testSet"
    assert output[2]["rows"][0][1] == "testHost"
    assert output[2]["rows"][0][2] == "N/A"
    assert output[2]["rows"][0][3] == "N/A"
    assert output[2]["rows"][0][4] == "N/A"
    assert output[2]["rows"][0][5] == "N/A"
    assert output[2]["rows"][0][6] == "N/A"

    assert output[3]["type"] == "chart"
    assert len(output[3]["data"]) == 0
