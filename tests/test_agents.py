"""
Unit tests for TravelPilot LangGraph agents.
"""

import pytest
from agents.planner_agent import plan_trip_node
from agents.state import TravelState


@pytest.mark.asyncio
async def test_planner_agent_node_execution():
    state: TravelState = {
        "trip_id": "test-123",
        "user_id": "user-123",
        "user_message": "Plan my trip to Paris",
        "destination": "Paris",
        "origin_city": "London",
        "start_date": "2026-06-01",
        "end_date": "2026-06-03",
        "num_days": 3,
        "num_travelers": 2,
        "budget": 1500.0,
        "currency": "EUR",
        "interests": ["culture", "food"],
        "dietary": [],
        "hotel_stars": 4,
        "transport_mode": "public",
        "agent_intent": "plan",
        "itinerary": [],
        "weather_data": {},
        "disruptions": [],
        "budget_summary": {},
        "hotel_info": None,
        "conversation_history": [],
        "gemini_interaction_id": None,
        "response": "",
        "itinerary_updated": False,
        "budget_updated": False,
        "error": None,
    }

    result = await plan_trip_node(state)
    assert result is not None
    assert result.get("itinerary_updated") is True
    assert len(result.get("itinerary", [])) == 3
    assert result.get("budget_summary") is not None
    assert result.get("budget_summary")["total_budget"] == 1500.0


@pytest.mark.asyncio
async def test_nlq_agent_core_questions():
    from agents.nlq_agent import nlq_agent_node

    itinerary_mock = [
        {
            "day_number": 1,
            "date": "2026-06-01",
            "theme": "Arrival & Landmarks",
            "activities": [
                {
                    "name": "Eiffel Tower",
                    "category": "landmark",
                    "start_time": "09:30",
                    "end_time": "12:00",
                    "location": "Champ de Mars",
                    "latitude": 48.8584,
                    "longitude": 2.2945,
                    "estimated_cost": 28.0,
                    "alternatives": [{"name": "Montparnasse Tower", "reason": "Sheltered panoramic alternative"}],
                },
                {
                    "name": "Bistro Lunch",
                    "category": "food",
                    "start_time": "12:30",
                    "end_time": "14:00",
                    "location": "Rue Cler",
                    "latitude": 48.8566,
                    "longitude": 2.3050,
                    "estimated_cost": 30.0,
                },
                {
                    "name": "Evening Seine Stroll",
                    "category": "dinner",
                    "start_time": "19:00",
                    "end_time": "21:30",
                    "location": "Pont Neuf",
                    "latitude": 48.8566,
                    "longitude": 2.3412,
                    "estimated_cost": 40.0,
                },
            ],
        },
        {
            "day_number": 2,
            "date": "2026-06-02",
            "theme": "Museums & Historic Quarters",
            "activities": [
                {
                    "name": "Louvre Museum",
                    "category": "culture",
                    "start_time": "09:30",
                    "end_time": "12:30",
                    "location": "Palais Royal",
                    "latitude": 48.8606,
                    "longitude": 2.3376,
                    "estimated_cost": 22.0,
                    "tips": "Book online in advance.",
                    "alternatives": [{"name": "Musee d'Orsay", "reason": "Impressionist masterworks alternative"}],
                }
            ],
        }
    ]

    base_state: TravelState = {
        "trip_id": "test-123",
        "user_id": "user-123",
        "user_message": "",
        "destination": "Paris",
        "origin_city": "London",
        "start_date": "2026-06-01",
        "end_date": "2026-06-03",
        "num_days": 3,
        "num_travelers": 2,
        "budget": 1500.0,
        "currency": "EUR",
        "interests": ["culture", "food"],
        "dietary": [],
        "hotel_stars": 4,
        "transport_mode": "public",
        "agent_intent": "query",
        "itinerary": itinerary_mock,
        "weather_data": {"2026-06-02": {"condition": "Sunny", "temp_high": 24}},
        "disruptions": [],
        "budget_summary": {"total_budget": 1500.0, "currency": "EUR", "spent_accommodation": 400.0, "spent_transport": 100.0, "spent_food": 300.0, "spent_activities": 200.0, "total_estimated": 1000.0, "remaining": 500.0},
        "hotel_info": {"name": "Hotel Le Marais", "neighborhood": "Le Marais", "latitude": 48.8570, "longitude": 2.3580, "estimated_cost_per_night": 140.0},
        "conversation_history": [],
        "gemini_interaction_id": None,
        "response": "",
        "itinerary_updated": False,
        "budget_updated": False,
        "error": None,
    }

    # 1. "What should I do tomorrow morning?"
    state1 = {**base_state, "user_message": "What should I do tomorrow morning?"}
    res1 = await nlq_agent_node(state1)
    assert "Morning" in res1["response"] or "Louvre" in res1["response"]

    # 2. "Can I fit this activity into today's schedule?"
    state2 = {**base_state, "user_message": "Can I fit this activity into today's schedule?"}
    res2 = await nlq_agent_node(state2)
    assert "schedule" in res2["response"].lower()
    assert "fit" in res2["response"].lower() or "window" in res2["response"].lower()

    # 3. "Which activities are close to my hotel?"
    state3 = {**base_state, "user_message": "Which activities are close to my hotel?"}
    res3 = await nlq_agent_node(state3)
    assert "hotel" in res3["response"].lower()
    assert "km" in res3["response"] or "min walk" in res3["response"]

    # 4. "What happens to my itinerary if this booking is cancelled?"
    state4 = {**base_state, "user_message": "What happens to my itinerary if this booking is cancelled?"}
    res4 = await nlq_agent_node(state4)
    assert "cancell" in res4["response"].lower()
    assert "backup" in res4["response"].lower() or "alternative" in res4["response"].lower()


@pytest.mark.asyncio
async def test_budget_agent_breakdown_and_categories():
    from agents.budget_agent import budget_agent_node, get_daily_budget_breakdown

    test_state: TravelState = {
        "trip_id": "budget-test-1",
        "user_id": "user-1",
        "user_message": "Check my budget",
        "destination": "Rome",
        "origin_city": "Berlin",
        "start_date": "2026-07-01",
        "end_date": "2026-07-04",
        "num_days": 4,
        "num_travelers": 2,
        "budget": 2000.0,
        "currency": "EUR",
        "interests": ["history", "food"],
        "dietary": [],
        "hotel_stars": 4,
        "transport_mode": "public",
        "agent_intent": "query",
        "itinerary": [
            {
                "day_number": 1,
                "date": "2026-07-01",
                "theme": "Arrival & Colosseum",
                "estimated_cost": 130.0,
                "activities": [
                    {"name": "Colosseum", "category": "landmark", "estimated_cost": 30.0},
                    {"name": "Trattoria Lunch", "category": "lunch", "estimated_cost": 40.0},
                    {"name": "Gelato Cafe", "category": "cafe", "estimated_cost": 10.0},
                    {"name": "Evening Dinner", "category": "dinner", "estimated_cost": 50.0},
                ],
            },
            {
                "day_number": 2,
                "date": "2026-07-02",
                "theme": "Vatican City",
                "estimated_cost": 85.0,
                "activities": [
                    {"name": "Vatican Museum", "category": "museum", "estimated_cost": 35.0},
                    {"name": "Metro Pass", "category": "metro", "estimated_cost": 10.0},
                    {"name": "Pizzeria Dinner", "category": "restaurant", "estimated_cost": 40.0},
                ],
            },
        ],
        "weather_data": {},
        "disruptions": [],
        "budget_summary": {},
        "hotel_info": {
            "name": "Hotel Quirinale",
            "neighborhood": "Monti",
            "estimated_cost_per_night": 120.0,
        },
        "conversation_history": [],
        "gemini_interaction_id": None,
        "response": "",
        "itinerary_updated": False,
        "budget_updated": False,
        "error": None,
    }

    res = await budget_agent_node(test_state)
    assert res.get("budget_updated") is True
    summary = res["budget_summary"]

    # Food should aggregate: lunch (40) + cafe (10) + dinner (50) + restaurant (40) = 140
    assert summary["spent_food"] == 140.0

    # Activities: Colosseum (30) + Vatican Museum (35) = 65
    assert summary["spent_activities"] == 65.0

    # Transport: Metro Pass = 10.0
    assert summary["spent_transport"] == 10.0

    # Accommodation: 3 nights * 120.0 = 360.0
    assert summary["spent_accommodation"] == 360.0

    # Total estimated = 140 + 65 + 10 + 360 = 575.0
    assert summary["total_estimated"] == 575.0
    assert summary["remaining"] == 2000.0 - 575.0
    assert summary["currency"] == "EUR"

    # Test daily breakdown
    daily = get_daily_budget_breakdown(test_state["itinerary"], "EUR")
    assert len(daily) == 2
    assert daily[0]["estimated_cost"] == 130.0
    assert daily[1]["estimated_cost"] == 85.0


