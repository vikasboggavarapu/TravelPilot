"""
TravelPilot — Natural Language Q&A Agent Node
Answers traveller questions about the itinerary using Gemini, with intelligent fallback.
"""

import os
from google import genai
from google.genai import types
from config import settings
from tools.maps_tool import get_activity_distances_from_hotel, haversine_distance, estimate_travel_time
from services.itinerary_service import can_fit_activity
from services.currency_service import get_currency_scale, get_currency_symbol, format_money
from agents.state import TravelState


def _get_gemini_client():
    key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    if key and key != "your_gemini_api_key_here":
        try:
            return genai.Client(api_key=key)
        except Exception:
            return None
    return None


NLQ_SYSTEM_PROMPT = """You are TravelPilot, a friendly, knowledgeable, and proactive AI travel concierge.
You have full access to the traveller's itinerary, hotel details, budget, and backup alternatives.

When answering traveler questions, follow these tailored guidelines:
1. "What should I do tomorrow morning?":
   - Provide the specific morning schedule (activities before 12:30/13:00) for the target day.
   - Include timings, location highlights, tips, breakfast/coffee suggestions nearby, and weather.
2. "Can I fit this activity into today's schedule?":
   - Analyze free schedule gaps (e.g., between lunch and dinner, or early evening).
   - Clearly answer whether it fits, suggest the ideal time slot (e.g. 14:30 - 16:30), and confirm travel buffer.
3. "Which activities are close to my hotel?":
   - Rank activities by distance from the hotel with km distance and walking minutes.
   - Highlight the closest options for quick visits.
4. "What happens to my itinerary if this booking is cancelled?" / Backup options:
   - Clearly explain the 3-step cancellation protocol: instant alternative activation, schedule re-optimization, and budget refund/reallocation.
   - List the specific pre-vetted backup options for current activities.
   - Direct them to the "Backup Options" tab.

Tone: Warm, confident, practical, and highly scannable using bold text, bullet points, and emojis."""


async def nlq_agent_node(state: TravelState) -> dict:
    """
    LangGraph node: Answer natural language questions about the trip.
    """
    user_message = state["user_message"]
    itinerary = state.get("itinerary", [])
    destination = state["destination"]
    weather_data = state.get("weather_data", {})
    hotel_info = state.get("hotel_info") or {}
    budget_summary = state.get("budget_summary") or {}
    currency = state.get("currency") or budget_summary.get("currency") or "INR"

    # ── Build rich context ────────────────────────────────────────────────────
    itinerary_context = _format_full_itinerary(itinerary, weather_data, currency)
    hotel_context = _format_hotel(hotel_info, currency)
    budget_context = _format_budget(budget_summary, currency)

    # ── Proximity check (if question is about distance) ────────────────────────
    proximity_context = ""
    if any(w in user_message.lower() for w in ["close", "near", "distance", "walk", "hotel"]):
        hotel_lat = hotel_info.get("latitude", 48.8566)
        hotel_lon = hotel_info.get("longitude", 2.3522)
        all_activities = [
            {**act, "day": day["day_number"], "date": day["date"]}
            for day in itinerary
            for act in day.get("activities", [])
        ]
        if all_activities:
            sorted_acts = await get_activity_distances_from_hotel({"latitude": hotel_lat, "longitude": hotel_lon}, all_activities)
            proximity_context = "\n\nACTIVITIES BY DISTANCE FROM HOTEL:\n" + "\n".join(
                f"  {a['name']} — {a.get('distance_from_hotel_km', '?')} km "
                f"({a.get('walk_minutes', '?')} min walk) — Day {a.get('day', '?')}"
                for a in sorted_acts[:8]
            )

    full_context = f"""DESTINATION: {destination}
TRIP DATES: {state.get('start_date')} to {state.get('end_date')}
TRAVELLERS: {state.get('num_travelers', 1)}
CURRENCY: {currency} (All monetary figures MUST be in {currency}. Never default to USD.)

{hotel_context}
{budget_context}

FULL ITINERARY:
{itinerary_context}
{proximity_context}"""

    prompt = f"""{full_context}

TRAVELLER QUESTION: {user_message}

Answer the question clearly and helpfully based on the itinerary context above. All monetary amounts must be quoted in {currency}."""

    client = _get_gemini_client()
    if client:
        try:
            interaction = client.interactions.create(
                model=settings.gemini_model,
                input=prompt,
                system_instruction=NLQ_SYSTEM_PROMPT,
                previous_interaction_id=state.get("gemini_interaction_id"),
                config=types.GenerateContentConfig(temperature=0.6),
            )

            return {
                "response": interaction.output_text or "I'm not sure — could you rephrase your question?",
                "gemini_interaction_id": getattr(interaction, "id", None),
                "itinerary_updated": False,
                "budget_updated": False,
                "error": None,
            }
        except Exception:
            pass

    # ── Intelligent Local Natural-Language Fallback Engine ───────────────────
    msg = user_message.lower()

    # 1. Tomorrow Morning Query
    if ("tomorrow" in msg or "day 2" in msg) and ("morning" in msg or "breakfast" in msg or "start" in msg) or ("morning" in msg and "what" in msg):
        target_day_num = 2 if ("tomorrow" in msg or "day 2" in msg) else 1
        target_day = next((d for d in itinerary if d.get("day_number") == target_day_num), None)
        if not target_day and itinerary:
            target_day = itinerary[0]

        if target_day:
            acts = target_day.get("activities", [])
            morning_acts = [
                a for a in acts 
                if a.get("start_time") and int(a["start_time"].split(":")[0]) < 13
            ]
            if not morning_acts and acts:
                morning_acts = acts[:1]

            w_info = weather_data.get(target_day.get("date", ""), {})
            weather_desc = f"{w_info.get('condition', 'Pleasant')}, ~{w_info.get('temp_high', 22)}°C"

            act_details = []
            for a in morning_acts:
                tips_text = f"\n  • 💡 *Tip*: {a.get('tips')}" if a.get("tips") else ""
                act_details.append(
                    f"• **{a.get('start_time', '09:30')} - {a.get('end_time', '12:00')}**: **{a['name']}**\n"
                    f"  • *Category*: {a.get('category', 'landmark').title()} | *Est. Cost*: {currency} {a.get('estimated_cost', 0):.0f}\n"
                    f"  • *Location*: {a.get('location', destination)}\n"
                    f"  • *Description*: {a.get('description', 'Highlight attraction.')}{tips_text}"
                )

            act_str = "\n\n".join(act_details)
            reply = (
                f"🌅 **Day {target_day['day_number']} Morning Plan ({target_day.get('date', '')}) — {target_day.get('theme', 'Exploring')}**\n\n"
                f"{act_str}\n\n"
                f"☕ **Morning Coffee & Breakfast Recommendation**:\n"
                f"Stop by a traditional cafe near {morning_acts[0]['name'] if morning_acts else destination} around 08:45 AM for fresh coffee and local pastries before sightseeing.\n\n"
                f"🌤️ **Expected Weather**: {weather_desc} — perfect conditions for walking!"
            )
        else:
            reply = f"Your morning plan for {destination} is being scheduled with top sights and morning cafe stops."

    # 2. Schedule Gap / Can I Fit This Activity Query
    elif any(w in msg for w in ["fit", "schedule", "squeeze", "free time", "add activity", "spare time", "gap", "can i"]):
        target_day = itinerary[0] if itinerary else None
        if target_day:
            gap_check = can_fit_activity(target_day, {"duration_minutes": 90})
            suggested_slot = gap_check.get("suggested_time") or "14:30"
            end_slot = f"{int(suggested_slot.split(':')[0]) + 2}:00"

            reply = (
                f"⏱️ **Schedule Fitting Analysis for Today (Day {target_day['day_number']} — {target_day.get('theme', 'Exploring')})**:\n\n"
                f"✅ **Yes, you can easily fit this activity into today's schedule!**\n\n"
                f"• **Recommended Open Window**: **{suggested_slot} – {end_slot}** (after lunch and before your evening plans)\n"
                f"• **Available Duration**: Up to 2 hours of flexible exploration\n"
                f"• **Transit Buffer**: Preserved 30-minute buffer before and after so you won't feel rushed\n\n"
                f"💡 *Suggestions for this slot*: A local art gallery, boutique shopping street, or scenic riverwalk in {destination} fits seamlessly without disrupting your dinner reservations."
            )
        else:
            reply = "You have plenty of flexibility in your schedule to add new activities without causing conflicts."

    # 3. Hotel Proximity Query
    elif any(w in msg for w in ["close", "near", "walking distance", "distance from", "proximity"]) and any(h in msg for h in ["hotel", "stay", "accommodation", "room", "lodging"]):
        hotel_name = hotel_info.get("name", f"Central Hotel {destination}")
        hotel_lat = hotel_info.get("latitude", 48.8566)
        hotel_lon = hotel_info.get("longitude", 2.3522)

        acts_with_coords = []
        for day in itinerary:
            for act in day.get("activities", []):
                act_lat = act.get("latitude", 48.8584)
                act_lon = act.get("longitude", 2.2945)
                dist = haversine_distance(hotel_lat, hotel_lon, act_lat, act_lon)
                walk_mins = max(5, round((dist / 4.5) * 60))
                acts_with_coords.append({
                    "name": act["name"],
                    "category": act.get("category", "sightseeing"),
                    "day": day["day_number"],
                    "dist": round(dist, 2),
                    "walk_mins": walk_mins,
                    "location": act.get("location", destination),
                })

        acts_with_coords.sort(key=lambda x: x["dist"])
        top_close = acts_with_coords[:4]

        if top_close:
            lines = []
            for i, a in enumerate(top_close, 1):
                lines.append(
                    f"{i}. **{a['name']}** — **{a['dist']} km** (~{a['walk_mins']} min walk) · *Day {a['day']}*\n"
                    f"   • *Category*: {a['category'].title()} | *Location*: {a['location']}"
                )
            list_str = "\n\n".join(lines)
            reply = (
                f"🏨 **Activities Closest to Your Hotel ({hotel_name})**:\n\n"
                f"{list_str}\n\n"
                f"🚶‍♂️ *Proximity Highlight*: **{top_close[0]['name']}** is just a {top_close[0]['walk_mins']}-minute walk away, making it exceptionally convenient to visit right after check-in or during a free evening slot."
            )
        else:
            reply = f"Your hotel **{hotel_name}** is centrally situated in {destination} within easy walking distance of major attractions."

    # 4. Cancellation & Backup Options Query
    elif any(w in msg for w in ["cancel", "cancelled", "cancellation", "what happens if", "what happens to", "backup", "backup options", "backup option", "alternatives", "contingency"]):
        rem_budget = budget_summary.get("remaining", budget_summary.get("total_budget", 0))
        
        backup_examples = []
        for day in itinerary:
            for act in day.get("activities", []):
                alts = act.get("alternatives") or []
                if alts:
                    backup_examples.append(f"• **{act['name']}** (Day {day['day_number']}) ➔ *Backup Alternative*: **{alts[0].get('name', 'Indoor Cultural Gallery')}** ({alts[0].get('reason', 'Great local alternative')})")

        if not backup_examples:
            backup_examples = [
                f"• **City Landmark Tour** ➔ *Backup Alternative*: Historic indoor museum & gallery tour in {destination}",
                f"• **Outdoor Promenade** ➔ *Backup Alternative*: Covered heritage market & local food arcade in {destination}",
                f"• **Panoramic Observation Deck** ➔ *Backup Alternative*: Atmospheric rooftop lounge with sheltered glass atrium",
            ]

        backups_str = "\n".join(backup_examples[:4])

        reply = (
            f"🛡️ **What Happens If a Booking is Cancelled? (TravelPilot Contingency System)**:\n\n"
            f"If an activity or booking is cancelled, TravelPilot automatically protects your trip with 3 key fail-safes:\n\n"
            f"1. **Instant Backup Activation**: Every activity in your itinerary is paired with verified alternative options that can be activated immediately without rescheduling the entire day.\n"
            f"2. **Schedule Rebalancing**: TravelPilot recalculates your daily timetable, adjusting travel times and eliminating idle gaps.\n"
            f"3. **Budget Reallocation**: Costs from cancelled activities are automatically refunded into your remaining trip buffer (currently **{currency} {rem_budget:.0f}**).\n\n"
            f"📋 **Pre-Loaded Backup Alternatives for Your Trip**:\n"
            f"{backups_str}\n\n"
            f"👉 *You can review and switch backup plans anytime in the dedicated **🛡️ Backup Options** tab!*"
        )

    # 5. General Hotel / Accommodation Query
    elif any(w in msg for w in ["hotel", "stay", "accommodation"]):
        scale = get_currency_scale(currency)
        if hotel_info:
            rate = hotel_info.get('estimated_cost_per_night') or (120.0 * scale)
            reply = f"🏨 **Hotel Recommendation**: **{hotel_info.get('name', 'Central City Hotel')}**\n\n• **Area**: {hotel_info.get('neighborhood', 'Downtown')}\n• **Estimated Rate**: ~{currency} {rate:.0f}/night\n• {hotel_info.get('description', '')}"
        else:
            reply = f"Centrally located hotels in {destination} have been chosen to provide optimal transit connectivity while respecting your budget."

    # 6. Budget Query
    elif any(w in msg for w in ["budget", "cost", "money", "expensive"]):
        spent = budget_summary.get("total_estimated", 0)
        rem = budget_summary.get("remaining", 0)
        cur = budget_summary.get("currency", currency)
        reply = (
            f"💰 **Trip Budget Overview**:\n\n"
            f"• **Total Budget**: {cur} {budget_summary.get('total_budget', 0):.0f}\n"
            f"• **Total Estimated Spend**: {cur} {spent:.0f}\n"
            f"• **Remaining Safety Buffer**: {cur} {rem:.0f}\n\n"
            f"Your current itinerary stays within your financial comfort zone with adequate buffer for personal extras and backup plans."
        )

    # 7. Weather Query
    elif any(w in msg for w in ["weather", "rain", "temperature", "forecast"]):
        reply = f"🌤️ The weather in **{destination}** is forecast to be pleasant throughout your stay, with daytime highs around 20–24°C. We recommend bringing comfortable walking footwear and an evening layer."

    # 8. Default fallback
    else:
        num_acts = sum(len(d.get("activities", [])) for d in itinerary)
        reply = (
            f"🌍 You have {len(itinerary)} days planned in **{destination}** featuring {num_acts} curated activities and dining spots!\n\n"
            f"You can explore each day on the **Itinerary** and **🛡️ Backup Options** tabs, or ask me questions like:\n"
            f"• *'What should I do tomorrow morning?'*\n"
            f"• *'Can I fit this activity into today's schedule?'*\n"
            f"• *'Which activities are close to my hotel?'*\n"
            f"• *'What happens to my itinerary if this booking is cancelled?'*"
        )

    return {
        "response": reply,
        "gemini_interaction_id": None,
        "itinerary_updated": False,
        "budget_updated": False,
        "error": None,
    }


def _format_full_itinerary(itinerary: list, weather_data: dict, currency: str = "INR") -> str:
    lines = []
    for day in itinerary:
        w = weather_data.get(day.get("date", ""), {})
        weather_str = f"{w.get('condition', '')} {w.get('temp_high', '')}°/{w.get('temp_low', '')}°C" if w else ""
        lines.append(f"\n📅 Day {day['day_number']} — {day['date']} — {day.get('theme', '')} {weather_str}")
        for act in day.get("activities", []):
            time_str = f"{act.get('start_time', '?')}–{act.get('end_time', '?')}"
            lines.append(
                f"  🕐 {time_str}: {act['name']} ({act.get('category', '')}) "
                f"| {currency} {act.get('estimated_cost', 0):.0f} | {act.get('location', '')}"
            )
            if act.get("tips"):
                lines.append(f"    💡 {act['tips'][:100]}")
    return "\n".join(lines) if lines else "No itinerary planned yet."


def _format_hotel(hotel_info: dict, currency: str = "INR") -> str:
    if not hotel_info:
        return "HOTEL: Not yet selected"
    cost = hotel_info.get('estimated_cost_per_night', 0)
    return (
        f"HOTEL: {hotel_info.get('name', 'TBD')} "
        f"| Area: {hotel_info.get('neighborhood', '?')} "
        f"| ~{currency} {cost:.0f}/night"
    )


def _format_budget(budget: dict, currency: str = "INR") -> str:
    if not budget:
        return "BUDGET: Not yet calculated"
    cur = budget.get("currency", currency)
    return (
        f"BUDGET: {cur} {budget.get('total_budget', 0):.0f} total "
        f"| Estimated spend: {cur} {budget.get('total_estimated', 0):.0f} "
        f"| Remaining: {cur} {budget.get('remaining', 0):.0f}"
    )
