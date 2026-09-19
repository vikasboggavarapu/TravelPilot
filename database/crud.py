"""
TravelPilot — Database CRUD Operations
All async database read/write operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import selectinload
from datetime import datetime, date, time
from typing import Optional

from database.models import (
    UserProfile, Trip, ItineraryDay, Activity,
    Booking, ConversationHistory, TripStatus, MessageRole
)
from database.schemas import (
    UserProfileCreate, TripCreate, ActivityCreate, BookingCreate
)
from services.currency_service import get_currency_scale


# ─────────────────────────────────────────────────────────
#  User Profile CRUD
# ─────────────────────────────────────────────────────────

async def create_user(db: AsyncSession, data: UserProfileCreate) -> UserProfile:
    user = UserProfile(
        name=data.name,
        email=data.email,
        home_city=data.home_city,
        currency=data.currency,
        preferences=data.preferences.model_dump() if data.preferences else {},
    )
    db.add(user)
    await db.flush()
    return user


async def get_user(db: AsyncSession, user_id: str) -> Optional[UserProfile]:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[UserProfile]:
    result = await db.execute(select(UserProfile).where(UserProfile.email == email))
    return result.scalar_one_or_none()


# ─────────────────────────────────────────────────────────
#  Trip CRUD
# ─────────────────────────────────────────────────────────

async def create_trip(db: AsyncSession, data: TripCreate) -> Trip:
    trip = Trip(
        user_id=data.user_id,
        destination=data.destination,
        origin_city=data.origin_city,
        start_date=data.start_date,
        end_date=data.end_date,
        num_travelers=data.num_travelers,
        budget=data.budget,
        currency=data.currency,
        trip_preferences=data.trip_preferences or {},
        notes=data.notes,
    )
    db.add(trip)
    await db.flush()
    return trip


async def get_trip(db: AsyncSession, trip_id: str) -> Optional[Trip]:
    result = await db.execute(
        select(Trip)
        .where(Trip.trip_id == trip_id)
        .options(
            selectinload(Trip.itinerary_days).selectinload(ItineraryDay.activities),
            selectinload(Trip.bookings),
        )
    )
    return result.scalar_one_or_none()


async def get_trips_by_user(db: AsyncSession, user_id: str) -> list[Trip]:
    result = await db.execute(
        select(Trip).where(Trip.user_id == user_id).order_by(Trip.start_date.desc())
    )
    return list(result.scalars().all())


async def update_trip_status(db: AsyncSession, trip_id: str, status: TripStatus) -> None:
    await db.execute(
        update(Trip).where(Trip.trip_id == trip_id).values(status=status, updated_at=datetime.utcnow())
    )


async def update_trip_preferences(db: AsyncSession, trip_id: str, preferences: dict) -> None:
    await db.execute(
        update(Trip).where(Trip.trip_id == trip_id).values(trip_preferences=preferences, updated_at=datetime.utcnow())
    )


# ─────────────────────────────────────────────────────────
#  Itinerary CRUD
# ─────────────────────────────────────────────────────────

async def save_itinerary_days(db: AsyncSession, trip_id: str, days: list[dict]) -> list[ItineraryDay]:
    """
    Replace the full itinerary for a trip.
    days: list of dicts from the LangGraph agent output.
    """
    # Delete existing days (cascade deletes activities)
    await db.execute(delete(ItineraryDay).where(ItineraryDay.trip_id == trip_id))

    saved_days = []
    for day_data in days:
        day_date = day_data.get("date")
        if isinstance(day_date, str):
            try:
                day_date = datetime.strptime(day_date, "%Y-%m-%d").date()
            except Exception:
                day_date = datetime.utcnow().date()

        activities_data = day_data.get("activities", [])
        act_cost_sum = sum(float(a.get("estimated_cost", 0) or 0) for a in activities_data)
        given_cost = float(day_data.get("estimated_cost") or 0.0)
        day_cost = given_cost if given_cost > 0 else act_cost_sum

        day = ItineraryDay(
            trip_id=trip_id,
            day_number=day_data["day_number"],
            date=day_date,
            theme=day_data.get("theme"),
            weather_summary=day_data.get("weather_summary"),
            weather_data=day_data.get("weather_data"),
            estimated_cost=round(day_cost, 2),
            notes=day_data.get("notes"),
        )
        db.add(day)
        await db.flush()  # get day_id

        for i, act_data in enumerate(activities_data):
            st = act_data.get("start_time")
            et = act_data.get("end_time")

            if isinstance(st, str) and st:
                try:
                    parts = [int(p) for p in st.split(":")[:2]]
                    st = time(parts[0], parts[1])
                except Exception:
                    st = None
            elif not isinstance(st, time):
                st = None

            if isinstance(et, str) and et:
                try:
                    parts = [int(p) for p in et.split(":")[:2]]
                    et = time(parts[0], parts[1])
                except Exception:
                    et = None
            elif not isinstance(et, time):
                et = None

            activity = Activity(
                day_id=day.day_id,
                name=act_data["name"],
                category=act_data.get("category", "general"),
                location=act_data.get("location"),
                address=act_data.get("address"),
                latitude=act_data.get("latitude"),
                longitude=act_data.get("longitude"),
                start_time=st,
                end_time=et,
                duration_minutes=act_data.get("duration_minutes"),
                estimated_cost=act_data.get("estimated_cost", 0.0),
                booking_required=act_data.get("booking_required", False),
                booking_url=act_data.get("booking_url"),
                description=act_data.get("description"),
                tips=act_data.get("tips"),
                alternatives=act_data.get("alternatives", []),
                sort_order=i,
            )
            db.add(activity)

        saved_days.append(day)

    return saved_days


async def get_itinerary(db: AsyncSession, trip_id: str) -> list[ItineraryDay]:
    result = await db.execute(
        select(ItineraryDay)
        .where(ItineraryDay.trip_id == trip_id)
        .options(selectinload(ItineraryDay.activities))
        .order_by(ItineraryDay.day_number)
    )
    return list(result.scalars().all())


async def get_day(db: AsyncSession, trip_id: str, day_number: int) -> Optional[ItineraryDay]:
    result = await db.execute(
        select(ItineraryDay)
        .where(ItineraryDay.trip_id == trip_id, ItineraryDay.day_number == day_number)
        .options(selectinload(ItineraryDay.activities))
    )
    return result.scalar_one_or_none()


async def update_activity_status(db: AsyncSession, activity_id: str, status: str) -> None:
    await db.execute(
        update(Activity).where(Activity.activity_id == activity_id).values(status=status)
    )


# ─────────────────────────────────────────────────────────
#  Booking CRUD
# ─────────────────────────────────────────────────────────

async def upsert_booking(db: AsyncSession, data: BookingCreate) -> Booking:
    booking = Booking(
        trip_id=data.trip_id,
        booking_type=data.booking_type,
        provider=data.provider,
        reference_number=data.reference_number,
        status=data.status,
        check_in=data.check_in,
        check_out=data.check_out,
        cost=data.cost,
        currency=data.currency,
        details=data.details or {},
    )
    db.add(booking)
    await db.flush()
    return booking


async def get_bookings(db: AsyncSession, trip_id: str) -> list[Booking]:
    result = await db.execute(
        select(Booking).where(Booking.trip_id == trip_id).order_by(Booking.created_at)
    )
    return list(result.scalars().all())


# ─────────────────────────────────────────────────────────
#  Conversation History CRUD
# ─────────────────────────────────────────────────────────

async def log_message(
    db: AsyncSession,
    trip_id: str,
    role: MessageRole,
    content: str,
    gemini_interaction_id: Optional[str] = None,
    agent_node: Optional[str] = None,
) -> ConversationHistory:
    msg = ConversationHistory(
        trip_id=trip_id,
        role=role,
        content=content,
        gemini_interaction_id=gemini_interaction_id,
        agent_node=agent_node,
    )
    db.add(msg)
    await db.flush()
    return msg


async def get_conversation_history(
    db: AsyncSession, trip_id: str, limit: int = 50
) -> list[ConversationHistory]:
    result = await db.execute(
        select(ConversationHistory)
        .where(ConversationHistory.trip_id == trip_id)
        .order_by(ConversationHistory.timestamp.desc())
        .limit(limit)
    )
    return list(reversed(result.scalars().all()))


async def get_last_gemini_interaction_id(db: AsyncSession, trip_id: str) -> Optional[str]:
    """Returns the most recent Gemini interaction ID for conversation chaining."""
    result = await db.execute(
        select(ConversationHistory.gemini_interaction_id)
        .where(
            ConversationHistory.trip_id == trip_id,
            ConversationHistory.gemini_interaction_id.isnot(None),
        )
        .order_by(ConversationHistory.timestamp.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


# ─────────────────────────────────────────────────────────
#  Budget Aggregation
# ─────────────────────────────────────────────────────────

FOOD_CATEGORIES = {
    "food", "restaurant", "dining", "dinner", "lunch", "breakfast",
    "cafe", "bar", "bistro", "drinks", "brunch", "snack", "bakery"
}

TRANSPORT_CATEGORIES = {
    "transport", "transit", "taxi", "cab", "bus", "metro", "subway",
    "train", "flight", "ferry", "shuttle", "car_rental", "transfer"
}


async def compute_budget_summary(db: AsyncSession, trip_id: str) -> dict:
    """Aggregate all costs across activities, bookings, hotel, and transport."""
    trip_result = await db.execute(select(Trip).where(Trip.trip_id == trip_id))
    trip = trip_result.scalar_one_or_none()
    if not trip:
        return {}

    # Activity costs per category
    activity_result = await db.execute(
        select(Activity.category, func.sum(Activity.estimated_cost))
        .join(ItineraryDay, Activity.day_id == ItineraryDay.day_id)
        .where(ItineraryDay.trip_id == trip_id)
        .group_by(Activity.category)
    )
    raw_cat_costs = {str(row[0] or "").lower(): float(row[1] or 0.0) for row in activity_result.all()}

    # Booking costs
    booking_result = await db.execute(
        select(Booking.booking_type, func.sum(Booking.cost))
        .where(Booking.trip_id == trip_id)
        .group_by(Booking.booking_type)
    )
    booking_costs = {str(row[0] or "").lower(): float(row[1] or 0.0) for row in booking_result.all()}

    prefs = trip.trip_preferences or {}
    saved_budget = prefs.get("budget_summary") or {}
    hotel_info = prefs.get("hotel_info") or {}

    num_days = max((trip.end_date - trip.start_date).days + 1, 1)
    num_nights = max(num_days - 1, 1)
    travelers = max(trip.num_travelers or 1, 1)

    food_cost = sum(raw_cat_costs.get(c, 0.0) for c in FOOD_CATEGORIES)
    activity_transport = sum(raw_cat_costs.get(c, 0.0) for c in TRANSPORT_CATEGORIES)
    activity_cost = sum(
        v for k, v in raw_cat_costs.items()
        if k not in FOOD_CATEGORIES and k not in TRANSPORT_CATEGORIES
    )

    # Accommodation
    if booking_costs.get("hotel", 0.0) > 0:
        accommodation_cost = booking_costs["hotel"]
    elif hotel_info.get("estimated_cost_per_night"):
        accommodation_cost = round(float(hotel_info["estimated_cost_per_night"]) * num_nights, 2)
    elif saved_budget.get("spent_accommodation", 0.0) > 0:
        accommodation_cost = float(saved_budget["spent_accommodation"])
    else:
        scale = get_currency_scale(trip.currency)
        default_nightly = min(max((trip.budget * 0.35) / num_nights, 40.0 * scale), 350.0 * scale)
        accommodation_cost = round(default_nightly * num_nights, 2)

    # Transport
    booking_transport = booking_costs.get("flight", 0.0) + booking_costs.get("transport", 0.0)
    if (activity_transport + booking_transport) > 0:
        transport_cost = round(activity_transport + booking_transport, 2)
    elif saved_budget.get("spent_transport", 0.0) > 0:
        transport_cost = float(saved_budget["spent_transport"])
    else:
        scale = get_currency_scale(trip.currency)
        transport_cost = round(15.0 * scale * num_days * travelers, 2)

    total_estimated = round(food_cost + activity_cost + transport_cost + accommodation_cost, 2)
    remaining = round(trip.budget - total_estimated, 2)

    return {
        "total_budget": trip.budget,
        "currency": trip.currency,
        "spent_accommodation": accommodation_cost,
        "spent_transport": transport_cost,
        "spent_food": round(food_cost, 2),
        "spent_activities": round(activity_cost, 2),
        "spent_other": 0.0,
        "total_estimated": total_estimated,
        "remaining": remaining,
    }
