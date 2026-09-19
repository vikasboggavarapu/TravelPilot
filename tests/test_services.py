"""
Unit tests for TravelPilot services: itinerary logic, conflict detection, and export.
"""

import pytest
from services.itinerary_service import detect_conflicts, detect_all_conflicts, can_fit_activity, optimize_day_route
from services.conflict_detector import detect_conflicts as cd_conflicts
from services.export_service import generate_trip_pdf


def test_conflict_detection_overlap():
    day = {
        "day_number": 1,
        "date": "2026-06-01",
        "activities": [
            {"name": "Activity 1", "start_time": "10:00", "end_time": "12:00", "category": "culture"},
            {"name": "Activity 2", "start_time": "11:30", "end_time": "13:00", "category": "food"},
        ]
    }
    conflicts = detect_conflicts(day)
    assert len(conflicts) == 1
    assert conflicts[0]["type"] == "overlap"
    assert "Activity 1" in conflicts[0]["message"]


def test_conflict_detection_clear():
    day = {
        "day_number": 1,
        "date": "2026-06-01",
        "activities": [
            {"name": "Morning Louvre", "start_time": "09:30", "end_time": "12:00", "category": "culture"},
            {"name": "Bistro Lunch", "start_time": "12:30", "end_time": "14:00", "category": "food"},
            {"name": "Afternoon Stroll", "start_time": "14:30", "end_time": "17:00", "category": "culture"},
        ]
    }
    conflicts = detect_conflicts(day)
    assert len(conflicts) == 0


def test_can_fit_activity():
    day = {
        "day_number": 1,
        "activities": [
            {"name": "Morning Activity", "start_time": "10:00", "end_time": "12:00"},
            {"name": "Evening Activity", "start_time": "18:00", "end_time": "20:00"},
        ]
    }
    new_act = {"name": "Afternoon Tea", "duration_minutes": 60}
    res = can_fit_activity(day, new_act)
    assert res["fits"] is True
    assert res["suggested_time"] is not None


def test_pdf_generation():
    trip = {
        "destination": "Rome",
        "start_date": "2026-07-01",
        "end_date": "2026-07-03",
        "num_travelers": 2,
        "budget": 1200.0,
        "currency": "EUR",
    }
    itinerary = [
        {
            "day_number": 1,
            "date": "2026-07-01",
            "theme": "Colosseum & Ancient Rome",
            "weather_summary": "Sunny, 28°C",
            "estimated_cost": 90.0,
            "notes": "Book Colosseum underground tour in advance.",
            "activities": [
                {
                    "name": "Colosseum",
                    "category": "landmark",
                    "location": "Piazza del Colosseo",
                    "start_time": "09:30",
                    "end_time": "12:00",
                    "estimated_cost": 36.0,
                    "tips": "Skip-the-line tickets recommended.",
                    "status": "confirmed",
                },
                {
                    "name": "Trattoria Romana",
                    "category": "food",
                    "location": "Monti",
                    "start_time": "12:30",
                    "end_time": "14:00",
                    "estimated_cost": 45.0,
                    "tips": "Try the Cacio e Pepe.",
                    "status": "confirmed",
                }
            ]
        }
    ]
    budget = {
        "total_budget": 1200.0,
        "currency": "EUR",
        "spent_accommodation": 400.0,
        "spent_transport": 100.0,
        "spent_food": 250.0,
        "spent_activities": 180.0,
        "total_estimated": 930.0,
        "remaining": 270.0,
    }
    pdf_bytes = generate_trip_pdf(trip, itinerary, budget, [])
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 500
    assert pdf_bytes.startswith(b"%PDF")


@pytest.mark.asyncio
async def test_compute_budget_summary():
    from unittest.mock import AsyncMock, MagicMock
    from datetime import date
    from database.crud import compute_budget_summary

    mock_trip = MagicMock()
    mock_trip.trip_id = "trip-barcelona"
    mock_trip.budget = 2500.0
    mock_trip.currency = "EUR"
    mock_trip.start_date = date(2026, 8, 1)
    mock_trip.end_date = date(2026, 8, 5)  # 5 days, 4 nights
    mock_trip.num_travelers = 2
    mock_trip.trip_preferences = {
        "hotel_info": {
            "name": "Hotel Arts",
            "estimated_cost_per_night": 160.0,
        }
    }

    mock_db = AsyncMock()

    # Call 1: trip query
    res1 = MagicMock()
    res1.scalar_one_or_none.return_value = mock_trip

    # Call 2: activity categories
    res2 = MagicMock()
    res2.all.return_value = [
        ("dinner", 80.0),
        ("lunch", 50.0),
        ("landmark", 60.0),
        ("metro", 15.0),
    ]

    # Call 3: bookings
    res3 = MagicMock()
    res3.all.return_value = []

    mock_db.execute.side_effect = [res1, res2, res3]

    summary = await compute_budget_summary(mock_db, "trip-barcelona")

    # Spent accommodation: 4 nights * 160.0 = 640.0
    assert summary["spent_accommodation"] == 640.0
    # Spent food: dinner (80) + lunch (50) = 130.0
    assert summary["spent_food"] == 130.0
    # Spent transport: metro = 15.0
    assert summary["spent_transport"] == 15.0
    # Spent activities: landmark = 60.0
    assert summary["spent_activities"] == 60.0
    # Total estimated: 640 + 130 + 15 + 60 = 845.0
    assert summary["total_estimated"] == 845.0
    assert summary["remaining"] == 2500.0 - 845.0
    assert summary["currency"] == "EUR"


def test_currency_service():
    from services.currency_service import (
        get_currency_scale,
        get_currency_symbol,
        scale_amount,
        format_money,
    )

    assert get_currency_scale("INR") == 88.0
    assert get_currency_scale("USD") == 1.0
    assert get_currency_scale("EUR") == 0.92
    assert get_currency_symbol("INR") == "₹"
    assert get_currency_symbol("EUR") == "€"
    assert get_currency_symbol("USD") == "$"
    assert scale_amount(100.0, "INR") == 8800.0
    assert format_money(150000, "INR") == "₹150,000"


@pytest.mark.asyncio
async def test_compute_budget_summary_inr_scaling():
    from unittest.mock import AsyncMock, MagicMock
    from datetime import date
    from database.crud import compute_budget_summary

    mock_trip = MagicMock()
    mock_trip.id = "trip-paris-inr"
    mock_trip.budget = 180000.0
    mock_trip.currency = "INR"
    mock_trip.start_date = date(2026, 7, 1)
    mock_trip.end_date = date(2026, 7, 6)  # 6 days, 5 nights
    mock_trip.num_travelers = 2
    mock_trip.trip_preferences = {}  # No explicit hotel, tests fallback scale

    mock_db = AsyncMock()

    res1 = MagicMock()
    res1.scalar_one_or_none.return_value = mock_trip

    res2 = MagicMock()
    res2.all.return_value = [
        ("food", 25000.0),
        ("landmark", 12000.0),
    ]

    res3 = MagicMock()
    res3.all.return_value = []

    mock_db.execute.side_effect = [res1, res2, res3]

    summary = await compute_budget_summary(mock_db, "trip-paris-inr")

    assert summary["currency"] == "INR"
    assert summary["total_budget"] == 180000.0
    # Accommodation should scale with INR (5 nights * (180000 * 0.35 / 5) = 63,000)
    assert summary["spent_accommodation"] > 10000.0  # Not capped at raw 180 USD!
    # Transport allowance should scale with INR (15 * 88 * 6 * 2 = 15,840)
    assert summary["spent_transport"] > 5000.0  # Not raw USD $90!
    assert summary["remaining"] > 0


