"""
TravelPilot — Dashboard Router
Aggregated trip dashboard endpoint.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from database.crud import get_trip, get_itinerary, get_bookings, compute_budget_summary
from database.schemas import DashboardResponse, TripResponse, ItineraryDayResponse, BookingResponse, BudgetSummarySchema
from agents.budget_agent import get_daily_budget_breakdown

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/{trip_id}", response_model=DashboardResponse)
async def get_dashboard(trip_id: str, db: AsyncSession = Depends(get_db)):
    """
    Aggregated dashboard: trip + itinerary + bookings + budget + weather.
    """
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    days = await get_itinerary(db, trip_id)
    bookings = await get_bookings(db, trip_id)
    budget = await compute_budget_summary(db, trip_id)

    # Collect weather overview from day data
    weather_overview = {}
    for d in days:
        if d.weather_data:
            weather_overview[str(d.date)] = d.weather_data

    # Backup options: collect alternatives from at-risk activities
    backup_options = []
    for d in days:
        for a in d.activities:
            if a.alternatives:
                backup_options.append({
                    "original_activity": a.name,
                    "day": d.day_number,
                    "date": str(d.date),
                    "alternatives": a.alternatives[:3],
                })

    return DashboardResponse(
        trip=TripResponse.model_validate(trip),
        itinerary=[ItineraryDayResponse.model_validate(d) for d in days],
        bookings=[BookingResponse.model_validate(b) for b in bookings],
        budget_summary=BudgetSummarySchema(**budget) if budget else BudgetSummarySchema(
            total_budget=trip.budget, currency=trip.currency, remaining=trip.budget
        ),
        weather_overview=weather_overview or None,
        backup_options=backup_options,
    )


@router.get("/{trip_id}/budget-breakdown")
async def get_budget_breakdown(trip_id: str, db: AsyncSession = Depends(get_db)):
    """Per-day budget breakdown for chart rendering."""
    days = await get_itinerary(db, trip_id)
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    itinerary_dicts = [
        {
            "day_number": d.day_number,
            "date": str(d.date),
            "theme": d.theme,
            "estimated_cost": d.estimated_cost,
            "activities": [{"estimated_cost": a.estimated_cost, "category": a.category} for a in d.activities],
        }
        for d in days
    ]

    breakdown = get_daily_budget_breakdown(itinerary_dicts, trip.currency)
    summary = await compute_budget_summary(db, trip_id)
    return {"daily": breakdown, "summary": summary}
