"""
TravelPilot — DuckDuckGo Location & Utility Tool
Used for location lookups, opening hours, and nearby POI search.
"""

from duckduckgo_search import DDGS
from typing import Optional
import re


def get_location_info(place_name: str, city: str = "") -> dict:
    """
    Search for location info: address, opening hours, coordinates.
    Returns a structured dict with available info.
    """
    query = f"{place_name} {city} address opening hours location"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        combined_text = " ".join(r.get("body", "") for r in results[:3])

        # Extract opening hours using simple pattern matching
        hours_pattern = r"(?:open|hours?)[:\s]+([^\.\n]{10,80})"
        hours_match = re.search(hours_pattern, combined_text, re.IGNORECASE)
        opening_hours = hours_match.group(1).strip() if hours_match else None

        return {
            "name": place_name,
            "city": city,
            "opening_hours": opening_hours,
            "description": results[0].get("body", "")[:400] if results else "",
            "source_url": results[0].get("href", "") if results else "",
            "raw_results": [
                {"title": r.get("title", ""), "snippet": r.get("body", "")[:200]}
                for r in results[:3]
            ],
        }

    except Exception as e:
        return {"name": place_name, "city": city, "error": str(e)}


def search_nearby(location: str, category: str, radius_km: float = 2.0) -> list[dict]:
    """
    Find nearby POIs of a given category around a location.
    category: restaurant | museum | cafe | park | transport | pharmacy | atm
    """
    query = f"Best {category} near {location} within {radius_km}km"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=8))

        places = []
        for r in results:
            places.append({
                "name": r.get("title", "Unknown"),
                "description": r.get("body", "")[:300],
                "url": r.get("href", ""),
                "category": category,
                "distance_note": f"Near {location}",
            })
        return places

    except Exception as e:
        return [{"name": "Search Error", "description": str(e), "category": category}]


def get_travel_tips(destination: str) -> dict:
    """
    Fetch general travel tips for a destination: safety, customs, currency, language.
    """
    query = f"Travel tips for {destination} — safety, currency, customs, language, transport guide"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))

        tips_text = " ".join(r.get("body", "") for r in results[:3])

        return {
            "destination": destination,
            "tips": tips_text[:1000],
            "sources": [r.get("href", "") for r in results[:3]],
        }

    except Exception as e:
        return {"destination": destination, "tips": "", "error": str(e)}


def check_visa_requirements(nationality: str, destination: str) -> dict:
    """
    Check visa requirements for a traveller's nationality to a destination.
    """
    query = f"Visa requirements for {nationality} passport holders visiting {destination} 2024"

    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))

        combined = " ".join(r.get("body", "") for r in results[:2])

        return {
            "nationality": nationality,
            "destination": destination,
            "visa_info": combined[:600],
            "source": results[0].get("href", "") if results else "",
        }

    except Exception as e:
        return {"nationality": nationality, "destination": destination, "error": str(e)}



# Alias for backwards compatibility with tests
search_location = get_location_info

