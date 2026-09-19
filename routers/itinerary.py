"""
TravelPilot — Itinerary Router
CRUD endpoints for trip itineraries.
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from database.crud import get_trip, get_itinerary, get_day, compute_budget_summary
from database.schemas import ItineraryDayResponse
from services.itinerary_service import detect_all_conflicts, can_fit_activity
from services.export_service import generate_trip_pdf

router = APIRouter(prefix="/itinerary", tags=["itinerary"])


@router.get("/{trip_id}", response_model=list[ItineraryDayResponse])
async def get_full_itinerary(trip_id: str, db: AsyncSession = Depends(get_db)):
    """Get the full day-by-day itinerary for a trip."""
    days = await get_itinerary(db, trip_id)
    if not days:
        return []
    return days


@router.get("/{trip_id}/day/{day_number}", response_model=ItineraryDayResponse)
async def get_single_day(trip_id: str, day_number: int, db: AsyncSession = Depends(get_db)):
    """Get a single day's itinerary."""
    day = await get_day(db, trip_id, day_number)
    if not day:
        raise HTTPException(status_code=404, detail=f"Day {day_number} not found")
    return day


@router.get("/{trip_id}/conflicts")
async def check_conflicts(trip_id: str, db: AsyncSession = Depends(get_db)):
    """Detect scheduling conflicts across all days."""
    days = await get_itinerary(db, trip_id)
    if not days:
        return {"conflicts": []}

    itinerary_dicts = [
        {
            "day_number": d.day_number,
            "date": str(d.date),
            "activities": [
                {
                    "name": a.name,
                    "category": a.category,
                    "start_time": str(a.start_time) if a.start_time else None,
                    "end_time": str(a.end_time) if a.end_time else None,
                    "latitude": a.latitude,
                    "longitude": a.longitude,
                    "estimated_cost": a.estimated_cost,
                    "status": a.status.value if a.status else "confirmed",
                }
                for a in d.activities
            ],
        }
        for d in days
    ]

    conflicts = detect_all_conflicts(itinerary_dicts)
    return {"conflicts": conflicts, "count": len(conflicts)}


@router.post("/{trip_id}/day/{day_number}/fit-check")
async def check_activity_fit(
    trip_id: str,
    day_number: int,
    activity: dict,
    db: AsyncSession = Depends(get_db),
):
    """Check if a new activity can fit into a specific day's schedule."""
    day = await get_day(db, trip_id, day_number)
    if not day:
        raise HTTPException(status_code=404, detail=f"Day {day_number} not found")

    day_dict = {
        "day_number": day.day_number,
        "activities": [
            {
                "name": a.name,
                "start_time": str(a.start_time) if a.start_time else None,
                "end_time": str(a.end_time) if a.end_time else None,
                "category": a.category,
                "latitude": a.latitude,
                "longitude": a.longitude,
            }
            for a in day.activities
        ],
    }

    result = can_fit_activity(day_dict, activity)
    return result


@router.get("/{trip_id}/export")
async def export_pdf(trip_id: str, db: AsyncSession = Depends(get_db)):
    """Export the trip itinerary as a PDF."""
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    days = await get_itinerary(db, trip_id)
    budget = await compute_budget_summary(db, trip_id)

    trip_dict = {
        "destination": trip.destination,
        "start_date": str(trip.start_date),
        "end_date": str(trip.end_date),
        "num_travelers": trip.num_travelers,
        "budget": trip.budget,
        "currency": trip.currency,
    }

    itinerary_dicts = [
        {
            "day_number": d.day_number,
            "date": str(d.date),
            "theme": d.theme,
            "weather_summary": d.weather_summary,
            "estimated_cost": d.estimated_cost,
            "notes": d.notes,
            "activities": [
                {
                    "name": a.name,
                    "category": a.category,
                    "location": a.location,
                    "start_time": str(a.start_time) if a.start_time else None,
                    "end_time": str(a.end_time) if a.end_time else None,
                    "estimated_cost": a.estimated_cost,
                    "tips": a.tips,
                    "status": a.status.value if a.status else "confirmed",
                }
                for a in d.activities
            ],
        }
        for d in days
    ]

    booking_dicts = [
        {
            "booking_type": b.booking_type.value,
            "provider": b.provider,
            "reference_number": b.reference_number,
            "status": b.status.value,
            "cost": b.cost,
            "currency": b.currency,
        }
        for b in trip.bookings
    ]

    pdf_bytes = generate_trip_pdf(trip_dict, itinerary_dicts, budget, booking_dicts)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=TravelPilot_{trip.destination}_{trip.start_date}.pdf"},
    )
