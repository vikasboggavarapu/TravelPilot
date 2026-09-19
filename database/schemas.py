"""
TravelPilot — Pydantic Schemas
Request/Response models for API validation.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any
from datetime import datetime, date, time
from database.models import TripStatus, ActivityStatus, BookingType, BookingStatus, MessageRole
import uuid


# ─────────────────────────────────────────────────────────
#  User Profile
# ─────────────────────────────────────────────────────────

class UserPreferences(BaseModel):
    interests: list[str] = []          # e.g. ["culture", "food", "adventure"]
    dietary: list[str] = []            # e.g. ["vegetarian", "halal"]
    hotel_stars: int = 3
    transport_mode: str = "public"     # public | taxi | rental_car | walking
    language: str = "en"


class UserProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    home_city: Optional[str] = None
    currency: str = "INR"
    preferences: Optional[UserPreferences] = None


class UserProfileResponse(BaseModel):
    user_id: str
    name: str
    email: Optional[str]
    home_city: Optional[str]
    currency: str
    preferences: Optional[dict]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────
#  Trip
# ─────────────────────────────────────────────────────────

class TripCreate(BaseModel):
    user_id: str
    destination: str = Field(..., min_length=2)
    origin_city: Optional[str] = None
    start_date: date
    end_date: date
    num_travelers: int = Field(default=1, ge=1, le=20)
    budget: float = Field(..., gt=0)
    currency: str = "INR"
    trip_preferences: Optional[dict] = None
    notes: Optional[str] = None


class TripResponse(BaseModel):
    trip_id: str
    user_id: str
    destination: str
    origin_city: Optional[str]
    start_date: date
    end_date: date
    num_travelers: int
    budget: float
    currency: str
    status: TripStatus
    trip_preferences: Optional[dict]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────
#  Activity
# ─────────────────────────────────────────────────────────

class ActivityCreate(BaseModel):
    name: str
    category: str
    location: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    duration_minutes: Optional[int] = None
    estimated_cost: float = 0.0
    booking_required: bool = False
    booking_url: Optional[str] = None
    description: Optional[str] = None
    tips: Optional[str] = None
    alternatives: Optional[list[dict]] = []
    sort_order: int = 0


class ActivityResponse(ActivityCreate):
    activity_id: str
    day_id: str
    status: ActivityStatus

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────
#  Itinerary Day
# ─────────────────────────────────────────────────────────

class ItineraryDayResponse(BaseModel):
    day_id: str
    trip_id: str
    day_number: int
    date: date
    theme: Optional[str]
    weather_summary: Optional[str]
    weather_data: Optional[dict]
    estimated_cost: float
    notes: Optional[str]
    activities: list[ActivityResponse] = []

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────
#  Booking
# ─────────────────────────────────────────────────────────

class BookingCreate(BaseModel):
    trip_id: str
    booking_type: BookingType
    provider: Optional[str] = None
    reference_number: Optional[str] = None
    status: BookingStatus = BookingStatus.CONFIRMED
    check_in: Optional[datetime] = None
    check_out: Optional[datetime] = None
    cost: float = 0.0
    currency: str = "INR"
    details: Optional[dict] = {}


class BookingResponse(BookingCreate):
    booking_id: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────
#  Conversation / Chat
# ─────────────────────────────────────────────────────────

class ChatMessage(BaseModel):
    trip_id: str
    message: str = Field(..., min_length=1)
    user_id: Optional[str] = None


class ChatResponse(BaseModel):
    trip_id: str
    response: str
    agent_node: Optional[str] = None
    itinerary_updated: bool = False
    budget_updated: bool = False
    disruptions_detected: list[str] = []


class ConversationHistoryResponse(BaseModel):
    message_id: str
    role: MessageRole
    content: str
    agent_node: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────

class BudgetSummarySchema(BaseModel):
    total_budget: float
    spent_accommodation: float = 0.0
    spent_transport: float = 0.0
    spent_food: float = 0.0
    spent_activities: float = 0.0
    spent_other: float = 0.0
    total_estimated: float = 0.0
    remaining: float = 0.0
    currency: str = "INR"


class DashboardResponse(BaseModel):
    trip: TripResponse
    itinerary: list[ItineraryDayResponse]
    bookings: list[BookingResponse]
    budget_summary: BudgetSummarySchema
    weather_overview: Optional[dict] = None
    backup_options: list[dict] = []
