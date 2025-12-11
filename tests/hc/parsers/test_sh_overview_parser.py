from x_ray.healthcheck.parsers.sh_overview_parser import SHOverviewParser

CLUSTER_INFO = {
    "type": "SH",
    "map": {
        "shard01": {},
        "shard02": {},
        "config": {},
        "mongos": {
            "setName": "mongos",
            "members": [
                {
                    "host": "M-QTFH0WFXLG:30017",
                },
                {
                    "host": "M-QTFH0WFXLG:30028",
                },
            ],
        },
    },
    "rawResult": {
        "M-QTFH0WFXLG:30017": {"pingLatencySec": 1.649169, "lastPing": {"$date": "2025-12-10T22:18:14.610Z"}},
        "M-QTFH0WFXLG:30028": {"pingLatencySec": 10315140, "lastPing": {"$date": "2025-08-13T12:59:19.978Z"}},
    },
}


def test_sh_overview_parser():
    parser = SHOverviewParser()
    result = parser.parse(CLUSTER_INFO)
    assert len(result) == 2
    overview_table = result[0]
    assert overview_table["caption"] == "Sharded Cluster Overview"
    assert overview_table["rows"][0] == [2, 2, 1]
    mongos_table = result[1]
    assert mongos_table["caption"] == "Component Details - `mongos`"
    assert mongos_table["rows"][0] == ["M-QTFH0WFXLG:30017", 1.649169, {"$date": "2025-12-10T22:18:14.610Z"}]
    assert mongos_table["rows"][1] == ["M-QTFH0WFXLG:30028", 10315140, {"$date": "2025-08-13T12:59:19.978Z"}]
