from x_ray.gmd_analysis.shared import load_json


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
