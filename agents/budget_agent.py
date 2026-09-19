"""
TravelPilot — Budget Agent Node
Tracks and recomputes budget estimates across the itinerary.
"""

from agents.state import TravelState, BudgetSummary
from services.currency_service import get_currency_scale


async def budget_agent_node(state: TravelState) -> dict:
    """
    LangGraph node: Recompute budget from current itinerary state.
    """
    itinerary = state.get("itinerary", [])
    total_budget = state.get("budget", 0.0)
    currency = state.get("currency") or "INR"
    existing_summary = state.get("budget_summary", {})
    hotel_info = state.get("hotel_info") or {}
    num_days = state.get("num_days", len(itinerary) or 1)
    num_nights = max(num_days - 1, 1)
    num_travelers = max(state.get("num_travelers", 1), 1)

    if not itinerary:
        return {"budget_updated": False}

    # ── Aggregate costs by category ───────────────────────────────────────────
    food_cost = 0.0
    activity_cost = 0.0
    transport_cost = 0.0

    FOOD_CATEGORIES = {
        "food", "restaurant", "dining", "dinner", "lunch", "breakfast",
        "cafe", "bar", "bistro", "drinks", "brunch", "snack", "bakery"
    }
    TRANSPORT_CATEGORIES = {
        "transport", "transit", "taxi", "cab", "bus", "metro", "subway",
        "train", "flight", "ferry", "shuttle", "car_rental", "transfer"
    }

    for day in itinerary:
        for act in day.get("activities", []):
            category = str(act.get("category", "general")).lower()
            cost = float(act.get("estimated_cost", 0) or 0.0)

            if category in FOOD_CATEGORIES:
                food_cost += cost
            elif category in TRANSPORT_CATEGORIES:
                transport_cost += cost
            else:
                activity_cost += cost

    # Accommodation calculation
    scale = get_currency_scale(currency)
    if existing_summary.get("spent_accommodation", 0.0) > 0:
        accommodation_cost = float(existing_summary["spent_accommodation"])
    elif hotel_info.get("estimated_cost_per_night"):
        accommodation_cost = round(float(hotel_info["estimated_cost_per_night"]) * num_nights, 2)
    else:
        default_nightly = min(max((total_budget * 0.35) / num_nights, 40.0 * scale), 350.0 * scale)
        accommodation_cost = round(default_nightly * num_nights, 2)

    # Transport fallback
    if transport_cost == 0.0:
        if existing_summary.get("spent_transport", 0.0) > 0:
            transport_cost = float(existing_summary["spent_transport"])
        else:
            transport_cost = round(15.0 * scale * num_days * num_travelers, 2)

    total_estimated = round(accommodation_cost + transport_cost + food_cost + activity_cost, 2)
    remaining = round(total_budget - total_estimated, 2)

    summary: BudgetSummary = {
        "total_budget": total_budget,
        "currency": currency,
        "spent_accommodation": accommodation_cost,
        "spent_transport": transport_cost,
        "spent_food": round(food_cost, 2),
        "spent_activities": round(activity_cost, 2),
        "total_estimated": total_estimated,
        "remaining": remaining,
    }

    return {
        "budget_summary": summary,
        "budget_updated": True,
    }


def get_budget_alert(budget_summary: BudgetSummary) -> str | None:
    """
    Returns a budget alert message if over/near budget.
    Returns None if within comfortable range.
    """
    remaining = budget_summary.get("remaining", 0)
    total = budget_summary.get("total_budget", 1)
    pct_used = (total - remaining) / total * 100 if total > 0 else 0

    if remaining < 0:
        return f"⚠️ Over budget by {budget_summary['currency']} {abs(remaining):.0f}! Consider removing some activities."
    elif pct_used > 90:
        return f"⚠️ Almost at budget ({pct_used:.0f}% used). Very little room for extras."
    elif pct_used > 80:
        return f"ℹ️ {pct_used:.0f}% of budget allocated. Keep an eye on spending."
    return None


def get_daily_budget_breakdown(itinerary: list, currency: str = "INR") -> list[dict]:
    """
    Per-day budget summary for the frontend chart.
    """
    breakdown = []
    for day in itinerary:
        day_total = sum(float(a.get("estimated_cost", 0)) for a in day.get("activities", []))
        if day_total == 0.0 and day.get("estimated_cost", 0) > 0:
            day_total = float(day["estimated_cost"])
        breakdown.append({
            "day": day["day_number"],
            "date": day["date"],
            "theme": day.get("theme", f"Day {day['day_number']}"),
            "estimated_cost": round(day_total, 2),
            "currency": currency,
        })
    return breakdown
