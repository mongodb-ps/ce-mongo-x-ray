from x_ray.healthcheck.issues import ISSUE
from x_ray.healthcheck.rules.security_rule import SecurityRule

DATA_WITH_ISSUES = {
    "parsed": {
        "net": {"port": 27017, "bindIp": "0.0.0.0"},
        "processManagement": {"fork": True},
        "replication": {"replSet": "shard01"},
        "sharding": {"clusterRole": "shardsvr"},
        "storage": {
            "dbPath": "/data/rs1/db",
            "wiredTiger": {"engineConfig": {"cacheSizeGB": 1}},
        },
        "systemLog": {
            "destination": "file",
            "path": "/data/rs1/mongod.log",
        },
    }
}

DATA_WITH_ISSUES_2 = {
    "parsed": {
        "net": {"port": 37017, "bindIp": "192.168.0.1", "tls": {"mode": "allowTLS"}},
        "security": {
            "authorization": "enabled",
            "redactClientLogData": True,
            "enableEncryption": True,
            "encryptionKeyFile": "/path/to/keyfile",
        },
        "processManagement": {"fork": True},
        "replication": {"replSet": "shard01"},
        "sharding": {"clusterRole": "shardsvr"},
        "storage": {
            "dbPath": "/data/rs1/db",
            "wiredTiger": {"engineConfig": {"cacheSizeGB": 1}},
        },
        "systemLog": {
            "destination": "file",
            "path": "/data/rs1/mongod.log",
        },
        "auditLog": {"destination": "file", "path": "/data/rs1/audit.log"},
    }
}
DATA_WITH_NO_ISSUES = {
    "parsed": {
        "net": {"port": 37017, "bindIp": "192.168.0.1", "tls": {"mode": "requireTLS"}},
        "security": {
            "authorization": "enabled",
            "redactClientLogData": True,
            "enableEncryption": True,
            "kmip": {
                "serverName": "kmip.example.com",
                "port": 5696,
                "clientCertificateFile": "/path/to/cert.pem",
                "serverCAFile": "/path/to/ca.pem",
            },
        },
        "processManagement": {"fork": True},
        "replication": {"replSet": "shard01"},
        "sharding": {"clusterRole": "shardsvr"},
        "storage": {
            "dbPath": "/data/rs1/db",
            "wiredTiger": {"engineConfig": {"cacheSizeGB": 1}},
        },
        "systemLog": {
            "destination": "file",
            "path": "/data/rs1/mongod.log",
        },
        "auditLog": {"destination": "file", "path": "/data/rs1/audit.log"},
    }
}


def test_security_rule_issues():
    rule = SecurityRule({})
    results, parsed_data = rule.apply(DATA_WITH_ISSUES)

    assert len(results) == 7

    issue_ids = {issue["id"] for issue in results}
    expected_issue_ids = {
        ISSUE.AUTHORIZATION_DISABLED,
        ISSUE.LOG_REDACTION_DISABLED,
        ISSUE.TLS_DISABLED,
        ISSUE.OPEN_BIND_IP,
        ISSUE.DEFAULT_PORT_USED,
        ISSUE.AUDITING_DISABLED,
        ISSUE.ENCRYPTION_AT_REST_DISABLED,
    }

    assert issue_ids == expected_issue_ids


def test_security_rule_issues_2():
    rule = SecurityRule({})
    results, parsed_data = rule.apply(DATA_WITH_ISSUES_2)

    assert len(results) == 2

    issue_ids = {issue["id"] for issue in results}
    expected_issue_ids = {
        ISSUE.OPTIONAL_TLS,
        ISSUE.ENCRYPTION_AT_REST_USING_KEYFILE,
    }

    assert issue_ids == expected_issue_ids


def test_security_rule_no_issues():
    rule = SecurityRule({})
    results, parsed_data = rule.apply(DATA_WITH_NO_ISSUES)

    assert len(results) == 0
