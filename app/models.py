from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    start_location: str = Field(..., min_length=2, max_length=120)
    fuel_type: Literal["diesel", "benzin95", "benzin98"] = Field(
        "diesel",
        description="Fuel type: diesel, benzin95, or benzin98",
    )
    consumption: float = Field(..., gt=0, description="Vehicle consumption in L/100km")
    tank_size: float = Field(..., gt=0, description="Tank capacity in liters")
    include_reserve_canister: bool = Field(
        False,
        description="Include legal reserve canister fuel volume in gross savings calculation",
    )
    reserve_canister_rule: Literal["austria", "switzerland"] = Field(
        "austria",
        description="Rule set for legal reserve canister volume (austria=10L, switzerland=25L)",
    )
    fuel_price_home: Optional[float] = Field(None, gt=0, description="Fuel price at home in EUR/L")
    fuel_price_samnaun: Optional[float] = Field(None, gt=0, description="Fuel price in Samnaun in EUR/L")
    time_cost_per_hour: float = Field(0.0, ge=0, description="Optional value of travel time in EUR/h")


class CalculationResponse(BaseModel):
    worth_it: bool
    net_savings: float
    explanation: str
    fuel_type: Literal["diesel", "benzin95", "benzin98"]
    fuel_price_home_used: float
    fuel_price_samnaun_used: float
    home_price_source: str
    samnaun_price_source: str
    route_source: str
    round_trip_distance_km: float
    trip_fuel_liters: float
    trip_fuel_cost: float
    gross_savings: float
    break_even_round_trip_km: float
    reserve_canister_liters_used: float
    total_refuel_volume_liters: float
