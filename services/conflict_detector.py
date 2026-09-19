"""
TravelPilot — Conflict Detector Service
Exposes conflict detection and schedule fitting functions.
"""

from services.itinerary_service import (
    detect_conflicts,
    detect_all_conflicts,
    can_fit_activity,
    optimize_day_route,
)

__all__ = [
    "detect_conflicts",
    "detect_all_conflicts",
    "can_fit_activity",
    "optimize_day_route",
]
