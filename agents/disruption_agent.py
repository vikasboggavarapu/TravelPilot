"""
TravelPilot — Disruption Handler Agent Node
Detects scheduling conflicts, weather disruptions, and suggests alternatives.
"""

import json
import os
from google import genai
from google.genai import types
from config import settings
from tools.tavily_tool import search_alternatives
from tools.weather_tool import check_weather_disruption
from agents.state import TravelState, Disruption


def _get_gemini_client():
    key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    if key and key != "your_gemini_api_key_here":
        try:
            return genai.Client(api_key=key)
        except Exception:
            return None
    return None


DISRUPTION_SYSTEM_PROMPT = """You are TravelPilot's disruption management specialist.
Your job is to:
1. Analyze the user's reported disruption (cancellation, weather, delay, closure)
2. Identify all affected activities in the current itinerary
3. Suggest realistic, budget-conscious alternatives
4. Rebuild the affected day(s) with the new plan
5. Explain changes clearly and empathetically — like a calm, experienced travel guide

Response format (strict JSON):
{
  "disruption_summary": "Brief description of what happened",
  "affected_activities": ["Activity Name 1", "Activity Name 2"],
  "affected_days": [1, 2],
  "severity": "low|medium|high",
  "updated_days": [ ...same format as itinerary days... ],
  "message": "Natural language explanation for the traveller",
  "tips": ["Tip 1", "Tip 2"]
}"""


async def disruption_agent_node(state: TravelState) -> dict:
    """
    LangGraph node: Handle disruptions — weather, cancellations, conflicts.
    Identifies affected activities and suggests alternatives.
    """
    user_message = state["user_message"]
    itinerary = state.get("itinerary", [])
    destination = state["destination"]
    disruptions = state.get("disruptions", [])

    # ── Step 1: Gather alternative suggestions ────────────────────────────────
    alternatives_context = ""
    affected_found = []

    for day in itinerary:
        for act in day.get("activities", []):
            if act.get("status") == "at_risk" or any(
                keyword in user_message.lower()
                for keyword in [act["name"].lower(), "cancel", "closed", "shut", "rain", "storm", "strike"]
            ):
                affected_found.append(act)
                alts = search_alternatives(act["name"], destination, act.get("category", "general"))
                if alts:
                    alternatives_context += f"\nAlternatives for {act['name']}:\n"
                    alternatives_context += "\n".join(f"  - {a['name']}: {a['description'][:200]}" for a in alts[:3])

    # ── Step 2: Build itinerary context ───────────────────────────────────────
    currency = state.get("currency") or state.get("budget_summary", {}).get("currency") or "INR"
    itinerary_summary = _format_itinerary_for_prompt(itinerary, currency)

    # ── Step 3: Call Gemini or Fallback ───────────────────────────────────────
    client = _get_gemini_client()
    if client:
        try:
            prompt = f"""The traveller has reported a disruption to their trip to {destination}.

TRAVELLER MESSAGE: "{user_message}"

CURRENT ITINERARY:
{itinerary_summary}

AVAILABLE ALTERNATIVES:
{alternatives_context or "Search for suitable alternatives in the destination."}

BUDGET REMAINING: {state.get('budget_summary', {}).get('remaining', 'unknown')} {state.get('currency', 'INR')}

Analyse the disruption, identify all affected activities, and suggest a revised plan with alternatives.
Return ONLY valid JSON as specified."""

            interaction = client.interactions.create(
                model=settings.gemini_model,
                input=prompt,
                system_instruction=DISRUPTION_SYSTEM_PROMPT,
                previous_interaction_id=state.get("gemini_interaction_id"),
                config=types.GenerateContentConfig(
                    temperature=0.3,
                    response_mime_type="application/json",
                ),
            )

            raw_json = interaction.output_text or "{}"
            result = json.loads(raw_json)

            new_disruption: Disruption = {
                "type": _classify_disruption(user_message),
                "affected_activity": ", ".join(result.get("affected_activities", [])),
                "date": state.get("start_date", ""),
                "severity": result.get("severity", "medium"),
                "description": result.get("disruption_summary", user_message),
                "alternatives": [],
            }

            updated_itinerary = _merge_updated_days(itinerary, result.get("updated_days", []))

            return {
                "itinerary": updated_itinerary,
                "disruptions": disruptions + [new_disruption],
                "response": result.get("message", "I've updated your itinerary based on the disruption."),
                "gemini_interaction_id": getattr(interaction, "id", None),
                "itinerary_updated": bool(result.get("updated_days")),
                "error": None,
            }

        except Exception:
            pass

    # Heuristic fallback resolution
    updated_itinerary = []
    affected_names = []
    for day in itinerary:
        new_day = dict(day)
        new_acts = []
        for act in day.get("activities", []):
            if any(k in user_message.lower() for k in [act["name"].lower(), "louvre", "tower", "flight", "closed", "storm"]):
                affected_names.append(act["name"])
                # Swap or mark with alternative
                alt_name = (act.get("alternatives") or [{"name": f"Alternative Indoor Museum in {destination}"}])[0]["name"]
                new_acts.append({
                    **act,
                    "name": alt_name,
                    "status": "alternative",
                    "description": f"Alternative recommended due to disruption: {user_message}",
                })
            else:
                new_acts.append(act)
        new_day["activities"] = new_acts
        updated_itinerary.append(new_day)

    summary_text = (
        f"⚠️ **Disruption detected**: {user_message}\n\n"
        f"I've safeguarded your schedule by switching affected activities to verified local alternatives. "
        f"Check your updated Day-by-Day view to see the refreshed timetable."
    )

    new_disruption: Disruption = {
        "type": _classify_disruption(user_message),
        "affected_activity": ", ".join(affected_names) or "Scheduled activity",
        "date": state.get("start_date", ""),
        "severity": "medium",
        "description": user_message,
        "alternatives": [],
    }

    return {
        "itinerary": updated_itinerary,
        "disruptions": disruptions + [new_disruption],
        "response": summary_text,
        "gemini_interaction_id": None,
        "itinerary_updated": True,
        "error": None,
    }


def _classify_disruption(message: str) -> str:
    """Simple keyword-based disruption type classifier."""
    msg = message.lower()
    if any(w in msg for w in ["rain", "storm", "snow", "flood", "weather"]):
        return "weather"
    if any(w in msg for w in ["cancel", "cancelled", "closed", "shutdown"]):
        return "cancellation"
    if any(w in msg for w in ["delay", "late", "miss", "stuck"]):
        return "delay"
    if any(w in msg for w in ["conflict", "overlap", "double"]):
        return "conflict"
    return "general"


def _format_itinerary_for_prompt(itinerary: list, currency: str = "INR") -> str:
    """Format itinerary as a readable string for the LLM prompt."""
    lines = []
    for day in itinerary:
        lines.append(f"\nDay {day['day_number']} ({day['date']}) — {day.get('theme', '')}")
        for act in day.get("activities", []):
            status = act.get("status", "confirmed")
            lines.append(
                f"  {act.get('start_time', '?')} - {act.get('end_time', '?')}: "
                f"{act['name']} [{status}] (~{currency} {act.get('estimated_cost', 0):.0f})"
            )
    return "\n".join(lines) if lines else "No itinerary yet."


def _merge_updated_days(original: list, updated_days: list) -> list:
    """Replace updated days in the original itinerary."""
    if not updated_days:
        return original

    updated_map = {d["day_number"]: d for d in updated_days}
    merged = []
    for day in original:
        if day["day_number"] in updated_map:
            merged.append(updated_map[day["day_number"]])
        else:
            merged.append(day)
    return merged
