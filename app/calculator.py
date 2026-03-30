from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ReserveCanisterRule = Literal["austria", "switzerland"]

RESERVE_CANISTER_LITERS_BY_RULE: dict[ReserveCanisterRule, float] = {
    "austria": 10.0,
    "switzerland": 25.0,
}


@dataclass(frozen=True)
class CalculationResult:
    worth_it: bool
    net_savings: float
    explanation: str
    round_trip_distance_km: float
    trip_fuel_liters: float
    trip_fuel_cost: float
    gross_savings: float
    break_even_round_trip_km: float
    reserve_canister_liters_used: float
    total_refuel_volume_liters: float


def calculate_trip_fuel_liters(round_trip_distance_km: float, consumption_l_per_100km: float) -> float:
    """Calculate liters needed for the full round trip."""
    return (round_trip_distance_km * consumption_l_per_100km) / 100.0


def calculate_trip_fuel_cost(trip_fuel_liters: float, fuel_price_home: float) -> float:
    """Calculate fuel cost for the trip when bought at home price."""
    return trip_fuel_liters * fuel_price_home


def get_reserve_canister_liters(
    include_reserve_canister: bool,
    reserve_canister_rule: ReserveCanisterRule,
) -> float:
    """Return legal reserve canister liters for the selected rule set."""
    if not include_reserve_canister:
        return 0.0
    return RESERVE_CANISTER_LITERS_BY_RULE[reserve_canister_rule]


def calculate_gross_savings(
    tank_size_liters: float,
    fuel_price_home: float,
    fuel_price_samnaun: float,
    reserve_canister_liters: float = 0.0,
) -> float:
    """Potential savings when filling a full tank plus optional reserve canister in Samnaun."""
    price_difference = fuel_price_home - fuel_price_samnaun
    total_refuel_volume_liters = max(tank_size_liters, 0.0) + max(reserve_canister_liters, 0.0)
    return max(price_difference, 0.0) * total_refuel_volume_liters


def calculate_break_even_round_trip_km(
    gross_savings: float,
    consumption_l_per_100km: float,
    fuel_price_home: float,
    time_cost_per_hour: float = 0.0,
    average_speed_kmh: float = 70.0,
) -> float:
    """Compute the round-trip distance at which net savings become zero."""
    fuel_cost_per_km = (consumption_l_per_100km / 100.0) * fuel_price_home
    time_cost_per_km = 0.0
    if time_cost_per_hour > 0.0 and average_speed_kmh > 0.0:
        time_cost_per_km = time_cost_per_hour / average_speed_kmh

    total_cost_per_km = fuel_cost_per_km + time_cost_per_km
    if gross_savings <= 0.0 or total_cost_per_km <= 0.0:
        return 0.0

    return gross_savings / total_cost_per_km


def evaluate_trip(
    round_trip_distance_km: float,
    consumption_l_per_100km: float,
    tank_size_liters: float,
    fuel_price_home: float,
    fuel_price_samnaun: float,
    include_reserve_canister: bool = False,
    reserve_canister_rule: ReserveCanisterRule = "austria",
    time_cost_per_hour: float = 0.0,
    travel_time_hours: float = 0.0,
    average_speed_kmh: float = 70.0,
) -> CalculationResult:
    """Evaluate whether refueling in Samnaun is economically beneficial."""
    trip_fuel_liters = calculate_trip_fuel_liters(round_trip_distance_km, consumption_l_per_100km)
    trip_fuel_cost = calculate_trip_fuel_cost(trip_fuel_liters, fuel_price_home)

    time_cost = max(time_cost_per_hour, 0.0) * max(travel_time_hours, 0.0)
    total_trip_cost = trip_fuel_cost + time_cost

    reserve_canister_liters = get_reserve_canister_liters(
        include_reserve_canister=include_reserve_canister,
        reserve_canister_rule=reserve_canister_rule,
    )
    total_refuel_volume_liters = max(tank_size_liters, 0.0) + reserve_canister_liters

    gross_savings = calculate_gross_savings(
        tank_size_liters=tank_size_liters,
        fuel_price_home=fuel_price_home,
        fuel_price_samnaun=fuel_price_samnaun,
        reserve_canister_liters=reserve_canister_liters,
    )
    net_savings = gross_savings - total_trip_cost

    break_even_round_trip_km = calculate_break_even_round_trip_km(
        gross_savings=gross_savings,
        consumption_l_per_100km=consumption_l_per_100km,
        fuel_price_home=fuel_price_home,
        time_cost_per_hour=max(time_cost_per_hour, 0.0),
        average_speed_kmh=average_speed_kmh,
    )

    worth_it = net_savings > 0.0
    explanation = (
        f"Round trip: {round_trip_distance_km:.1f} km, fuel needed: {trip_fuel_liters:.2f} L, "
        f"trip cost: {total_trip_cost:.2f} EUR (fuel: {trip_fuel_cost:.2f} EUR, time: {time_cost:.2f} EUR), "
        f"refuel volume considered: {total_refuel_volume_liters:.2f} L "
        f"(tank: {tank_size_liters:.2f} L, reserve canister: {reserve_canister_liters:.2f} L), "
        f"gross savings at pump: {gross_savings:.2f} EUR, net savings: {net_savings:.2f} EUR, "
        f"break-even round-trip distance: {break_even_round_trip_km:.1f} km."
    )

    return CalculationResult(
        worth_it=worth_it,
        net_savings=round(net_savings, 2),
        explanation=explanation,
        round_trip_distance_km=round(round_trip_distance_km, 2),
        trip_fuel_liters=round(trip_fuel_liters, 2),
        trip_fuel_cost=round(trip_fuel_cost, 2),
        gross_savings=round(gross_savings, 2),
        break_even_round_trip_km=round(break_even_round_trip_km, 2),
        reserve_canister_liters_used=round(reserve_canister_liters, 2),
        total_refuel_volume_liters=round(total_refuel_volume_liters, 2),
    )
