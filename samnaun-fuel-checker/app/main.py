from __future__ import annotations

from fastapi import FastAPI

from app.calculator import evaluate_trip
from app.models import CalculationRequest, CalculationResponse
from app.services.distance_api import get_route_info

app = FastAPI(title="Samnaun Fuel Checker", version="0.1.0")


@app.post("/calculate", response_model=CalculationResponse)
def calculate(request: CalculationRequest) -> CalculationResponse:
    route = get_route_info(request.start_location)
    result = evaluate_trip(
        round_trip_distance_km=route.round_trip_distance_km,
        consumption_l_per_100km=request.consumption,
        tank_size_liters=request.tank_size,
        fuel_price_home=request.fuel_price_home,
        fuel_price_samnaun=request.fuel_price_samnaun,
        time_cost_per_hour=request.time_cost_per_hour,
        travel_time_hours=route.travel_time_hours,
        average_speed_kmh=route.average_speed_kmh,
    )

    return CalculationResponse(
        worth_it=result.worth_it,
        net_savings=result.net_savings,
        explanation=result.explanation,
        round_trip_distance_km=result.round_trip_distance_km,
        trip_fuel_liters=result.trip_fuel_liters,
        trip_fuel_cost=result.trip_fuel_cost,
        gross_savings=result.gross_savings,
        break_even_round_trip_km=result.break_even_round_trip_km,
    )
