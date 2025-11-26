from libs.healthcheck.issues import ISSUE
from libs.healthcheck.rules.cache_rule import CacheRule

DATA_BASE_SERVER_STATUS = {
    "wiredTiger": {
        "cache": {
            "bytes read into cache": 0,
            "bytes written from cache": 0,
            "bytes allocated for updates": 0,
            "bytes dirty in the cache cumulative": 0,
            "maximum bytes configured": 200000000,  # 200 MB
            "bytes currently in the cache": 150000000,  # 150 MB
        },
    },
    "uptimeMillis": 1000,
}

DATA_SERVER_STATUS_NORMAL = {
    "wiredTiger": {
        "cache": {
            "bytes read into cache": 50000000,  # 50 MB
            "bytes written from cache": 5000000,  # 5 MB
            "bytes allocated for updates": 5000000,  # 5 MB
            "bytes dirty in the cache cumulative": 10000000,  # 10 MB
            "maximum bytes configured": 200000000,  # 200 MB
            "bytes currently in the cache": 150000000,  # 150 MB
        },
    },
    "uptimeMillis": 2000,
}

DATA_SERVER_STATUS_HIGH = {
    "wiredTiger": {
        "cache": {
            "bytes read into cache": 110000000,  # 110 MB
            "bytes written from cache": 6000000,  # 6 MB
            "bytes allocated for updates": 17000000,  # 17 MB
            "bytes dirty in the cache cumulative": 35000000,  # 35 MB
            "maximum bytes configured": 200000000,  # 200 MB
            "bytes currently in the cache": 185000000,  # 185 MB
        },
    },
    "uptimeMillis": 2000,
}

DATA_SERVER_STATUS_CRITICAL = {
    "wiredTiger": {
        "cache": {
            "bytes read into cache": 90000000,  # 90 MB
            "bytes written from cache": 6000000,  # 6 MB
            "bytes allocated for updates": 25000000,  # 25 MB
            "bytes dirty in the cache cumulative": 45000000,  # 45 MB
            "maximum bytes configured": 200000000,  # 200 MB
            "bytes currently in the cache": 195000000,  # 195 MB
        },
    },
    "uptimeMillis": 2000,
}
config = {
    "cache_read_into_mb": 100,
    "updates_ratio": [0.08, 0.1],
    "dirty_ratio": [0.15, 0.2],
    "cache_fill_ratio": [0.9, 0.95],
}


def test_cache_rule_normal():
    rule = CacheRule(config)
    result, parsed_data = rule.apply(
        DATA_SERVER_STATUS_NORMAL,
        extra_info={"host": "localhost", "server_status": DATA_BASE_SERVER_STATUS},
    )
    assert result == []
    assert parsed_data["readInto"] == 50000000.0
    assert parsed_data["writtenFrom"] == 5000000.0
    assert parsed_data["forUpdates"] == 5000000
    assert parsed_data["dirty"] == 10000000


def test_cache_rule_high():
    rule = CacheRule(config)
    result, parsed_data = rule.apply(
        DATA_SERVER_STATUS_HIGH,
        extra_info={"host": "localhost", "server_status": DATA_BASE_SERVER_STATUS},
    )
    assert len(result) == 4
    assert result[0]["id"] == ISSUE.HIGH_SWAPPING
    assert result[1]["id"] == ISSUE.HIGH_UPDATES_RATIO
    assert result[2]["id"] == ISSUE.HIGH_DIRTY_RATIO
    assert result[3]["id"] == ISSUE.HIGH_CACHE_FILL_RATIO
    assert parsed_data["readInto"] == 110000000.0
    assert parsed_data["writtenFrom"] == 6000000.0
    assert parsed_data["forUpdates"] == 17000000
    assert parsed_data["dirty"] == 35000000


def test_cache_rule_critical():
    rule = CacheRule(config)
    result, parsed_data = rule.apply(
        DATA_SERVER_STATUS_CRITICAL,
        extra_info={"host": "localhost", "server_status": DATA_BASE_SERVER_STATUS},
    )
    assert len(result) == 3
    assert result[0]["id"] == ISSUE.CRITICAL_UPDATES_RATIO
    assert result[1]["id"] == ISSUE.CRITICAL_DIRTY_RATIO
    assert result[2]["id"] == ISSUE.CRITICAL_CACHE_FILL_RATIO
    assert parsed_data["readInto"] == 90000000.0
    assert parsed_data["writtenFrom"] == 6000000.0
    assert parsed_data["forUpdates"] == 25000000
    assert parsed_data["dirty"] == 45000000
