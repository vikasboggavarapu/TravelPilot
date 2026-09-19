"""
TravelPilot — Profile Router
User profile CRUD endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from database.crud import create_user, get_user, get_user_by_email, get_trips_by_user
from database.schemas import UserProfileCreate, UserProfileResponse, TripResponse

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("/", response_model=UserProfileResponse, status_code=201)
async def create_profile(payload: UserProfileCreate, db: AsyncSession = Depends(get_db)):
    """Create a new user profile."""
    if payload.email:
        existing = await get_user_by_email(db, payload.email)
        if existing:
            raise HTTPException(status_code=409, detail="Email already registered")
    user = await create_user(db, payload)
    return user


@router.get("/{user_id}", response_model=UserProfileResponse)
async def get_profile(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get a user profile by ID."""
    user = await get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/trips", response_model=list[TripResponse])
async def get_user_trips(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get all trips for a user."""
    trips = await get_trips_by_user(db, user_id)
    return trips
