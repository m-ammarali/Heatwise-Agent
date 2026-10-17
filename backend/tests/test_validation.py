import datetime

import pytest
from pydantic import ValidationError

from models.schemas import AnalyzeRequest, LocationIn


def test_valid_location_accepted():
    loc = LocationIn(name="Site A", latitude=33.4484, longitude=-112.0740)
    assert loc.name == "Site A"


def test_out_of_range_latitude_rejected():
    with pytest.raises(ValidationError):
        LocationIn(name="Bad", latitude=999.0, longitude=-112.0)


def test_non_us_location_now_accepted():
    # Open-data providers are global, so the old US-only restriction is gone.
    loc = LocationIn(name="Lahore Fort", latitude=31.5889, longitude=74.3147)
    assert loc.longitude == 74.3147


def test_out_of_range_longitude_still_rejected():
    with pytest.raises(ValidationError):
        LocationIn(name="Bad", latitude=10.0, longitude=999.0)


def test_analyze_request_requires_at_least_one_location():
    with pytest.raises(ValidationError):
        AnalyzeRequest(locations=[], analysis_date=datetime.date(2026, 7, 15))


def test_analyze_request_caps_at_five_locations():
    locs = [LocationIn(name=f"Site {i}", latitude=33.0, longitude=-112.0) for i in range(6)]
    with pytest.raises(ValidationError):
        AnalyzeRequest(locations=locs, analysis_date=datetime.date(2026, 7, 15))
