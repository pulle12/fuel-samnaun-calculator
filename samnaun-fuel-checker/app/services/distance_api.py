from __future__ import annotations

from dataclasses import dataclass


DEFAULT_ROUND_TRIP_DISTANCE_KM = 120.0
DEFAULT_AVERAGE_SPEED_KMH = 70.0

# Simple mock map; can be replaced by a real routing API later.
ROUND_TRIP_DISTANCES_KM: dict[str, float] = {
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


def get_route_info(start_location: str) -> RouteInfo:
    key = start_location.strip().lower()
    round_trip_distance_km = ROUND_TRIP_DISTANCES_KM.get(key, DEFAULT_ROUND_TRIP_DISTANCE_KM)
    travel_time_hours = round_trip_distance_km / DEFAULT_AVERAGE_SPEED_KMH

    return RouteInfo(
        start_location=start_location,
        round_trip_distance_km=round_trip_distance_km,
        average_speed_kmh=DEFAULT_AVERAGE_SPEED_KMH,
        travel_time_hours=travel_time_hours,
    )
