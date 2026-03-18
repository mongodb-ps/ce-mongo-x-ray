from x_ray.healthcheck.parsers.security_parser import SecurityParser  # type: ignore

SECURITY_INFOS = [
    {
        "set_name": "shard01",
        "host": "localhost:30018",
        "rawResult": {
            "parsed": {
                "net": {
                    "port": 30018,
                    "tls": {
                        "mode": "requireTLS",
                        "certificateKeyFile": "/etc/ssl/mongodb.pem",
                    },
                },
                "processManagement": {"fork": True},
                "replication": {"replSet": "shard01"},
                "sharding": {"clusterRole": "shardsvr"},
                "storage": {
                    "dbPath": "/Users/yaoxing.zhang/Workspace/MongoDB/sh_5.0.19/data/shard01/rs1/db",
                    "wiredTiger": {"engineConfig": {"cacheSizeGB": 1.0}},
                },
                "systemLog": {
                    "destination": "file",
                    "path": "/Users/yaoxing.zhang/Workspace/MongoDB/sh_5.0.19/data/shard01/rs1/mongod.log",
                },
                "auditLog": {"destination": "file", "path": "/var/log/mongodb/audit.log"},
            },
        },
    },
    {
        "set_name": "shard02",
        "host": "localhost:30021",
        "rawResult": {
            "parsed": {
                "net": {"port": 30021},
                "processManagement": {"fork": True},
                "replication": {"replSet": "shard02"},
                "sharding": {"clusterRole": "shardsvr"},
                "storage": {
                    "dbPath": "/Users/yaoxing.zhang/Workspace/MongoDB/sh_5.0.19/data/shard02/rs1/db",
                    "wiredTiger": {"engineConfig": {"cacheSizeGB": 1.0}},
                },
                "systemLog": {
                    "destination": "file",
                    "path": "/Users/yaoxing.zhang/Workspace/MongoDB/sh_5.0.19/data/shard02/rs1/mongod.log",
                },
                "security": {
                    "authorization": "enabled",
                    "enableEncryption": True,
                    "encryptionKeyFile": "/etc/ssl/mongodb-keyfile",
                    "redactClientLogData": True,
                    "clusterAuthMode": "X.509",
                },
            },
        },
    },
    {
        "set_name": "configRepl",
        "host": "localhost:30024",
        "rawResult": {
            "parsed": {
                "net": {"port": 30024},
                "processManagement": {"fork": True},
                "replication": {"replSet": "configRepl"},
                "sharding": {"clusterRole": "configsvr"},
                "storage": {
                    "dbPath": "/Users/yaoxing.zhang/Workspace/MongoDB/sh_5.0.19/data/configRepl/rs1/db",
                    "wiredTiger": {"engineConfig": {"cacheSizeGB": 1.0}},
                },
                "systemLog": {
                    "destination": "file",
                    "path": "/Users/yaoxing.zhang/Workspace/MongoDB/sh_5.0.19/data/configRepl/rs1/mongod.log",
                },
            },
        },
    },
    {
        "set_name": "mongos",
        "host": "M-QTFH0WFXLG:30017",
        "rawResult": {
            "parsed": {
                "net": {"port": 30017},
                "processManagement": {"fork": True},
                "sharding": {"configDB": "configRepl/localhost:30024"},
                "systemLog": {
                    "destination": "file",
                    "path": "/Users/yaoxing.zhang/Workspace/MongoDB/sh_5.0.19/data/mongos.log",
                },
            },
        },
    },
    {
        "set_name": "mongos",
        "host": "M-QTFH0WFXLG:30028",
        "rawResult": None,
    },
]


def test_security_parser():
    parser = SecurityParser()
    result = parser.parse(SECURITY_INFOS)
    table = result[0]
    assert table["caption"] == "Security Information"
    assert table["header"] == [
        "Component",
        "Host",
        "Listen",
        "TLS",
        "Authorization",
        "Cluster Auth",
        "Log Redaction",
        "EAR",
        "Auditing",
    ]
    rows = table["rows"]
    assert rows[0][0] == "shard01"
    assert rows[0][1] == "localhost:30018"
    assert rows[0][2] == "127.0.0.1:30018"
    assert rows[0][3] == "requireTLS"
    assert rows[0][4] == "disabled"
    assert rows[0][5] == "disabled"
    assert rows[0][6] == "disabled"
    assert rows[0][7] == "false"
    assert rows[0][8] == "enabled"

    assert rows[1][0] == "shard02"
    assert rows[1][1] == "localhost:30021"
    assert rows[1][2] == "127.0.0.1:30021"
    assert rows[1][3] == "disabled"
    assert rows[1][4] == "enabled"
    assert rows[1][5] == "X.509"
    assert rows[1][6] == True
    assert rows[1][7] == True
    assert rows[1][8] == "disabled"

    assert rows[2][0] == "configRepl"
    assert rows[2][1] == "localhost:30024"
    assert rows[2][2] == "127.0.0.1:30024"
    assert rows[2][3] == "disabled"
    assert rows[2][4] == "disabled"
    assert rows[2][5] == "disabled"
    assert rows[2][6] == "disabled"
    assert rows[2][7] == "false"
    assert rows[2][8] == "disabled"

    assert rows[3][0] == "mongos"
    assert rows[3][1] == "M-QTFH0WFXLG:30017"
    assert rows[3][2] == "127.0.0.1:30017"
    assert rows[3][3] == "disabled"
    assert rows[3][4] == "disabled"
    assert rows[3][5] == "disabled"
    assert rows[3][6] == "disabled"
    assert rows[3][7] == "false"
    assert rows[3][8] == "disabled"

    assert rows[4][0] == "mongos"
    assert rows[4][1] == "M-QTFH0WFXLG:30028"
    assert rows[4][2] == "N/A"
    assert rows[4][3] == "N/A"
    assert rows[4][4] == "N/A"
    assert rows[4][5] == "N/A"
    assert rows[4][6] == "N/A"
    assert rows[4][7] == "N/A"
    assert rows[4][8] == "N/A"
