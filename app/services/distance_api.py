from __future__ import annotations

from dataclasses import dataclass
import os

import requests


DEFAULT_ROUND_TRIP_DISTANCE_KM = 120.0
DEFAULT_AVERAGE_SPEED_KMH = 70.0
DEFAULT_TIMEOUT_SECONDS = 4.0

NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
OSRM_ROUTE_URL = "https://router.project-osrm.org/route/v1/driving/{start_lon},{start_lat};{end_lon},{end_lat}"
GOOGLE_DISTANCE_MATRIX_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"

# SOCAR Samnaun (approximate coordinates), used as fixed destination for route calculation.
SAMNAUN_SOCAR_LAT = 46.94486
SAMNAUN_SOCAR_LON = 10.36290

# Simple mock map; can be replaced by a real routing API later.
ROUND_TRIP_DISTANCES_KM: dict[str, float] = {
    "zams": 130.0,
    "landeck": 120.0,
    "innsbruck": 220.0,
    "feldkirch": 200.0,
    "chur": 170.0,
}


@dataclass(frozen=True)
class RouteInfo:
    start_location: str
    round_trip_distance_km: float
    average_speed_kmh: float
    travel_time_hours: float
    route_source: str


def _geocode_start_location(start_location: str) -> tuple[float, float] | None:
    params = {
        "q": f"{start_location}, Austria",
        "format": "jsonv2",
        "limit": 1,
    }
    headers = {"User-Agent": "samnaun-fuel-checker/0.2"}

    try:
        response = requests.get(NOMINATIM_SEARCH_URL, params=params, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    if not isinstance(payload, list) or not payload:
        return None

    first = payload[0]
    try:
        lat = float(first["lat"])
        lon = float(first["lon"])
    except (KeyError, TypeError, ValueError):
        return None

    return lat, lon


def _fetch_route_one_way_km_and_hours(start_lat: float, start_lon: float) -> tuple[float, float] | None:
    url = OSRM_ROUTE_URL.format(
        start_lon=start_lon,
        start_lat=start_lat,
        end_lon=SAMNAUN_SOCAR_LON,
        end_lat=SAMNAUN_SOCAR_LAT,
    )
    params = {
        "overview": "false",
    }

    try:
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    routes = payload.get("routes") if isinstance(payload, dict) else None
    if not routes:
        return None

    first = routes[0]
    try:
        distance_m = float(first["distance"])
        duration_s = float(first["duration"])
    except (KeyError, TypeError, ValueError):
        return None

    if distance_m <= 0 or duration_s <= 0:
        return None

    return distance_m / 1000.0, duration_s / 3600.0


def _fetch_google_route_one_way_km_and_hours(start_lat: float, start_lon: float) -> tuple[float, float] | None:
    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not api_key:
        return None

    params = {
        "origins": f"{start_lat},{start_lon}",
        "destinations": f"{SAMNAUN_SOCAR_LAT},{SAMNAUN_SOCAR_LON}",
        "mode": "driving",
        "key": api_key,
    }

    try:
        response = requests.get(GOOGLE_DISTANCE_MATRIX_URL, params=params, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    if not isinstance(payload, dict):
        return None

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        return None

    elements = rows[0].get("elements") if isinstance(rows[0], dict) else None
    if not isinstance(elements, list) or not elements:
        return None

    first_element = elements[0]
    if not isinstance(first_element, dict) or first_element.get("status") != "OK":
        return None

    distance_data = first_element.get("distance")
    duration_data = first_element.get("duration")
    if not isinstance(distance_data, dict) or not isinstance(duration_data, dict):
        return None

    try:
        distance_m = float(distance_data["value"])
        duration_s = float(duration_data["value"])
    except (KeyError, TypeError, ValueError):
        return None

    if distance_m <= 0 or duration_s <= 0:
        return None

    return distance_m / 1000.0, duration_s / 3600.0


def get_route_info(start_location: str) -> RouteInfo:
    key = start_location.strip().lower()
    start_coords = _geocode_start_location(start_location)

    if start_coords is not None:
        start_lat, start_lon = start_coords
        route_source = "none"
        route = _fetch_google_route_one_way_km_and_hours(start_lat, start_lon)
        if route is not None:
            route_source = "google_distance_matrix"
        else:
            route = _fetch_route_one_way_km_and_hours(start_lat, start_lon)
            if route is not None:
                route_source = "osrm"

        if route is not None:
            one_way_distance_km, one_way_travel_time_h = route
            round_trip_distance_km = one_way_distance_km * 2.0
            travel_time_hours = one_way_travel_time_h * 2.0
            avg_speed = round_trip_distance_km / travel_time_hours if travel_time_hours > 0 else DEFAULT_AVERAGE_SPEED_KMH

            return RouteInfo(
                start_location=start_location,
                round_trip_distance_km=round(round_trip_distance_km, 2),
                average_speed_kmh=round(avg_speed, 2),
                travel_time_hours=round(travel_time_hours, 2),
                route_source=route_source,
            )

    round_trip_distance_km = ROUND_TRIP_DISTANCES_KM.get(key, DEFAULT_ROUND_TRIP_DISTANCE_KM)
    travel_time_hours = round_trip_distance_km / DEFAULT_AVERAGE_SPEED_KMH

    return RouteInfo(
        start_location=start_location,
        round_trip_distance_km=round_trip_distance_km,
        average_speed_kmh=DEFAULT_AVERAGE_SPEED_KMH,
        travel_time_hours=travel_time_hours,
        route_source="fallback_map",
    )
