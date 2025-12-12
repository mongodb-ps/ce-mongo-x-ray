from x_ray.healthcheck.parsers.rs_details_parser import RSDetailsParser
from bson.timestamp import Timestamp
from bson.objectid import ObjectId

from x_ray.utils import is_number

RS_INFOS = [
    {
        "set_name": "shard01",
        "rs_config": {
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
                "replicaSetId": ObjectId("664ef1c56b32cb6f98acdf7e"),
            },
        },
        "rs_status": {
            "set": "shard01",
            "date": {"$date": "2025-12-10T22:18:19.672Z"},
            "myState": 1,
            "term": 560,
            "syncSourceHost": "",
            "syncSourceId": -1,
            "heartbeatIntervalMillis": 2000,
            "majorityVoteCount": 2,
            "writeMajorityCount": 2,
            "votingMembersCount": 3,
            "writableVotingMembersCount": 3,
            "optimes": {
                "lastCommittedOpTime": {"ts": Timestamp(1765405090, 1), "t": 560},
                "lastCommittedWallTime": {"$date": "2025-12-10T22:18:10.936Z"},
                "readConcernMajorityOpTime": {"ts": Timestamp(1765405090, 1), "t": 560},
                "appliedOpTime": {"ts": Timestamp(1765405090, 1), "t": 560},
                "durableOpTime": {"ts": Timestamp(1765405090, 1), "t": 560},
                "lastAppliedWallTime": {"$date": "2025-12-10T22:18:10.936Z"},
                "lastDurableWallTime": {"$date": "2025-12-10T22:18:10.936Z"},
            },
            "lastStableRecoveryTimestamp": Timestamp(1765405060, 1),
            "electionCandidateMetrics": {
                "lastElectionReason": "electionTimeout",
                "lastElectionDate": {"$date": "2025-11-25T12:00:39.526Z"},
                "electionTerm": 560,
                "lastCommittedOpTimeAtElection": {"ts": Timestamp(0, 0), "t": -1},
                "lastSeenOpTimeAtElection": {"ts": Timestamp(1764071986, 1), "t": 559},
                "numVotesNeeded": 2,
                "priorityAtElection": 1.0,
                "electionTimeoutMillis": 10000,
                "numCatchUpOps": 0,
                "newTermStartDate": {"$date": "2025-11-25T12:00:39.605Z"},
                "wMajorityWriteAvailabilityDate": {"$date": "2025-11-25T12:00:40.250Z"},
            },
            "members": [
                {
                    "_id": 0,
                    "name": "localhost:30018",
                    "health": 1.0,
                    "state": 1,
                    "stateStr": "PRIMARY",
                    "uptime": 1333074,
                    "optime": {"ts": Timestamp(1765405090, 1), "t": 560},
                    "optimeDate": {"$date": "2025-12-10T22:18:10Z"},
                    "lastAppliedWallTime": {"$date": "2025-12-10T22:18:10.936Z"},
                    "lastDurableWallTime": {"$date": "2025-12-10T22:18:10.936Z"},
                    "syncSourceHost": "",
                    "syncSourceId": -1,
                    "infoMessage": "",
                    "electionTime": Timestamp(1764072039, 1),
                    "electionDate": {"$date": "2025-11-25T12:00:39Z"},
                    "configVersion": 2,
                    "configTerm": 560,
                    "self": True,
                    "lastHeartbeatMessage": "",
                },
                {
                    "_id": 1,
                    "name": "localhost:30019",
                    "health": 0,
                    "state": 8,
                    "stateStr": "(not reachable/healthy)",
                    "uptime": 0,
                    "optime": {"ts": Timestamp(0, 0), "t": {"$numberLong": "-1"}},
                    "optimeDurable": {"ts": Timestamp(0, 0), "t": {"$numberLong": "-1"}},
                    "optimeDate": {"$date": "1970-01-01T00:00:00.000Z"},
                    "optimeDurableDate": {"$date": "1970-01-01T00:00:00.000Z"},
                    "lastAppliedWallTime": {"$date": "2025-12-12T15:27:37.867Z"},
                    "lastDurableWallTime": {"$date": "2025-12-12T15:27:37.867Z"},
                    "lastHeartbeat": {"$date": "2025-12-12T15:27:50.222Z"},
                    "lastHeartbeatRecv": {"$date": "2025-12-12T15:27:42.204Z"},
                    "pingMs": {"$numberLong": "0"},
                    "lastHeartbeatMessage": "Error connecting to localhost:30019 (127.0.0.1:30019) :: caused by :: Connection refused",
                    "syncSourceHost": "",
                    "syncSourceId": -1,
                    "infoMessage": "",
                    "configVersion": 2,
                    "configTerm": 560,
                },
                {
                    "_id": 2,
                    "name": "localhost:30020",
                    "health": 1.0,
                    "state": 2,
                    "stateStr": "SECONDARY",
                    "uptime": 1333064,
                    "optime": {"ts": Timestamp(1765405090, 1), "t": 560},
                    "optimeDurable": {"ts": Timestamp(1765405090, 1), "t": 560},
                    "optimeDate": {"$date": "2025-12-10T22:18:10Z"},
                    "optimeDurableDate": {"$date": "2025-12-10T22:18:10Z"},
                    "lastAppliedWallTime": {"$date": "2025-12-10T22:18:10.936Z"},
                    "lastDurableWallTime": {"$date": "2025-12-10T22:18:10.936Z"},
                    "lastHeartbeat": {"$date": "2025-12-10T22:18:19.215Z"},
                    "lastHeartbeatRecv": {"$date": "2025-12-10T22:18:18.036Z"},
                    "pingMs": 0,
                    "lastHeartbeatMessage": "",
                    "syncSourceHost": "localhost:30018",
                    "syncSourceId": 0,
                    "infoMessage": "",
                    "configVersion": 2,
                    "configTerm": 560,
                },
            ],
            "ok": 1.0,
            "$gleStats": {
                "lastOpTime": Timestamp(0, 0),
                "electionId": ObjectId("7fffffff0000000000000230"),
            },
            "lastCommittedOpTime": Timestamp(1765405090, 1),
            "$configServerState": {"opTime": {"ts": Timestamp(1765405098, 2), "t": -1}},
            "$clusterTime": {
                "clusterTime": Timestamp(1765405098, 2),
                "signature": {
                    "hash": {"$binary": {"base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAA=", "subType": "00"}},
                    "keyId": 0,
                },
            },
            "operationTime": Timestamp(1765405090, 1),
        },
        "oplog_info": {
            "localhost:30018": {
                "configured_retention_hours": "N/A",
                "current_retention_hours": 36.710277777778,
            },
            "localhost:30019": {
                "configured_retention_hours": 0,
                "current_retention_hours": 36.710277777778,
            },
            "localhost:30020": {
                "configured_retention_hours": 0,
                "current_retention_hours": 36.710277777778,
            },
        },
    },
    {
        "set_name": "shard02",
        "rs_config": {
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
                "replicaSetId": ObjectId("664ef1c6f0ba584523a9ff0a"),
            },
        },
        "rs_status": {
            "set": "shard02",
            "date": {"$date": "2025-12-10T22:18:19.696Z"},
            "myState": 1,
            "term": 559,
            "syncSourceHost": "",
            "syncSourceId": -1,
            "heartbeatIntervalMillis": 2000,
            "majorityVoteCount": 2,
            "writeMajorityCount": 2,
            "votingMembersCount": 3,
            "writableVotingMembersCount": 3,
            "optimes": {
                "lastCommittedOpTime": {"ts": Timestamp(1765405098, 1), "t": 559},
                "lastCommittedWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
                "readConcernMajorityOpTime": {"ts": Timestamp(1765405098, 1), "t": 559},
                "appliedOpTime": {"ts": Timestamp(1765405098, 1), "t": 559},
                "durableOpTime": {"ts": Timestamp(1765405098, 1), "t": 559},
                "lastAppliedWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
                "lastDurableWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
            },
            "lastStableRecoveryTimestamp": Timestamp(1765405078, 1),
            "electionCandidateMetrics": {
                "lastElectionReason": "electionTimeout",
                "lastElectionDate": {"$date": "2025-11-25T12:00:47.862Z"},
                "electionTerm": 559,
                "lastCommittedOpTimeAtElection": {"ts": Timestamp(0, 0), "t": -1},
                "lastSeenOpTimeAtElection": {"ts": Timestamp(1764071995, 1), "t": 558},
                "numVotesNeeded": 2,
                "priorityAtElection": 1.0,
                "electionTimeoutMillis": 10000,
                "numCatchUpOps": 0,
                "newTermStartDate": {"$date": "2025-11-25T12:00:47.960Z"},
                "wMajorityWriteAvailabilityDate": {"$date": "2025-11-25T12:00:48.631Z"},
            },
            "members": [
                {
                    "_id": 0,
                    "name": "localhost:30021",
                    "health": 1.0,
                    "state": 1,
                    "stateStr": "PRIMARY",
                    "uptime": 1333065,
                    "optime": {"ts": Timestamp(1765405098, 1), "t": 559},
                    "optimeDate": {"$date": "2025-12-10T22:18:18Z"},
                    "lastAppliedWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
                    "lastDurableWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
                    "syncSourceHost": "",
                    "syncSourceId": -1,
                    "infoMessage": "",
                    "electionTime": Timestamp(1764072047, 1),
                    "electionDate": {"$date": "2025-11-25T12:00:47Z"},
                    "configVersion": 2,
                    "configTerm": 559,
                    "self": True,
                    "lastHeartbeatMessage": "",
                },
                {
                    "_id": 1,
                    "name": "localhost:30022",
                    "health": 1.0,
                    "state": 2,
                    "stateStr": "SECONDARY",
                    "uptime": 1333058,
                    "optime": {"ts": Timestamp(1765405088, 1), "t": 559},
                    "optimeDurable": {"ts": Timestamp(1765405088, 1), "t": 559},
                    "optimeDate": {"$date": "2025-12-10T22:18:08Z"},
                    "optimeDurableDate": {"$date": "2025-12-10T22:18:08Z"},
                    "lastAppliedWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
                    "lastDurableWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
                    "lastHeartbeat": {"$date": "2025-12-10T22:18:18.040Z"},
                    "lastHeartbeatRecv": {"$date": "2025-12-10T22:18:18.976Z"},
                    "pingMs": 0,
                    "lastHeartbeatMessage": "",
                    "syncSourceHost": "localhost:30021",
                    "syncSourceId": 0,
                    "infoMessage": "",
                    "configVersion": 2,
                    "configTerm": 559,
                },
                {
                    "_id": 2,
                    "name": "localhost:30023",
                    "health": 1.0,
                    "state": 2,
                    "stateStr": "SECONDARY",
                    "uptime": 1333055,
                    "optime": {"ts": Timestamp(1765405098, 1), "t": 559},
                    "optimeDurable": {"ts": Timestamp(1765405098, 1), "t": 559},
                    "optimeDate": {"$date": "2025-12-10T22:18:18Z"},
                    "optimeDurableDate": {"$date": "2025-12-10T22:18:18Z"},
                    "lastAppliedWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
                    "lastDurableWallTime": {"$date": "2025-12-10T22:18:18.396Z"},
                    "lastHeartbeat": {"$date": "2025-12-10T22:18:18.980Z"},
                    "lastHeartbeatRecv": {"$date": "2025-12-10T22:18:19.214Z"},
                    "pingMs": 0,
                    "lastHeartbeatMessage": "",
                    "syncSourceHost": "localhost:30021",
                    "syncSourceId": 0,
                    "infoMessage": "",
                    "configVersion": 2,
                    "configTerm": 559,
                },
            ],
            "ok": 1.0,
            "$gleStats": {
                "lastOpTime": Timestamp(0, 0),
                "electionId": ObjectId("7fffffff000000000000022f"),
            },
            "lastCommittedOpTime": Timestamp(1765405098, 1),
            "$configServerState": {"opTime": {"ts": Timestamp(1765405095, 2), "t": -1}},
            "$clusterTime": {
                "clusterTime": Timestamp(1765405098, 1),
                "signature": {
                    "hash": {"$binary": {"base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAA=", "subType": "00"}},
                    "keyId": 0,
                },
            },
            "operationTime": Timestamp(1765405098, 1),
        },
        "oplog_info": {
            "localhost:30021": {
                "configured_retention_hours": 48,
                "current_retention_hours": 36.710277777778,
            },
            "localhost:30022": {
                "configured_retention_hours": 48,
                "current_retention_hours": 36.710277777778,
            },
            "localhost:30023": {
                "configured_retention_hours": 72,
                "current_retention_hours": 36.710277777778,
            },
        },
    },
    {
        "set_name": "configRepl",
        "rs_config": {
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
                "replicaSetId": ObjectId("664ef1c5174b158d636d6ee6"),
            },
        },
        "rs_status": {
            "set": "configRepl",
            "date": {"$date": "2025-12-10T22:18:19.719Z"},
            "myState": 1,
            "term": 12,
            "syncSourceHost": "",
            "syncSourceId": -1,
            "configsvr": True,
            "heartbeatIntervalMillis": 2000,
            "majorityVoteCount": 1,
            "writeMajorityCount": 1,
            "votingMembersCount": 1,
            "writableVotingMembersCount": 1,
            "optimes": {
                "lastCommittedOpTime": {"ts": Timestamp(1765405098, 2), "t": 12},
                "lastCommittedWallTime": {"$date": "2025-12-10T22:18:18.789Z"},
                "readConcernMajorityOpTime": {"ts": Timestamp(1765405098, 2), "t": 12},
                "appliedOpTime": {"ts": Timestamp(1765405098, 2), "t": 12},
                "durableOpTime": {"ts": Timestamp(1765405098, 2), "t": 12},
                "lastAppliedWallTime": {"$date": "2025-12-10T22:18:18.789Z"},
                "lastDurableWallTime": {"$date": "2025-12-10T22:18:18.789Z"},
            },
            "lastStableRecoveryTimestamp": Timestamp(1765405052, 1),
            "electionCandidateMetrics": {
                "lastElectionReason": "electionTimeout",
                "lastElectionDate": {"$date": "2025-11-25T12:00:13.940Z"},
                "electionTerm": 12,
                "lastCommittedOpTimeAtElection": {"ts": Timestamp(0, 0), "t": -1},
                "lastSeenOpTimeAtElection": {"ts": Timestamp(1764071996, 1), "t": 11},
                "numVotesNeeded": 1,
                "priorityAtElection": 1.0,
                "electionTimeoutMillis": 10000,
                "newTermStartDate": {"$date": "2025-11-25T12:00:14.060Z"},
                "wMajorityWriteAvailabilityDate": {"$date": "2025-11-25T12:00:14.094Z"},
            },
            "members": [
                {
                    "_id": 0,
                    "name": "localhost:30024",
                    "health": 1.0,
                    "state": 1,
                    "stateStr": "PRIMARY",
                    "uptime": 1333086,
                    "optime": {"ts": Timestamp(1765405098, 2), "t": 12},
                    "optimeDate": {"$date": "2025-12-10T22:18:18Z"},
                    "lastAppliedWallTime": {"$date": "2025-12-10T22:18:18.789Z"},
                    "lastDurableWallTime": {"$date": "2025-12-10T22:18:18.789Z"},
                    "syncSourceHost": "",
                    "syncSourceId": -1,
                    "infoMessage": "",
                    "electionTime": Timestamp(1764072013, 1),
                    "electionDate": {"$date": "2025-11-25T12:00:13Z"},
                    "configVersion": 1,
                    "configTerm": 12,
                    "self": True,
                    "lastHeartbeatMessage": "",
                }
            ],
            "ok": 1.0,
            "$gleStats": {
                "lastOpTime": Timestamp(0, 0),
                "electionId": ObjectId("7fffffff000000000000000c"),
            },
            "lastCommittedOpTime": Timestamp(1765405098, 2),
            "$clusterTime": {
                "clusterTime": Timestamp(1765405098, 2),
                "signature": {
                    "hash": {"$binary": {"base64": "AAAAAAAAAAAAAAAAAAAAAAAAAAA=", "subType": "00"}},
                    "keyId": 0,
                },
            },
            "operationTime": Timestamp(1765405098, 2),
        },
        "oplog_info": {
            "localhost:30024": {
                "configured_retention_hours": 48,
                "current_retention_hours": 36.710277777778,
            },
        },
    },
]


def test_rs_details_parser():
    for rs_info in RS_INFOS:
        parser = RSDetailsParser()
        set_name = rs_info["set_name"]
        rs_config = rs_info["rs_config"]
        rs_status = rs_info["rs_status"]
        oplog_info = rs_info["oplog_info"]

        details_table = parser.parse(rs_info)[0]

        assert details_table["caption"] == f"Component Details - `{set_name}`"
        assert details_table["header"] == [
            "Host",
            "_id",
            "Arbiter",
            "Build Indexes",
            "Hidden",
            "Priority",
            "Votes",
            "Configured Delay (sec)",
            "Current Delay (sec)",
            "Oplog Window Hours",
        ]
        assert len(details_table["rows"]) == len(rs_config["members"])

        latest_optime = max(m["optime"]["ts"] for m in rs_status["members"])
        for i, row in enumerate(details_table["rows"]):
            host = row[0]
            _id = row[1]
            arbiter = row[2]
            build_indexes = row[3]
            hidden = row[4]
            priority = row[5]
            votes = row[6]
            configured_delay = row[7]
            current_delay = row[8]
            retention_hours = row[9]

            assert host == rs_config["members"][i]["host"]
            assert _id == rs_config["members"][i]["_id"]
            assert arbiter == rs_config["members"][i]["arbiterOnly"]
            assert build_indexes == rs_config["members"][i]["buildIndexes"]
            assert hidden == rs_config["members"][i]["hidden"]
            assert priority == rs_config["members"][i]["priority"]
            assert votes == rs_config["members"][i]["votes"]
            assert configured_delay == rs_config["members"][i]["secondaryDelaySecs"]
            assert current_delay == latest_optime.time - rs_status["members"][i]["optime"]["ts"].time
            configured = oplog_info[host]["configured_retention_hours"]
            current = oplog_info[host]["current_retention_hours"]
            if is_number(current) and is_number(configured):
                retention = max(configured, current)
            elif is_number(current):
                retention = current
            else:
                retention = "N/A"
            assert retention_hours == retention
