"""
TravelPilot — Itinerary Service
Business logic for itinerary building, optimization, and conflict detection.
"""

from datetime import datetime, time
from agents.state import DayPlan, ActivityPlan
from tools.maps_tool import optimize_route, estimate_travel_time


def detect_conflicts(day: DayPlan) -> list[dict]:
    """
    Detect scheduling conflicts within a single day.
    Returns a list of conflict descriptions.
    """
    conflicts = []
    activities = sorted(
        [a for a in day.get("activities", []) if a.get("start_time") and a.get("end_time")],
        key=lambda a: a["start_time"]
    )

    for i in range(len(activities) - 1):
        a = activities[i]
        b = activities[i + 1]

        a_end = _parse_time(a["end_time"])
        b_start = _parse_time(b["start_time"])

        if a_end and b_start and a_end > b_start:
            conflicts.append({
                "type": "overlap",
                "day": day["day_number"],
                "activity_a": a["name"],
                "activity_b": b["name"],
                "a_end": a["end_time"],
                "b_start": b["start_time"],
                "message": f"⚠️ '{a['name']}' ends at {a['end_time']} but '{b['name']}' starts at {b['start_time']}",
            })
        elif a_end and b_start:
            gap_minutes = int((
                datetime.combine(datetime.today(), b_start) -
                datetime.combine(datetime.today(), a_end)
            ).total_seconds() / 60)

            # Flag insufficient travel buffer
            travel = None
            if a.get("latitude") and b.get("latitude"):
                travel = estimate_travel_time(
                    a["latitude"], a["longitude"],
                    b["latitude"], b["longitude"],
                    mode="public_transport"
                )

            if travel and gap_minutes < travel["duration_minutes"]:
                conflicts.append({
                    "type": "insufficient_buffer",
                    "day": day["day_number"],
                    "activity_a": a["name"],
                    "activity_b": b["name"],
                    "gap_minutes": gap_minutes,
                    "travel_needed": travel["duration_minutes"],
                    "message": (
                        f"ℹ️ Only {gap_minutes} min between '{a['name']}' and '{b['name']}', "
                        f"but ~{travel['duration_minutes']} min travel needed."
                    ),
                })

    return conflicts


def detect_all_conflicts(itinerary: list[DayPlan]) -> list[dict]:
    """Run conflict detection across all days."""
    all_conflicts = []
    for day in itinerary:
        all_conflicts.extend(detect_conflicts(day))
    return all_conflicts


def optimize_day_route(day: DayPlan) -> DayPlan:
    """
    Reorder activities in a day to minimize travel using nearest-neighbor.
    Preserves morning/evening anchor activities (hotel check-in, dinner).
    """
    activities = day.get("activities", [])

    # Separate anchored (transport/hotel/dinner) from flexible
    anchored_start = [a for a in activities if a.get("category") in ("hotel", "flight", "transport") and
                      a.get("start_time") and _parse_time(a["start_time"]) and _parse_time(a["start_time"]).hour < 12]
    anchored_end = [a for a in activities if a.get("category") in ("dinner", "hotel") and
                    a.get("start_time") and _parse_time(a["start_time"]) and _parse_time(a["start_time"]).hour >= 18]
    flexible = [a for a in activities if a not in anchored_start and a not in anchored_end]

    # Optimize only flexible activities
    if flexible and any(a.get("latitude") for a in flexible):
        optimized_flexible = optimize_route(flexible)
    else:
        optimized_flexible = flexible

    optimized_activities = anchored_start + optimized_flexible + anchored_end
    return {**day, "activities": optimized_activities}


def can_fit_activity(day: DayPlan, new_activity: dict) -> dict:
    """
    Check if a new activity can fit into the day's schedule.
    Returns {fits: bool, suggested_time: str, conflicts: list}
    """
    if not new_activity.get("duration_minutes"):
        return {"fits": True, "suggested_time": "flexible", "conflicts": []}

    existing = sorted(
        [a for a in day.get("activities", []) if a.get("start_time") and a.get("end_time")],
        key=lambda a: a["start_time"]
    )

    duration = new_activity["duration_minutes"]
    needed_gap = duration + 30  # 30 min buffer

    # Find gaps between activities
    slots = []
    prev_end = "09:00"

    for act in existing:
        gap = _time_gap_minutes(prev_end, act["start_time"])
        if gap >= needed_gap:
            slots.append(prev_end)
        prev_end = act["end_time"]

    # Check after last activity
    if _time_gap_minutes(prev_end, "21:00") >= needed_gap:
        slots.append(prev_end)

    if slots:
        return {
            "fits": True,
            "suggested_time": slots[0],
            "available_slots": slots,
            "conflicts": [],
        }
    else:
        return {
            "fits": False,
            "suggested_time": None,
            "conflicts": ["No available time slot found in the current schedule."],
        }


def _parse_time(time_str: str) -> time | None:
    """Parse 'HH:MM' string to time object."""
    try:
        h, m = time_str.split(":")
        return time(int(h), int(m))
    except Exception:
        return None


def _time_gap_minutes(start_str: str, end_str: str) -> int:
    """Calculate gap in minutes between two 'HH:MM' strings."""
    try:
        s = _parse_time(start_str)
        e = _parse_time(end_str)
        if s and e:
            return int((
                datetime.combine(datetime.today(), e) -
                datetime.combine(datetime.today(), s)
            ).total_seconds() / 60)
    except Exception:
        pass
    return 0
