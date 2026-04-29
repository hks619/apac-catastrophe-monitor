import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import APAC_BBOX, APAC_ISO3


def in_apac_bbox(lat: float, lon: float) -> bool:
    b = APAC_BBOX
    return b["lat_min"] <= lat <= b["lat_max"] and b["lon_min"] <= lon <= b["lon_max"]


class TestApacBbox:
    def test_tokyo(self):
        assert in_apac_bbox(35.68, 139.69)

    def test_sydney(self):
        assert in_apac_bbox(-33.87, 151.21)

    def test_jakarta(self):
        assert in_apac_bbox(-6.21, 106.85)

    def test_manila(self):
        assert in_apac_bbox(14.60, 120.98)

    def test_london_excluded(self):
        assert not in_apac_bbox(51.51, -0.13)

    def test_new_york_excluded(self):
        assert not in_apac_bbox(40.71, -74.01)

    def test_dubai_excluded(self):
        # lon 55.3 is west of our 60° boundary
        assert not in_apac_bbox(25.20, 55.30)

    def test_south_pole_excluded(self):
        assert not in_apac_bbox(-90.0, 135.0)

    def test_north_pole_excluded(self):
        assert not in_apac_bbox(90.0, 135.0)

    def test_bbox_southern_edge(self):
        assert in_apac_bbox(APAC_BBOX["lat_min"], 135.0)

    def test_bbox_eastern_edge(self):
        assert in_apac_bbox(35.0, APAC_BBOX["lon_max"])

    def test_bbox_western_edge(self):
        assert in_apac_bbox(35.0, APAC_BBOX["lon_min"])


class TestApacIso3:
    def test_japan(self):
        assert "JPN" in APAC_ISO3

    def test_australia(self):
        assert "AUS" in APAC_ISO3

    def test_indonesia(self):
        assert "IDN" in APAC_ISO3

    def test_philippines(self):
        assert "PHL" in APAC_ISO3

    def test_usa_excluded(self):
        assert "USA" not in APAC_ISO3

    def test_uk_excluded(self):
        assert "GBR" not in APAC_ISO3

    def test_france_excluded(self):
        assert "FRA" not in APAC_ISO3

    def test_count_reasonable(self):
        assert 40 <= len(APAC_ISO3) <= 70
