"""
TravelPilot — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from database.connection import init_db
from database.crud import create_trip, get_trip
from database.schemas import TripCreate, TripResponse
from database.connection import get_db
from routers import chat, itinerary, profile, dashboard
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    print("✅ TravelPilot API started — database initialized")
    yield
    print("🛑 TravelPilot API shutting down")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="TravelPilot API",
    description="Intelligent Trip Planning & Disruption Management Agent powered by Gemini + LangGraph",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(itinerary.router)
app.include_router(dashboard.router)


# ── Trip Management (direct) ──────────────────────────────────────────────────
@app.post("/trips", response_model=TripResponse, status_code=201, tags=["trips"])
async def create_new_trip(payload: TripCreate, db: AsyncSession = Depends(get_db)):
    """Create a new trip and get back the trip_id for all subsequent requests."""
    trip = await create_trip(db, payload)
    return trip


@app.get("/trips/{trip_id}", response_model=TripResponse, tags=["trips"])
async def get_trip_by_id(trip_id: str, db: AsyncSession = Depends(get_db)):
    """Get trip details by ID."""
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


# ── Health Check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "service": "TravelPilot API",
        "version": "1.0.0",
        "model": settings.gemini_model,
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "message": "Welcome to TravelPilot API 🌍✈️",
        "docs": "/docs",
        "health": "/health",
    }


# ── Global Exception Handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.app_debug,
        log_level="info",
    )
