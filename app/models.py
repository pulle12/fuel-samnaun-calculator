from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CalculationRequest(BaseModel):
    start_location: str = Field(..., min_length=2, max_length=120)
    consumption: float = Field(..., gt=0, description="Vehicle consumption in L/100km")
    tank_size: float = Field(..., gt=0, description="Tank capacity in liters")
    fuel_price_home: Optional[float] = Field(None, gt=0, description="Fuel price at home in EUR/L")
    fuel_price_samnaun: Optional[float] = Field(None, gt=0, description="Fuel price in Samnaun in EUR/L")
    time_cost_per_hour: float = Field(0.0, ge=0, description="Optional value of travel time in EUR/h")


class CalculationResponse(BaseModel):
    worth_it: bool
    net_savings: float
    explanation: str
    round_trip_distance_km: float
    trip_fuel_liters: float
    trip_fuel_cost: float
    gross_savings: float
    break_even_round_trip_km: float
