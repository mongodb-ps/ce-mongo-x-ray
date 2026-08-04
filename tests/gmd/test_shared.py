from x_ray.gmd_analysis.shared import ShardNameMapper, load_json  # type: ignore


def test_shard_name_mapper():
    mapper = ShardNameMapper(["UK-xxx-shard-01", "HK-xxx-shard-02", "UK-xxx-shard-01"])
    assert mapper.map("UK-xxx-shard-01") == "s1"
    assert mapper.map("HK-xxx-shard-02") == "s0"
    assert mapper.notes() == "- s0: HK-xxx-shard-02\n- s1: UK-xxx-shard-01"


def test_shard_name_mapper_empty():
    mapper = ShardNameMapper()
    assert mapper.notes() == ""
    assert mapper.map("shard01") == "shard01"


def test_shard_name_mapper_config_alias():
    mapper = ShardNameMapper(["config", "UK-xxx-shard-01", "HK-xxx-shard-02"])
    assert mapper.map("config") == "c"
    assert mapper.map("HK-xxx-shard-02") == "s0"
    assert mapper.map("UK-xxx-shard-01") == "s1"
    assert mapper.notes() == "- c: config\n- s0: HK-xxx-shard-02\n- s1: UK-xxx-shard-01"


def test_shard_name_mapper_config_absent():
    mapper = ShardNameMapper(["UK-xxx-shard-01"])
    assert mapper.map("config") == "config"
    assert mapper.notes() == "- s0: UK-xxx-shard-01"


def test_shard_name_mapper_deterministic_order():
    mapper_a = ShardNameMapper(["B-shard", "A-shard", "C-shard"])
    mapper_b = ShardNameMapper(["C-shard", "A-shard", "B-shard"])
    assert mapper_a.notes() == mapper_b.notes() == "- s0: A-shard\n- s1: B-shard\n- s2: C-shard"


def test_load_json():
    json_str_legacy = '{"ts":{"$timestamp":{"t":1765119887,"i":0}},"num":{"$numberLong":"123"},"date":{"$date":1717243200000},"objId":{"$oid":"6935a4e5f25e7aa93c32a928"}}'
    result = load_json(json_str_legacy)
    assert result["date"].isoformat() == "2024-06-01T12:00:00"
    assert result["ts"].time == 1765119887
    assert result["num"] == 123
    assert str(result["objId"]) == "6935a4e5f25e7aa93c32a928"

    ejson_str = '{"ts":{"$timestamp":{"t":1765119887,"i":0}},"num":{"$numberLong":"123"},"date":{"$date":"2024-06-01T12:00:00Z"},"objId":{"$oid":"6935a4e5f25e7aa93c32a928"}}'
    result = load_json(ejson_str)
    assert result["date"].isoformat() == "2024-06-01T12:00:00"
    assert result["ts"].time == 1765119887
    assert result["num"] == 123
    assert str(result["objId"]) == "6935a4e5f25e7aa93c32a928"

    illegal_json_str = '{"ts": {"$timestamp": "7581132188184215559"}, "ts2":{"$timestamp":{"t":1765119887,"i":0}}}'
    result = load_json(illegal_json_str)
    assert result["ts2"].time == 1765119887
    assert result["ts"].time == 1765119887
    assert result["ts"].inc == 7
