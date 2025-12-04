from x_ray.version import Version


def test_version_comparison():
    v1 = Version.parse("1.2.3")
    v2 = Version([1, 2, 4])
    v3 = Version.parse("1.3.0")
    v4 = Version.parse("2.0.0")
    v5 = Version.parse("1.2.3")

    assert v1 < v2
    assert v2 < v3
    assert v3 < v4
    assert v1 == v5
    assert v4 > v1
    assert v3 >= v2
    assert v2 <= v4
    assert v1 < "1.2.4"
    assert v3 > [1, 2, 9]
