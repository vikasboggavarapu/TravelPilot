"""
Unit tests for TravelPilot external tools.
Verifies geocoding, distance estimation, route optimization, weather, and fallback data.
"""

import pytest
from tools.maps_tool import haversine_distance, estimate_travel_time, optimize_route, geocode
from tools.duckduckgo_tool import search_location
from tools.weather_tool import get_forecast, get_trip_weather_overview


def test_haversine_distance():
    # Distance between Eiffel Tower and Louvre Museum ~ 3.5 km
    eiffel = (48.8584, 2.2945)
    louvre = (48.8606, 2.3376)
    dist = haversine_distance(eiffel[0], eiffel[1], louvre[0], louvre[1])
    assert 3.0 < dist < 4.0


def test_estimate_travel_time():
    result = estimate_travel_time(48.8584, 2.2945, 48.8606, 2.3376, mode="walking")
    assert "distance_km" in result
    assert "duration_minutes" in result
    assert result["distance_km"] > 0
    assert result["duration_minutes"] > 0


def test_optimize_route():
    activities = [
        {"name": "Stop A", "latitude": 48.8584, "longitude": 2.2945},
        {"name": "Stop B", "latitude": 48.8606, "longitude": 2.3376},
        {"name": "Stop C", "latitude": 48.8530, "longitude": 2.3499},
    ]
    optimized = optimize_route(activities)
    assert len(optimized) == 3
    assert all("name" in a for a in optimized)


def test_weather_overview():
    weather = get_trip_weather_overview("Paris", "2026-06-01", "2026-06-03")
    assert isinstance(weather, dict)
    assert len(weather) == 3
    assert "2026-06-01" in weather
    assert "condition" in weather["2026-06-01"]


def test_geocode_fallback():
    coords = geocode("Paris, France")
    assert coords is not None
    lat, lon = coords
    assert isinstance(lat, float)
    assert isinstance(lon, float)
