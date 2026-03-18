from x_ray.gmd_analysis.parsers.sh_details_parser import SHDetailsParser  # type: ignore

GMD_ITEM = {
    "shards": [
        {
            "_id": "shard01",
            "host": "shard01/localhost:30018,localhost:30019,localhost:30020",
        },
        {
            "_id": "shard02",
            "host": "shard02/localhost:30021,localhost:30022,localhost:30023",
        },
    ],
    "csrs": "configRepl/localhost:30024",
}


def test_sh_details_parser() -> None:
    parser = SHDetailsParser()
    result = parser.parse(GMD_ITEM)
    assert len(result) == 1
    details_table = result[0]
    assert details_table["type"] == "table"
    assert details_table["caption"] == "Component Details - `shards/csrs`"
    assert details_table["header"] == ["Component Name", "Hosts"]
    assert details_table["rows"] == [
        ["shard01", "localhost:30018,localhost:30019,localhost:30020"],
        ["shard02", "localhost:30021,localhost:30022,localhost:30023"],
        ["configRepl", "localhost:30024"],
    ]
