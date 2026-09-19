"""
TravelPilot — SQLAlchemy ORM Models
All tables for the database (supports PostgreSQL and SQLite).
"""

import uuid
from datetime import datetime, date, time
from typing import Optional
from sqlalchemy import (
    String, Text, Integer, Float, Boolean, DateTime, Date, Time,
    ForeignKey, Enum as SAEnum, JSON, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connection import Base
import enum


# ── Enums ─────────────────────────────────────────────────────────────────────

class TripStatus(str, enum.Enum):
    PLANNING = "planning"
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ActivityStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    AT_RISK = "at_risk"
    CANCELLED = "cancelled"
    ALTERNATIVE = "alternative"


class BookingType(str, enum.Enum):
    FLIGHT = "flight"
    HOTEL = "hotel"
    ACTIVITY = "activity"
    TRANSPORT = "transport"


class BookingStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


# ── Models ────────────────────────────────────────────────────────────────────

class UserProfile(Base):
    """Stores traveller profiles and preferences."""
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True)
    home_city: Mapped[Optional[str]] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    # JSON: { interests, dietary, hotel_stars, transport_mode, language }
    preferences: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    trips: Mapped[list["Trip"]] = relationship("Trip", back_populates="user", cascade="all, delete-orphan")


class Trip(Base):
    """Core trip entity — anchors everything else."""
    __tablename__ = "trips"

    trip_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("user_profiles.user_id"), nullable=False)
    destination: Mapped[str] = mapped_column(String(200), nullable=False)
    origin_city: Mapped[Optional[str]] = mapped_column(String(200))
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    num_travelers: Mapped[int] = mapped_column(Integer, default=1)
    budget: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    status: Mapped[TripStatus] = mapped_column(SAEnum(TripStatus), default=TripStatus.PLANNING)
    # JSON: { interests: [], dietary: [], hotel_stars: int, transport_mode: str }
    trip_preferences: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="trips")
    itinerary_days: Mapped[list["ItineraryDay"]] = relationship("ItineraryDay", back_populates="trip", cascade="all, delete-orphan", order_by="ItineraryDay.day_number")
    bookings: Mapped[list["Booking"]] = relationship("Booking", back_populates="trip", cascade="all, delete-orphan")
    conversation_history: Mapped[list["ConversationHistory"]] = relationship("ConversationHistory", back_populates="trip", cascade="all, delete-orphan")


class ItineraryDay(Base):
    """One day in the trip itinerary."""
    __tablename__ = "itinerary_days"

    day_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(String(36), ForeignKey("trips.trip_id"), nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-indexed
    date: Mapped[date] = mapped_column(Date, nullable=False)
    theme: Mapped[Optional[str]] = mapped_column(String(200))       # e.g. "Museum Day"
    weather_summary: Mapped[Optional[str]] = mapped_column(String(500))
    # JSON: { temp_high, temp_low, condition, icon, precipitation_pct }
    weather_data: Mapped[Optional[dict]] = mapped_column(JSON)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="itinerary_days")
    activities: Mapped[list["Activity"]] = relationship("Activity", back_populates="day", cascade="all, delete-orphan", order_by="Activity.start_time")


class Activity(Base):
    """A single activity / event within a day."""
    __tablename__ = "activities"

    activity_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    day_id: Mapped[str] = mapped_column(String(36), ForeignKey("itinerary_days.day_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    category: Mapped[str] = mapped_column(String(100))   # food, culture, adventure, transport, etc.
    location: Mapped[Optional[str]] = mapped_column(String(500))
    address: Mapped[Optional[str]] = mapped_column(Text)
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    start_time: Mapped[Optional[time]] = mapped_column(Time)
    end_time: Mapped[Optional[time]] = mapped_column(Time)
    duration_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0.0)
    booking_required: Mapped[bool] = mapped_column(Boolean, default=False)
    booking_url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[ActivityStatus] = mapped_column(SAEnum(ActivityStatus), default=ActivityStatus.CONFIRMED)
    description: Mapped[Optional[str]] = mapped_column(Text)
    tips: Mapped[Optional[str]] = mapped_column(Text)
    # JSON: list of alternative activity dicts if this one is cancelled
    alternatives: Mapped[Optional[list]] = mapped_column(JSON, default=list)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    day: Mapped["ItineraryDay"] = relationship("ItineraryDay", back_populates="activities")


class Booking(Base):
    """Tracks all bookings (flights, hotels, activities)."""
    __tablename__ = "bookings"

    booking_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(String(36), ForeignKey("trips.trip_id"), nullable=False)
    booking_type: Mapped[BookingType] = mapped_column(SAEnum(BookingType), nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(200))
    reference_number: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[BookingStatus] = mapped_column(SAEnum(BookingStatus), default=BookingStatus.CONFIRMED)
    check_in: Mapped[Optional[datetime]] = mapped_column(DateTime)
    check_out: Mapped[Optional[datetime]] = mapped_column(DateTime)
    cost: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="INR")
    # JSON: full booking details (flight number, seat, hotel name, room type, etc.)
    details: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="bookings")


class ConversationHistory(Base):
    """Persists full chat history per trip for multi-turn Gemini interactions."""
    __tablename__ = "conversation_history"

    message_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    trip_id: Mapped[str] = mapped_column(String(36), ForeignKey("trips.trip_id"), nullable=False)
    role: Mapped[MessageRole] = mapped_column(SAEnum(MessageRole), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Gemini interaction ID for chaining previous_interaction_id
    gemini_interaction_id: Mapped[Optional[str]] = mapped_column(String(500))
    # LangGraph node that produced this message
    agent_node: Mapped[Optional[str]] = mapped_column(String(100))
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # Relationships
    trip: Mapped["Trip"] = relationship("Trip", back_populates="conversation_history")
