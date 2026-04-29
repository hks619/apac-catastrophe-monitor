import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import REGIONS

APAC = REGIONS["APAC"]["bbox"]
EU   = REGIONS["Europe"]["bbox"]
NA   = REGIONS["North America"]["bbox"]
SA   = REGIONS["South America"]["bbox"]
AF   = REGIONS["Africa"]["bbox"]
ANT  = REGIONS["Antarctica"]["bbox"]


def in_bbox(bbox, lat, lon) -> bool:
    return (
        bbox["lat_min"] <= lat <= bbox["lat_max"] and
        bbox["lon_min"] <= lon <= bbox["lon_max"]
    )


class TestApacBbox:
    def test_tokyo(self):       assert in_bbox(APAC, 35.68,  139.69)
    def test_sydney(self):      assert in_bbox(APAC, -33.87, 151.21)
    def test_jakarta(self):     assert in_bbox(APAC, -6.21,  106.85)
    def test_manila(self):      assert in_bbox(APAC, 14.60,  120.98)
    def test_london_out(self):  assert not in_bbox(APAC, 51.51,  -0.13)
    def test_new_york_out(self): assert not in_bbox(APAC, 40.71, -74.01)
    def test_dubai_out(self):   assert not in_bbox(APAC, 25.20,  55.30)
    def test_south_pole_out(self): assert not in_bbox(APAC, -90.0, 135.0)
    def test_north_pole_out(self): assert not in_bbox(APAC, 90.0, 135.0)


class TestEuropeBbox:
    def test_london(self):      assert in_bbox(EU, 51.51,  -0.13)
    def test_rome(self):        assert in_bbox(EU, 41.90,  12.50)
    def test_istanbul(self):    assert in_bbox(EU, 41.01,  28.98)
    def test_tokyo_out(self):   assert not in_bbox(EU, 35.68, 139.69)
    def test_new_york_out(self): assert not in_bbox(EU, 40.71, -74.01)


class TestNorthAmericaBbox:
    def test_new_york(self):    assert in_bbox(NA, 40.71,  -74.01)
    def test_mexico_city(self): assert in_bbox(NA, 19.43,  -99.13)
    def test_toronto(self):     assert in_bbox(NA, 43.65,  -79.38)
    def test_tokyo_out(self):   assert not in_bbox(NA, 35.68, 139.69)
    def test_london_out(self):  assert not in_bbox(NA, 51.51,  -0.13)


class TestSouthAmericaBbox:
    def test_lima(self):        assert in_bbox(SA, -12.05,  -77.04)
    def test_buenos_aires(self): assert in_bbox(SA, -34.60, -58.38)
    def test_bogota(self):      assert in_bbox(SA, 4.71,   -74.07)
    def test_new_york_out(self): assert not in_bbox(SA, 40.71, -74.01)


class TestAfricaBbox:
    def test_nairobi(self):     assert in_bbox(AF, -1.29,   36.82)
    def test_cairo(self):       assert in_bbox(AF, 30.04,   31.24)
    def test_lagos(self):       assert in_bbox(AF, 6.52,    3.38)
    def test_london_out(self):  assert not in_bbox(AF, 51.51,  -0.13)


class TestAntarcticaBbox:
    def test_south_pole(self):  assert in_bbox(ANT, -90.0,   0.0)
    def test_palmer(self):      assert in_bbox(ANT, -64.77, -64.05)
    def test_sydney_out(self):  assert not in_bbox(ANT, -33.87, 151.21)


class TestRegionsExist:
    def test_all_regions_present(self):
        for r in ("Global", "APAC", "Europe", "Africa", "North America", "South America", "Antarctica"):
            assert r in REGIONS
    def test_global_has_no_bbox(self):
        assert REGIONS["Global"]["bbox"] is None
    def test_all_regions_have_center(self):
        for r in REGIONS.values():
            assert "center" in r
