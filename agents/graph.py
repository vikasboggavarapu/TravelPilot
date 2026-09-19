"""
TravelPilot — LangGraph State Machine (Main Graph)
Orchestrates all agent nodes with conditional routing.
"""

import os
from langgraph.graph import StateGraph, START, END
from google import genai
from google.genai import types
from config import settings
from agents.state import TravelState
from agents.planner_agent import plan_trip_node
from agents.disruption_agent import disruption_agent_node
from agents.nlq_agent import nlq_agent_node
from agents.budget_agent import budget_agent_node


def _get_gemini_client():
    key = settings.gemini_api_key or os.getenv("GEMINI_API_KEY", "")
    if key and key != "your_gemini_api_key_here":
        try:
            return genai.Client(api_key=key)
        except Exception:
            return None
    return None


INTENT_SYSTEM_PROMPT = """You are a travel assistant intent classifier.
Classify the user's message into exactly ONE of these intents:
- "plan"     — User wants to create or build a new itinerary
- "modify"   — User wants to change, update, or adjust the itinerary/budget/dates
- "query"    — User is asking a question about the trip, schedule, activities, or logistics
- "disrupt"  — User is reporting a disruption (cancellation, weather problem, delay, conflict, closure)

Reply with ONLY the intent word. Nothing else."""


# ── Intent Classifier ─────────────────────────────────────────────────────────

async def classify_intent_node(state: TravelState) -> dict:
    """Route the user message to the correct agent."""
    user_message = state["user_message"]
    itinerary = state.get("itinerary", [])

    # If no itinerary yet, always plan
    if not itinerary:
        return {"agent_intent": "plan"}

    client = _get_gemini_client()
    if client:
        try:
            interaction = client.interactions.create(
                model=settings.gemini_model,
                input=f"User message: \"{user_message}\"",
                system_instruction=INTENT_SYSTEM_PROMPT,
                config=types.GenerateContentConfig(temperature=0.1, max_output_tokens=10),
            )
            intent = (interaction.output_text or "").strip().lower()
            for possible in ["disrupt", "modify", "plan", "query"]:
                if possible in intent:
                    return {"agent_intent": possible}
        except Exception:
            pass

    # Heuristic fallback
    msg = user_message.lower()
    if any(q in msg for q in ["what happens if", "what happens to", "what if", "backup options", "backup option", "can i fit", "what should i do", "which activities"]):
        return {"agent_intent": "query"}
    elif any(k in msg for k in ["cancel", "closed", "delay", "storm", "rain", "strike", "problem", "missed", "reschedule", "shut"]):
        return {"agent_intent": "disrupt"}
    elif any(k in msg for k in ["plan", "create itinerary", "build itinerary", "make itinerary", "new trip"]):
        return {"agent_intent": "plan"}
    elif any(k in msg for k in ["change", "swap", "add", "remove", "update budget", "increase budget", "different hotel"]):
        return {"agent_intent": "modify"}
    return {"agent_intent": "query"}


# ── Generate Final Response (for plan/modify paths) ───────────────────────────

async def generate_response_node(state: TravelState) -> dict:
    """
    After plan/modify, generate a friendly natural-language summary response.
    """
    if state.get("response"):
        # Disruption/NLQ agents set their own response
        return {}

    itinerary = state.get("itinerary", [])
    budget = state.get("budget_summary", {})
    intent = state.get("agent_intent", "plan")
    error = state.get("error")

    if error:
        return {"response": f"I ran into an issue: {error}. Please try again."}

    if not itinerary:
        return {"response": "I wasn't able to build an itinerary. Please provide your destination, dates, and budget."}

    num_days = len(itinerary)
    total_cost = budget.get("total_estimated", 0)
    currency = budget.get("currency") or state.get("currency") or "INR"
    remaining = budget.get("remaining", 0)

    if intent in ("plan", "modify"):
        themes = [f"Day {d['day_number']}: {d.get('theme', 'Exploring')}" for d in itinerary[:3]]
        themes_str = " | ".join(themes)
        response = (
            f"🌍 Your {num_days}-day itinerary for **{state['destination']}** is ready!\n\n"
            f"**Highlights:** {themes_str}{'...' if num_days > 3 else ''}\n\n"
            f"**Total estimated cost:** {currency} {total_cost:.0f} "
            f"({f'{currency} {remaining:.0f} under budget' if remaining >= 0 else f'⚠️ {currency} {abs(remaining):.0f} over budget'})\n\n"
            f"Feel free to ask me anything about your trip — like *'What's the weather on Day 3?'* "
            f"or *'Which activities are near my hotel?'*"
        )
    else:
        response = "Your itinerary has been updated. What else can I help you with?"

    return {"response": response}


# ── Routing Logic ─────────────────────────────────────────────────────────────

def route_by_intent(state: TravelState) -> str:
    """Conditional edge: route to correct agent node based on intent."""
    intent = state.get("agent_intent", "query")
    routes = {
        "plan": "plan_trip",
        "modify": "plan_trip",
        "disrupt": "handle_disruption",
        "query": "answer_query",
    }
    return routes.get(intent, "answer_query")


def should_update_budget(state: TravelState) -> str:
    """After planning/disruption, always update budget. After query, skip."""
    if state.get("itinerary_updated"):
        return "update_budget"
    return "generate_response"


# ── Build the Graph ───────────────────────────────────────────────────────────

def build_travel_graph() -> StateGraph:
    graph = StateGraph(TravelState)

    # Add nodes
    graph.add_node("classify_intent", classify_intent_node)
    graph.add_node("plan_trip", plan_trip_node)
    graph.add_node("handle_disruption", disruption_agent_node)
    graph.add_node("answer_query", nlq_agent_node)
    graph.add_node("update_budget", budget_agent_node)
    graph.add_node("generate_response", generate_response_node)

    # Entry point
    graph.add_edge(START, "classify_intent")

    # Route from intent classifier
    graph.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "plan_trip": "plan_trip",
            "handle_disruption": "handle_disruption",
            "answer_query": "answer_query",
        },
    )

    # After planning/disruption → budget update → response
    graph.add_conditional_edges(
        "plan_trip",
        should_update_budget,
        {"update_budget": "update_budget", "generate_response": "generate_response"},
    )
    graph.add_conditional_edges(
        "handle_disruption",
        should_update_budget,
        {"update_budget": "update_budget", "generate_response": "generate_response"},
    )

    # After query → straight to response
    graph.add_edge("answer_query", "generate_response")

    # Budget always leads to response
    graph.add_edge("update_budget", "generate_response")

    # End
    graph.add_edge("generate_response", END)

    return graph.compile()


# ── Singleton compiled graph ──────────────────────────────────────────────────
travel_graph = build_travel_graph()


async def run_graph(state: TravelState) -> TravelState:
    """
    Entry point: run the full LangGraph pipeline for a user message.
    Returns the final updated state.
    """
    result = await travel_graph.ainvoke(state)
    return result
