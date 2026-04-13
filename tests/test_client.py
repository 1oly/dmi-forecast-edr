"""
Test suite for dmi-forecast-edr client.

Usage:
    # Run directly (no dependencies beyond the package itself):
    python tests/test_client.py

    # Run with pytest (requires: pip install pytest):
    python -m pytest tests/test_client.py -v

    # Include live API tests (requires internet):
    python tests/test_client.py --run-live
    python -m pytest tests/test_client.py -v --run-live
"""

import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Bootstrap: ensure package is importable and stub missing deps
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import tenacity  # noqa: F401
except ImportError:
    import types
    tenacity = types.ModuleType("tenacity")
    tenacity.retry = lambda **kw: (lambda fn: fn)
    tenacity.stop_after_attempt = lambda n: None
    tenacity.wait_random = lambda **kw: None
    sys.modules["tenacity"] = tenacity

from dmi_forecast_edr.enums import Collection
from dmi_forecast_edr.client import (
    DMIForecastEDRClient,
    hour_rounder,
    _construct_datetime_argument,
    _construct_query,
)

# ---------------------------------------------------------------------------
# Fake API responses used by mocked tests
# ---------------------------------------------------------------------------
FAKE_SINGLE_COLLECTION = {
    "id": "harmonie_dini_sf",
    "parameter_names": {
        "temperature-0m": {"type": "Parameter", "description": "Temperature"},
        "wind-speed": {"type": "Parameter", "description": "Wind speed"},
        "wind-dir": {"type": "Parameter", "description": "Wind direction"},
    },
}

FAKE_ALL_COLLECTIONS = {
    "collections": [
        {"id": "harmonie_dini_sf", "parameter_names": {"temperature-0m": {}, "wind-speed": {}}},
        {"id": "dkss_nsbs", "parameter_names": {"sea-mean-deviation": {}, "current-u": {}, "current-v": {}}},
    ]
}

FAKE_GEOJSON_RESPONSE = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [12.561, 55.715]},
            "properties": {"temperature-0m": 12.3},
        }
    ],
}


# ===========================================================================
# Direct runner — works with zero extra dependencies
# ===========================================================================
def assert_eq(a, b):
    assert a == b, f"{a!r} != {b!r}"

def assert_raises(exc, fn):
    try:
        fn()
        raise AssertionError(f"Expected {exc.__name__}")
    except exc:
        pass


def run_tests():
    passed = 0
    failed = 0

    def run(name, fn):
        nonlocal passed, failed
        try:
            fn()
            print(f"  PASS  {name}")
            passed += 1
        except Exception as e:
            print(f"  FAIL  {name}: {e}")
            failed += 1

    print("=" * 60)
    print("  dmi-forecast-edr test suite")
    print("=" * 60)

    # -- hour_rounder --
    print("\n-- hour_rounder --")
    run("round down",    lambda: assert_eq(hour_rounder(datetime(2024,6,15,10,20)), datetime(2024,6,15,10,0)))
    run("round up",      lambda: assert_eq(hour_rounder(datetime(2024,6,15,10,35)), datetime(2024,6,15,11,0)))
    run("exact hour",    lambda: assert_eq(hour_rounder(datetime(2024,6,15,10,0)),  datetime(2024,6,15,10,0)))
    run("boundary 30",   lambda: assert_eq(hour_rounder(datetime(2024,6,15,10,30)), datetime(2024,6,15,11,0)))
    run("None",          lambda: assert_eq(hour_rounder(None), None))

    # -- _construct_datetime_argument --
    print("\n-- _construct_datetime_argument --")
    run("both None",     lambda: assert_eq(_construct_datetime_argument(None, None), None))
    run("from only",     lambda: assert_eq(
        _construct_datetime_argument(from_time=datetime(2024,6,15,12), instance=True),
        "2024-06-15T12:00:00Z"))
    run("to only",       lambda: assert_eq(
        _construct_datetime_argument(to_time=datetime(2024,6,15,12), instance=False),
        "2024-06-15T12:00:00Z"))
    run("range",         lambda: assert_eq(
        _construct_datetime_argument(datetime(2024,6,15,12), datetime(2024,6,16)),
        "2024-06-15T12:00:00Z/2024-06-16T00:00:00Z"))

    # -- _construct_query --
    print("\n-- _construct_query --")
    run("point query",   lambda: assert_eq(
        _construct_query("test", [12.0, 55.0]),
        ("collections/test/position", {"coords": "POINT(12.0 55.0)"})))
    run("cube query",    lambda: assert_eq(
        _construct_query("test", [9.5, 55.3, 9.7, 55.4]),
        ("collections/test/cube", {"bbox": "9.5,55.3,9.7,55.4"})))
    run("invalid coords", lambda: assert_eq(_construct_query("test", [1.0]), (None, None)))

    # -- Client init --
    print("\n-- Client init --")
    run("valid version",   lambda: assert_eq(DMIForecastEDRClient("v1").version, "v1"))
    run("default version", lambda: assert_eq(DMIForecastEDRClient().version, "v1"))
    run("invalid version", lambda: assert_raises(ValueError, lambda: DMIForecastEDRClient("v99")))

    # -- base_url --
    print("\n-- base_url --")
    run("forecastedr",   lambda: assert_eq(
        DMIForecastEDRClient().base_url("forecastedr"),
        "https://opendataapi.dmi.dk/v1/forecastedr"))
    run("unsupported",   lambda: assert_raises(
        NotImplementedError, lambda: DMIForecastEDRClient().base_url("climatedata")))

    # -- list_collection --
    print("\n-- list_collection --")
    run("count matches enum", lambda: assert_eq(
        len(DMIForecastEDRClient().list_collection()), len(Collection)))

    def _check_known_collections():
        values = [c["value"] for c in DMIForecastEDRClient().list_collection()]
        assert "harmonie_dini_sf" in values
        assert "dkss_nsbs" in values
    run("contains known ids", _check_known_collections)

    # -- get_collection --
    print("\n-- get_collection --")
    run("valid id",   lambda: assert_eq(
        DMIForecastEDRClient.get_collection("harmonie_dini_sf"), Collection.HarmonieDiniSf))
    run("invalid id", lambda: assert_raises(
        ValueError, lambda: DMIForecastEDRClient.get_collection("nope")))

    # -- list_parameters (mocked) --
    print("\n-- list_parameters (mocked) --")

    def _test_list_params_single():
        client = DMIForecastEDRClient()
        with patch.object(client, "_query", return_value=FAKE_SINGLE_COLLECTION) as mq:
            result = client.list_parameters(Collection.HarmonieDiniSf)
            mq.assert_called_once_with(api="forecastedr", service="collections/harmonie_dini_sf", params={})
        assert isinstance(result, list)
        assert sorted(result) == ["temperature-0m", "wind-dir", "wind-speed"]

    def _test_list_params_all():
        client = DMIForecastEDRClient()
        with patch.object(client, "_query", return_value=FAKE_ALL_COLLECTIONS) as mq:
            result = client.list_parameters()
            mq.assert_called_once_with(api="forecastedr", service="collections", params={})
        assert isinstance(result, dict)
        assert "harmonie_dini_sf" in result
        assert "dkss_nsbs" in result
        assert len(result["dkss_nsbs"]) == 3

    run("single collection", _test_list_params_single)
    run("all collections",   _test_list_params_all)

    # -- get_forecast (mocked) --
    print("\n-- get_forecast (mocked) --")

    def _test_forecast_point():
        client = DMIForecastEDRClient()
        with patch.object(client, "_query", return_value=FAKE_GEOJSON_RESPONSE) as mq:
            features = client.get_forecast(
                collection=Collection.HarmonieDiniSf,
                parameter=["temperature-0m"],
                from_time=datetime(2024, 6, 15, 12),
                to_time=datetime(2024, 6, 15, 15),
                coords=[12.561, 55.715],
                crs="crs84",
                f="GeoJSON",
            )
        assert len(features) == 1
        assert features[0]["properties"]["temperature-0m"] == 12.3
        assert "position" in mq.call_args.kwargs["service"]

    def _test_forecast_empty():
        client = DMIForecastEDRClient()
        with patch.object(client, "_query", return_value={}):
            features = client.get_forecast(
                collection=Collection.DkssNsbs,
                parameter=["sea-mean-deviation"],
                coords=[12.0, 55.0],
                f="GeoJSON",
            )
        assert features == []

    run("point query",     _test_forecast_point)
    run("empty response",  _test_forecast_empty)

    # -- Live API tests (optional) --
    if "--run-live" in sys.argv:
        print("\n-- Live API tests --")
        client = DMIForecastEDRClient()

        def _live_list_params():
            p = client.list_parameters(Collection.HarmonieDiniSf)
            assert isinstance(p, list) and len(p) > 0, f"Expected parameters, got {p}"
            print(f"    -> {len(p)} params, e.g. {p[:3]}")

        def _live_list_all():
            r = client.list_parameters()
            assert isinstance(r, dict) and len(r) > 0
            for k, v in r.items():
                print(f"    -> {k}: {len(v)} params")

        def _live_forecast():
            p = client.list_parameters(Collection.HarmonieDiniSf)
            features = client.get_forecast(
                collection=Collection.HarmonieDiniSf,
                parameter=p[:2],
                coords=[12.561, 55.715],
                crs="crs84",
                f="GeoJSON",
            )
            assert isinstance(features, list)
            print(f"    -> {len(features)} features")

        run("list_parameters single", _live_list_params)
        run("list_parameters all",    _live_list_all)
        run("get_forecast point",     _live_forecast)
    else:
        print("\n  (skipping live API tests -- pass --run-live to enable)")

    # -- Summary --
    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed")
    print(f"{'='*60}")
    return failed


# ===========================================================================
# pytest classes (only defined when pytest is available)
# ===========================================================================
try:
    import pytest

    @pytest.fixture
    def client():
        return DMIForecastEDRClient(version="v1")

    class TestHourRounder:
        def test_round_down(self):
            assert hour_rounder(datetime(2024,6,15,10,20,45)) == datetime(2024,6,15,10,0,0)
        def test_round_up(self):
            assert hour_rounder(datetime(2024,6,15,10,35,0)) == datetime(2024,6,15,11,0,0)
        def test_exact_hour(self):
            assert hour_rounder(datetime(2024,6,15,10,0,0)) == datetime(2024,6,15,10,0,0)
        def test_boundary_30(self):
            assert hour_rounder(datetime(2024,6,15,10,30,0)) == datetime(2024,6,15,11,0,0)
        def test_none(self):
            assert hour_rounder(None) is None

    class TestConstructDatetimeArgument:
        def test_both_none(self):
            assert _construct_datetime_argument(None, None) is None
        def test_from_only_instance(self):
            assert _construct_datetime_argument(from_time=datetime(2024,6,15,12), instance=True) == "2024-06-15T12:00:00Z"
        def test_to_only_no_instance(self):
            assert _construct_datetime_argument(to_time=datetime(2024,6,15,12), instance=False) == "2024-06-15T12:00:00Z"
        def test_range(self):
            assert _construct_datetime_argument(datetime(2024,6,15,12), datetime(2024,6,16)) == "2024-06-15T12:00:00Z/2024-06-16T00:00:00Z"

    class TestConstructQuery:
        def test_point(self):
            s, p = _construct_query("harmonie_dini_sf", [12.561, 55.715])
            assert s == "collections/harmonie_dini_sf/position" and p == {"coords": "POINT(12.561 55.715)"}
        def test_cube(self):
            s, p = _construct_query("harmonie_dini_sf", [9.5, 55.3, 9.7, 55.4])
            assert s == "collections/harmonie_dini_sf/cube" and p == {"bbox": "9.5,55.3,9.7,55.4"}
        def test_invalid_coords(self):
            s, p = _construct_query("harmonie_dini_sf", [1.0])
            assert s is None and p is None

    class TestClientInit:
        def test_valid(self):
            assert DMIForecastEDRClient("v1").version == "v1"
        def test_default(self):
            assert DMIForecastEDRClient().version == "v1"
        def test_invalid(self):
            with pytest.raises(ValueError):
                DMIForecastEDRClient("v99")

    class TestBaseUrl:
        def test_forecastedr(self, client):
            assert client.base_url("forecastedr") == "https://opendataapi.dmi.dk/v1/forecastedr"
        def test_unsupported(self, client):
            with pytest.raises(NotImplementedError):
                client.base_url("climatedata")

    class TestListCollection:
        def test_count(self, client):
            assert len(client.list_collection()) == len(Collection)
        def test_known_ids(self, client):
            vals = [c["value"] for c in client.list_collection()]
            assert "harmonie_dini_sf" in vals and "dkss_nsbs" in vals

    class TestGetCollection:
        def test_valid(self):
            assert DMIForecastEDRClient.get_collection("harmonie_dini_sf") == Collection.HarmonieDiniSf
        def test_invalid(self):
            with pytest.raises(ValueError):
                DMIForecastEDRClient.get_collection("nope")

    class TestListParametersMocked:
        @patch.object(DMIForecastEDRClient, "_query", return_value=FAKE_SINGLE_COLLECTION)
        def test_single(self, mock_query, client):
            result = client.list_parameters(Collection.HarmonieDiniSf)
            mock_query.assert_called_once_with(api="forecastedr", service="collections/harmonie_dini_sf", params={})
            assert sorted(result) == ["temperature-0m", "wind-dir", "wind-speed"]

        @patch.object(DMIForecastEDRClient, "_query", return_value=FAKE_ALL_COLLECTIONS)
        def test_all(self, mock_query, client):
            result = client.list_parameters()
            assert isinstance(result, dict) and "harmonie_dini_sf" in result and len(result["dkss_nsbs"]) == 3

    class TestGetForecastMocked:
        @patch.object(DMIForecastEDRClient, "_query", return_value=FAKE_GEOJSON_RESPONSE)
        def test_point(self, mock_query, client):
            features = client.get_forecast(
                collection=Collection.HarmonieDiniSf, parameter=["temperature-0m"],
                from_time=datetime(2024,6,15,12), to_time=datetime(2024,6,15,15),
                coords=[12.561, 55.715], crs="crs84", f="GeoJSON")
            assert len(features) == 1 and features[0]["properties"]["temperature-0m"] == 12.3

        @patch.object(DMIForecastEDRClient, "_query", return_value={})
        def test_empty(self, mock_query, client):
            features = client.get_forecast(
                collection=Collection.DkssNsbs, parameter=["sea-mean-deviation"],
                coords=[12.0, 55.0], f="GeoJSON")
            assert features == []

    @pytest.mark.live
    class TestLiveAPI:
        def test_list_parameters_single(self):
            p = DMIForecastEDRClient().list_parameters(Collection.HarmonieDiniSf)
            assert isinstance(p, list) and len(p) > 0
        def test_list_parameters_all(self):
            r = DMIForecastEDRClient().list_parameters()
            assert isinstance(r, dict) and len(r) > 0
        def test_get_forecast_point(self):
            c = DMIForecastEDRClient()
            p = c.list_parameters(Collection.HarmonieDiniSf)
            f = c.get_forecast(collection=Collection.HarmonieDiniSf, parameter=p[:2],
                               coords=[12.561, 55.715], crs="crs84", f="GeoJSON")
            assert isinstance(f, list)

except ImportError:
    pass  # pytest not installed -- direct runner still works


if __name__ == "__main__":
    sys.exit(run_tests())
