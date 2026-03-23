from x_ray.healthcheck.parsers.rs_overview_parser import RSOverviewParser

RS_CONFIGS = [
    (
        "shard01",
        {
            "_id": "shard01",
            "version": 2,
            "term": 560,
            "members": [
                {
                    "_id": 0,
                    "host": "localhost:30018",
                    "arbiterOnly": False,
                    "buildIndexes": True,
                    "hidden": False,
                    "priority": 1.0,
                    "tags": {},
                    "secondaryDelaySecs": 0,
                    "votes": 1,
                },
                {
                    "_id": 1,
                    "host": "localhost:30019",
                    "arbiterOnly": False,
                    "buildIndexes": True,
                    "hidden": False,
                    "priority": 1.0,
                    "tags": {},
                    "secondaryDelaySecs": 0,
                    "votes": 1,
                },
                {
                    "_id": 2,
                    "host": "localhost:30020",
                    "arbiterOnly": False,
                    "buildIndexes": True,
                    "hidden": False,
                    "priority": 1.0,
                    "tags": {},
                    "secondaryDelaySecs": 0,
                    "votes": 1,
                },
            ],
            "protocolVersion": 1,
            "writeConcernMajorityJournalDefault": True,
            "settings": {
                "chainingAllowed": True,
                "heartbeatIntervalMillis": 2000,
                "heartbeatTimeoutSecs": 10,
                "electionTimeoutMillis": 10000,
                "catchUpTimeoutMillis": -1,
                "catchUpTakeoverDelayMillis": 30000,
                "getLastErrorModes": {},
                "getLastErrorDefaults": {"w": 1, "wtimeout": 0},
                "replicaSetId": {"$oid": "664ef1c56b32cb6f98acdf7e"},
            },
        },
    ),
    (
        "shard02",
        {
            "_id": "shard02",
            "version": 2,
            "term": 559,
            "members": [
                {
                    "_id": 0,
                    "host": "localhost:30021",
                    "arbiterOnly": False,
                    "buildIndexes": True,
                    "hidden": False,
                    "priority": 1.0,
                    "tags": {},
                    "secondaryDelaySecs": 0,
                    "votes": 1,
                },
                {
                    "_id": 1,
                    "host": "localhost:30022",
                    "arbiterOnly": False,
                    "buildIndexes": True,
                    "hidden": False,
                    "priority": 1.0,
                    "tags": {},
                    "secondaryDelaySecs": 0,
                    "votes": 1,
                },
                {
                    "_id": 2,
                    "host": "localhost:30023",
                    "arbiterOnly": False,
                    "buildIndexes": True,
                    "hidden": False,
                    "priority": 1.0,
                    "tags": {},
                    "secondaryDelaySecs": 0,
                    "votes": 1,
                },
            ],
            "protocolVersion": 1,
            "writeConcernMajorityJournalDefault": True,
            "settings": {
                "chainingAllowed": True,
                "heartbeatIntervalMillis": 2000,
                "heartbeatTimeoutSecs": 10,
                "electionTimeoutMillis": 10000,
                "catchUpTimeoutMillis": -1,
                "catchUpTakeoverDelayMillis": 30000,
                "getLastErrorModes": {},
                "getLastErrorDefaults": {"w": 1, "wtimeout": 0},
                "replicaSetId": {"$oid": "664ef1c6f0ba584523a9ff0a"},
            },
        },
    ),
    (
        "configRepl",
        {
            "_id": "configRepl",
            "version": 1,
            "term": 12,
            "members": [
                {
                    "_id": 0,
                    "host": "localhost:30024",
                    "arbiterOnly": False,
                    "buildIndexes": True,
                    "hidden": False,
                    "priority": 1.0,
                    "tags": {},
                    "secondaryDelaySecs": 0,
                    "votes": 1,
                }
            ],
            "configsvr": True,
            "protocolVersion": 1,
            "writeConcernMajorityJournalDefault": True,
            "settings": {
                "chainingAllowed": True,
                "heartbeatIntervalMillis": 2000,
                "heartbeatTimeoutSecs": 10,
                "electionTimeoutMillis": 10000,
                "catchUpTimeoutMillis": -1,
                "catchUpTakeoverDelayMillis": 30000,
                "getLastErrorModes": {},
                "getLastErrorDefaults": {"w": 1, "wtimeout": 0},
                "replicaSetId": {"$oid": "664ef1c5174b158d636d6ee6"},
            },
        },
    ),
]


def test_rs_overview_parser():
    parser = RSOverviewParser()
    result = parser.parse(RS_CONFIGS)
    assert len(result) == 1
    table = result[0]
    assert table["type"] == "table"
    assert table["caption"] == "Components Overview"
    assert table["header"] == ["Name", "#Members", "#Voting Members", "#Arbiters", "#Hidden Members"]
    assert len(table["rows"]) == 3
    assert table["rows"][0] == ["shard01", 3, 3, 0, 0]
    assert table["rows"][1] == ["shard02", 3, 3, 0, 0]
    assert table["rows"][2] == ["configRepl", 1, 1, 0, 0]
