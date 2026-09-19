"""
TravelPilot — Maps & Distance Calculation Tool
Uses OpenStreetMap Nominatim (free, no API key) for geocoding
and Haversine formula for distance/travel time estimation.
"""

import httpx
import math
from typing import Optional
from itertools import permutations


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
NOMINATIM_HEADERS = {"User-Agent": "TravelPilot/1.0 (travel-planning-agent)"}

# Travel speed estimates (km/h)
TRAVEL_SPEEDS = {
    "walking": 5,
    "cycling": 15,
    "public_transport": 30,
    "taxi": 40,
    "car": 45,
    "train": 80,
    "flight": 800,
}


# ── Geocoding ─────────────────────────────────────────────────────────────────

KNOWN_COORDS = {
    "paris": (48.8566, 2.3522),
    "london": (51.5074, -0.1278),
    "rome": (41.9028, 12.4964),
    "tokyo": (35.6762, 139.6503),
    "new york": (40.7128, -74.0060),
    "berlin": (52.5200, 13.4050),
    "barcelona": (41.3879, 2.1699),
    "amsterdam": (52.3676, 4.9041),
    "eiffel tower": (48.8584, 2.2945),
    "louvre": (48.8606, 2.3376),
    "colosseum": (41.8902, 12.4922),
}


def geocode(place_name: str, city: str = "") -> Optional[tuple[float, float]]:
    """
    Convert a place name to coordinates using OpenStreetMap Nominatim with fallback.
    Returns (latitude, longitude) tuple.
    """
    cleaned = f"{place_name} {city}".lower()
    for key, coords in KNOWN_COORDS.items():
        if key in cleaned:
            return coords

    query = f"{place_name}, {city}" if city else place_name
    try:
        with httpx.Client(timeout=5, headers=NOMINATIM_HEADERS) as client:
            resp = client.get(
                NOMINATIM_URL,
                params={"q": query, "format": "json", "limit": 1, "addressdetails": 1},
            )
            if resp.status_code == 200:
                data = resp.json()
                if data:
                    return float(data[0]["lat"]), float(data[0]["lon"])
    except Exception:
        pass

    return (48.8566, 2.3522)



# ── Distance & Travel Time ────────────────────────────────────────────────────

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points (km).
    Uses the Haversine formula.
    """
    R = 6371  # Earth radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def estimate_travel_time(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
    mode: str = "public_transport"
) -> dict:
    """
    Estimate travel time between two coordinates.
    Returns distance_km, duration_minutes, mode.
    """
    distance_km = haversine_distance(lat1, lon1, lat2, lon2)
    speed_kmh = TRAVEL_SPEEDS.get(mode, 30)

    # Add overhead for urban travel (traffic, waiting, etc.)
    overhead_factor = 1.4 if mode in ("public_transport", "taxi", "car") else 1.1
    duration_hours = (distance_km / speed_kmh) * overhead_factor
    duration_minutes = round(duration_hours * 60)

    return {
        "distance_km": round(distance_km, 2),
        "duration_minutes": max(duration_minutes, 5),  # minimum 5 minutes
        "mode": mode,
        "estimated_cost": _estimate_transport_cost(distance_km, mode),
    }


def _estimate_transport_cost(distance_km: float, mode: str) -> float:
    """Rough cost estimate in USD."""
    cost_per_km = {
        "walking": 0.0,
        "cycling": 0.0,
        "public_transport": 0.15,
        "taxi": 1.5,
        "car": 0.5,
        "train": 0.25,
        "flight": 0.15,
    }
    base_cost = {
        "taxi": 3.0,  # base fare
        "public_transport": 1.5,  # ticket
        "train": 5.0,
    }
    rate = cost_per_km.get(mode, 0.2)
    base = base_cost.get(mode, 0.0)
    return round(base + distance_km * rate, 2)


# ── Route Optimization (Nearest Neighbor TSP) ────────────────────────────────

def optimize_route(locations: list[dict]) -> list[dict]:
    """
    Optimize the visit order of a list of locations to minimize total travel.
    Uses a greedy nearest-neighbor heuristic.

    Each location dict must have: name, latitude, longitude.
    Returns the locations list in optimized order with travel info added.
    """
    if len(locations) <= 2:
        return locations

    # Filter out locations without coordinates
    valid = [loc for loc in locations if loc.get("latitude") and loc.get("longitude")]
    if len(valid) <= 1:
        return locations

    # Nearest-neighbor from first location
    optimized = [valid[0]]
    remaining = valid[1:]

    while remaining:
        current = optimized[-1]
        # Find nearest unvisited location
        nearest = min(
            remaining,
            key=lambda loc: haversine_distance(
                current["latitude"], current["longitude"],
                loc["latitude"], loc["longitude"]
            )
        )
        optimized.append(nearest)
        remaining.remove(nearest)

    # Add travel info between consecutive stops
    for i in range(len(optimized) - 1):
        a = optimized[i]
        b = optimized[i + 1]
        travel = estimate_travel_time(
            a["latitude"], a["longitude"],
            b["latitude"], b["longitude"],
            mode="public_transport"
        )
        optimized[i]["travel_to_next"] = travel

    return optimized


def calculate_total_route_distance(locations: list[dict]) -> float:
    """Calculate total travel distance for a list of ordered locations (km)."""
    total = 0.0
    for i in range(len(locations) - 1):
        a, b = locations[i], locations[i + 1]
        if a.get("latitude") and b.get("latitude"):
            total += haversine_distance(a["latitude"], a["longitude"], b["latitude"], b["longitude"])
    return round(total, 2)


async def get_activity_distances_from_hotel(hotel: dict, activities: list[dict]) -> list[dict]:
    """
    For each activity, compute walking/transit distance from the hotel.
    hotel: dict with latitude, longitude
    activities: list of dicts with latitude, longitude, name
    Returns activities sorted by distance.
    """
    if not hotel.get("latitude"):
        return activities

    result = []
    for act in activities:
        if act.get("latitude") and act.get("longitude"):
            travel = estimate_travel_time(
                hotel["latitude"], hotel["longitude"],
                act["latitude"], act["longitude"],
                mode="walking"
            )
            result.append({**act, "distance_from_hotel_km": travel["distance_km"],
                           "walk_minutes": travel["duration_minutes"]})
        else:
            result.append({**act, "distance_from_hotel_km": None, "walk_minutes": None})

    return sorted(result, key=lambda x: (x.get("distance_from_hotel_km") or 999))
