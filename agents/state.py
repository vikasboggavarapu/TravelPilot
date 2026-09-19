"""
TravelPilot — LangGraph State Definition
The shared state object that flows through all agent nodes.
"""

from typing import TypedDict, Optional, Annotated
from datetime import date
import operator


class ActivityPlan(TypedDict):
    name: str
    category: str
    location: Optional[str]
    address: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    start_time: Optional[str]          # "HH:MM"
    end_time: Optional[str]            # "HH:MM"
    duration_minutes: Optional[int]
    estimated_cost: float
    booking_required: bool
    booking_url: Optional[str]
    description: Optional[str]
    tips: Optional[str]
    alternatives: list[dict]
    status: str                        # confirmed | at_risk | cancelled
    travel_to_next: Optional[dict]     # {distance_km, duration_minutes, mode}


class DayPlan(TypedDict):
    day_number: int
    date: str                          # "YYYY-MM-DD"
    theme: Optional[str]
    weather_summary: Optional[str]
    weather_data: Optional[dict]
    estimated_cost: float
    activities: list[ActivityPlan]
    notes: Optional[str]


class BudgetSummary(TypedDict):
    total_budget: float
    currency: str
    spent_accommodation: float
    spent_transport: float
    spent_food: float
    spent_activities: float
    total_estimated: float
    remaining: float


class Disruption(TypedDict):
    type: str                          # weather | cancellation | conflict | delay
    affected_activity: str
    date: str
    severity: str                      # low | medium | high
    description: str
    alternatives: list[dict]


class TravelState(TypedDict):
    # ── Core Trip Context ──────────────────────────────────
    trip_id: str
    user_id: str

    # ── User Input ─────────────────────────────────────────
    user_message: str

    # ── Trip Request (from wizard) ─────────────────────────
    destination: str
    origin_city: Optional[str]
    start_date: str                    # "YYYY-MM-DD"
    end_date: str                      # "YYYY-MM-DD"
    num_days: int
    num_travelers: int
    budget: float
    currency: str
    interests: list[str]               # food, culture, adventure, nightlife, relaxation
    dietary: list[str]
    hotel_stars: int
    transport_mode: str                # public | taxi | rental_car | walking

    # ── Agent Routing ──────────────────────────────────────
    agent_intent: str                  # plan | modify | query | disrupt

    # ── Generated Itinerary ────────────────────────────────
    itinerary: list[DayPlan]

    # ── Weather ────────────────────────────────────────────
    weather_data: dict                 # keyed by date string

    # ── Disruptions ────────────────────────────────────────
    disruptions: list[Disruption]

    # ── Budget ─────────────────────────────────────────────
    budget_summary: BudgetSummary

    # ── Hotel context ─────────────────────────────────────
    hotel_info: Optional[dict]         # name, lat, lon, estimated_cost_per_night

    # ── Conversation ──────────────────────────────────────
    conversation_history: list[dict]   # [{role, content}]
    gemini_interaction_id: Optional[str]

    # ── Output ────────────────────────────────────────────
    response: str
    itinerary_updated: bool
    budget_updated: bool
    error: Optional[str]
