"""
TravelPilot — Chat Router
WebSocket + HTTP endpoints for the AI chat interface.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from database.crud import (
    get_trip, log_message, get_conversation_history,
    get_last_gemini_interaction_id, save_itinerary_days, compute_budget_summary,
    update_trip_preferences
)
from database.models import MessageRole
from database.schemas import ChatMessage, ChatResponse, ConversationHistoryResponse
from agents.graph import run_graph
from agents.state import TravelState
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{trip_id}", response_model=ChatResponse)
async def send_message(
    trip_id: str,
    payload: ChatMessage,
    db: AsyncSession = Depends(get_db),
):
    """
    Send a message to the TravelPilot agent and get a response.
    Runs the full LangGraph pipeline.
    """
    trip = await get_trip(db, trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    # Log user message
    await log_message(db, trip_id, MessageRole.USER, payload.message)

    # Get previous Gemini interaction ID for conversation continuity
    prev_interaction_id = await get_last_gemini_interaction_id(db, trip_id)

    # Build itinerary days from DB
    itinerary_days = [
        {
            "day_number": d.day_number,
            "date": str(d.date),
            "theme": d.theme,
            "weather_summary": d.weather_summary,
            "weather_data": d.weather_data,
            "estimated_cost": d.estimated_cost,
            "notes": d.notes,
            "activities": [
                {
                    "name": a.name,
                    "category": a.category,
                    "location": a.location,
                    "address": a.address,
                    "latitude": a.latitude,
                    "longitude": a.longitude,
                    "start_time": str(a.start_time) if a.start_time else None,
                    "end_time": str(a.end_time) if a.end_time else None,
                    "duration_minutes": a.duration_minutes,
                    "estimated_cost": a.estimated_cost,
                    "booking_required": a.booking_required,
                    "booking_url": a.booking_url,
                    "description": a.description,
                    "tips": a.tips,
                    "alternatives": a.alternatives or [],
                    "status": a.status.value if a.status else "confirmed",
                    "travel_to_next": None,
                }
                for a in d.activities
            ],
        }
        for d in trip.itinerary_days
    ]

    prefs = trip.trip_preferences or {}
    start = trip.start_date
    end = trip.end_date
    num_days = (end - start).days + 1

    # Build LangGraph state
    state: TravelState = {
        "trip_id": trip_id,
        "user_id": trip.user_id,
        "user_message": payload.message,
        "destination": trip.destination,
        "origin_city": trip.origin_city,
        "start_date": str(start),
        "end_date": str(end),
        "num_days": num_days,
        "num_travelers": trip.num_travelers,
        "budget": trip.budget,
        "currency": trip.currency,
        "interests": prefs.get("interests", []),
        "dietary": prefs.get("dietary", []),
        "hotel_stars": prefs.get("hotel_stars", 3),
        "transport_mode": prefs.get("transport_mode", "public_transport"),
        "agent_intent": "",
        "itinerary": itinerary_days,
        "weather_data": {},
        "disruptions": [],
        "budget_summary": prefs.get("budget_summary") or {},
        "hotel_info": prefs.get("hotel_info"),
        "conversation_history": [],
        "gemini_interaction_id": prev_interaction_id,
        "response": "",
        "itinerary_updated": False,
        "budget_updated": False,
        "error": None,
    }

    try:
        # Run graph
        result = await run_graph(state)

        # Persist updated itinerary if changed
        if result.get("itinerary_updated") and result.get("itinerary"):
            await save_itinerary_days(db, trip_id, result["itinerary"])

        # Persist updated hotel info or budget summary into trip preferences
        updated_prefs = dict(prefs)
        has_pref_updates = False
        if result.get("hotel_info"):
            updated_prefs["hotel_info"] = result["hotel_info"]
            has_pref_updates = True
        if result.get("budget_summary"):
            updated_prefs["budget_summary"] = result["budget_summary"]
            has_pref_updates = True
        if has_pref_updates:
            await update_trip_preferences(db, trip_id, updated_prefs)

        # Log assistant response
        await log_message(
            db, trip_id, MessageRole.ASSISTANT,
            result.get("response", ""),
            gemini_interaction_id=result.get("gemini_interaction_id"),
            agent_node=result.get("agent_intent", ""),
        )

        disruption_descriptions = [
            d.get("description", "") for d in result.get("disruptions", [])
        ]

        return ChatResponse(
            trip_id=trip_id,
            response=result.get("response", ""),
            agent_node=result.get("agent_intent"),
            itinerary_updated=result.get("itinerary_updated", False),
            budget_updated=result.get("budget_updated", False),
            disruptions_detected=disruption_descriptions,
        )
    except Exception as e:
        err_msg = f"I ran into an issue while planning your trip: {str(e)}. Please try asking again or adjusting your request."
        await log_message(
            db, trip_id, MessageRole.ASSISTANT,
            err_msg,
            agent_node="error",
        )
        return ChatResponse(
            trip_id=trip_id,
            response=err_msg,
            agent_node="error",
            itinerary_updated=False,
            budget_updated=False,
            disruptions_detected=[],
        )


@router.get("/{trip_id}/history", response_model=list[ConversationHistoryResponse])
async def get_history(
    trip_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Get conversation history for a trip."""
    history = await get_conversation_history(db, trip_id, limit=limit)
    return history


@router.websocket("/ws/{trip_id}")
async def websocket_chat(websocket: WebSocket, trip_id: str, db: AsyncSession = Depends(get_db)):
    """
    WebSocket endpoint for real-time streaming chat.
    """
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            user_message = data.get("message", "")

            if not user_message:
                continue

            # Reuse the HTTP handler logic
            payload = ChatMessage(trip_id=trip_id, message=user_message)

            try:
                response = await send_message(trip_id, payload, db)
                await websocket.send_json({
                    "type": "response",
                    "data": response.model_dump(),
                })
            except Exception as e:
                await websocket.send_json({
                    "type": "error",
                    "message": str(e),
                })

    except WebSocketDisconnect:
        pass
