import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import MIN_MAGNITUDE, SOURCES


class TestConfig:
    def test_min_magnitude(self):
        assert MIN_MAGNITUDE == 4.5

    def test_usgs_url(self):
        assert "usgs.gov" in SOURCES["usgs"]
        assert "4.5" in SOURCES["usgs"]

    def test_gdacs_url(self):
        assert "gdacs.org" in SOURCES["gdacs"]

    def test_eonet_url(self):
        assert "eonet.gsfc.nasa.gov" in SOURCES["eonet"]


class TestSourceParsers:
    def test_usgs_parse_features_filters_magnitude(self):
        from src.sources.usgs import _parse_features
        feature = {
            "id": "test1",
            "properties": {"mag": 3.0, "title": "Small quake", "time": 0, "url": ""},
            "geometry": {"coordinates": [10.0, 20.0, 0]},
        }
        assert _parse_features([feature]) == []

    def test_usgs_parse_features_accepts_global_coords(self):
        from src.sources.usgs import _parse_features
        # Western hemisphere (e.g. California) — should now be accepted
        feature = {
            "id": "ci12345",
            "properties": {"mag": 5.0, "title": "M 5.0 - California", "time": 1_700_000_000_000, "url": ""},
            "geometry": {"coordinates": [-118.0, 34.0, 10]},
        }
        result = _parse_features([feature])
        assert len(result) == 1
        assert result[0]["event_type"] == "earthquake"

    def test_usgs_severity_red(self):
        from src.sources.usgs import _parse_features
        feature = {
            "id": "x1",
            "properties": {"mag": 7.0, "title": "Big quake", "time": 1_700_000_000_000, "url": ""},
            "geometry": {"coordinates": [100.0, 10.0, 0]},
        }
        assert _parse_features([feature])[0]["severity"] == "red"

    def test_usgs_severity_orange(self):
        from src.sources.usgs import _parse_features
        feature = {
            "id": "x2",
            "properties": {"mag": 6.0, "title": "Med quake", "time": 1_700_000_000_000, "url": ""},
            "geometry": {"coordinates": [100.0, 10.0, 0]},
        }
        assert _parse_features([feature])[0]["severity"] == "orange"

    def test_usgs_severity_green(self):
        from src.sources.usgs import _parse_features
        feature = {
            "id": "x3",
            "properties": {"mag": 5.0, "title": "Small quake", "time": 1_700_000_000_000, "url": ""},
            "geometry": {"coordinates": [100.0, 10.0, 0]},
        }
        assert _parse_features([feature])[0]["severity"] == "green"
