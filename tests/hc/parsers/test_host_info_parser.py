from x_ray.healthcheck.parsers.host_info_parser import HostInfoParser  # type: ignore

HOST_INFOS = [
    (
        "M-QTFH0WFXLG:30017",
        {
            "system": {
                "hostname": "M-QTFH0WFXLG:30017",
                "memLimitMB": 32768,
                "numCores": 10,
                "cpuArch": "x86_64",
                "numaEnabled": False,
            },
            "os": {"type": "Darwin", "name": "Mac OS X", "version": "24.6.0"},
            "extra": {
                "cpuFrequencyMHz": 2400,
                "cpuString": "Apple M1 Max",
            },
        },
    ),
    (
        "ip-172-31-22-196",
        {
            "system": {
                "hostname": "ip-172-31-22-196",
                "memLimitMB": 7736,
                "numCores": 2,
                "numCpuSockets": 1,
                "cpuArch": "x86_64",
                "numaEnabled": False,
            },
            "os": {"type": "Linux", "name": "Ubuntu", "version": "22.04"},
            "extra": {
                "extra": {
                    "cpuString": "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz",
                    "cpuFrequencyMHz": "3200.679",
                    "maxOpenFiles": 64000,
                    "mountInfo": [
                        {
                            "mountId": 25,
                            "mountPoint": "/",
                            "options": "rw,relatime",
                            "type": "ext4",
                        },
                        {
                            "mountId": 26,
                            "mountPoint": "/dev",
                            "options": "rw,nosuid,noexec,relatime",
                            "type": "devtmpfs",
                        },
                    ],
                }
            },
        },
    ),
    ("M-QTFH0WFXLG:30028", None),
]


def test_host_info_parser():
    parser = HostInfoParser()
    output = parser.parse(HOST_INFOS)
    assert len(output) == 2
    table_hardware = output[0]
    assert table_hardware["type"] == "table"
    assert table_hardware["caption"] == "Host Hardware Information"
    assert table_hardware["header"] == [
        {"text": "Host", "width": "*"},
        {"text": "CPU Family", "width": "350px"},
        {"text": "CPU Cores", "width": "100px"},
        {"text": "Memory", "width": "100px"},
        {"text": "OS", "width": "150px"},
        {"text": "NUMA Enabled", "width": "100px"},
    ]
    assert table_hardware["rows"][0] == [
        "M-QTFH0WFXLG:30017",
        "Apple M1 Max (x86_64) 2400 MHz",
        "10c",
        ("32.00 GB", 34359738368),
        "Mac OS X 24.6.0",
        False,
    ]
    assert table_hardware["rows"][1] == [
        "ip-172-31-22-196",
        "Intel(R) Xeon(R) Platinum 8175M CPU @ 2.50GHz (x86_64) 3200.679 MHz",
        "2c",
        ("7.55 GB", 8111783936),
        "Ubuntu 22.04",
        False,
    ]
    assert table_hardware["rows"][2] == [
        "M-QTFH0WFXLG:30028",
        "N/A",
        "N/A",
        "N/A",
        "N/A",
        "N/A",
    ]
    table_mounts = output[1]
    assert table_mounts["type"] == "table"
    assert table_mounts["caption"] == "Mount Points"
    assert table_mounts["header"] == [
        {"text": "Host", "width": "*"},
        {"text": "Mount Point", "width": "550px"},
        {"text": "Type", "width": "100px"},
        {"text": "Options", "width": "200px"},
    ]
    assert table_mounts["rows"][0] == [
        "ip-172-31-22-196",
        "/",
        "ext4",
        "rw,relatime",
    ]
    assert table_mounts["rows"][1] == [
        "ip-172-31-22-196",
        "/dev",
        "devtmpfs",
        "rw,nosuid,noexec,relatime",
    ]
