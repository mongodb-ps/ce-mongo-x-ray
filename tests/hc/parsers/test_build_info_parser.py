from x_ray.healthcheck.parsers.build_info_parser import BuildInfoParser

BUILD_INFOS = [
    (
        "shard01",
        "localhost:30018",
        {
            "version": "5.0.19",
            "versionArray": [5, 0, 19, 0],
            "openssl": {"running": "Apple Secure Transport"},
            "buildEnvironment": {
                "target_arch": "x86_64",
                "target_os": "macOS",
            },
        },
    ),
    (
        "shard01",
        "localhost:30019",
        {
            "version": "5.0.19",
            "versionArray": [5, 0, 19, 0],
            "openssl": {"running": "Apple Secure Transport"},
            "buildEnvironment": {
                "target_arch": "x86_64",
                "target_os": "macOS",
            },
        },
    ),
    (
        "shard01",
        "localhost:30020",
        None,
    ),
]


def test_build_info_parser():
    parser = BuildInfoParser()
    parsed_output = parser.parse(BUILD_INFOS)

    assert len(parsed_output) == 2

    table = parsed_output[0]
    assert table["type"] == "table"
    assert table["caption"] == "Server Build Information"
    assert table["header"] == ["Component", "Host", "Version", "OpenSSL", "Target Arch", "Target OS"]
    assert len(table["rows"]) == 3
    assert table["rows"][0] == [
        "shard01",
        "localhost:30018",
        "5.0.19",
        "Apple Secure Transport",
        "x86_64",
        "macOS",
    ]
    assert table["rows"][1] == [
        "shard01",
        "localhost:30019",
        "5.0.19",
        "Apple Secure Transport",
        "x86_64",
        "macOS",
    ]
    assert table["rows"][2] == [
        "shard01",
        "localhost:30020",
        "N/A",
        "N/A",
        "N/A",
        "N/A",
    ]

    chart = parsed_output[1]
    assert chart["type"] == "chart"
    assert chart["data"] == {"5.0.19": 2, "N/A": 1}
