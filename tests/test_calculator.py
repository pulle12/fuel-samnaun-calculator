from __future__ import annotations

import pytest

from app.calculator import (
    calculate_break_even_round_trip_km,
    calculate_gross_savings,
    calculate_trip_fuel_cost,
    calculate_trip_fuel_liters,
    evaluate_trip,
    get_reserve_canister_liters,
)


def test_calculate_trip_fuel_liters() -> None:
    assert calculate_trip_fuel_liters(120.0, 6.5) == pytest.approx(7.8)


def test_calculate_trip_fuel_cost() -> None:
    assert calculate_trip_fuel_cost(8.0, 1.7) == pytest.approx(13.6)


def test_calculate_gross_savings_positive() -> None:
    assert calculate_gross_savings(55.0, 1.70, 1.35) == pytest.approx(19.25)


def test_calculate_gross_savings_no_price_advantage() -> None:
    assert calculate_gross_savings(55.0, 1.35, 1.35) == pytest.approx(0.0)
    assert calculate_gross_savings(55.0, 1.30, 1.35) == pytest.approx(0.0)


def test_get_reserve_canister_liters_by_rule() -> None:
    assert get_reserve_canister_liters(False, "austria") == pytest.approx(0.0)
    assert get_reserve_canister_liters(True, "austria") == pytest.approx(10.0)
    assert get_reserve_canister_liters(True, "switzerland") == pytest.approx(25.0)


def test_calculate_gross_savings_with_reserve_canister() -> None:
    # 55L tank + 10L reserve canister with 0.35 EUR/L price difference.
    assert calculate_gross_savings(55.0, 1.70, 1.35, reserve_canister_liters=10.0) == pytest.approx(22.75)


def test_calculate_break_even_round_trip_km() -> None:
    break_even = calculate_break_even_round_trip_km(
        gross_savings=20.0,
        consumption_l_per_100km=6.0,
        fuel_price_home=1.8,
        time_cost_per_hour=0.0,
        average_speed_kmh=70.0,
    )
    assert break_even == pytest.approx(185.185, rel=1e-3)


def test_evaluate_trip_worth_it() -> None:
    result = evaluate_trip(
        round_trip_distance_km=90.0,
        consumption_l_per_100km=5.5,
        tank_size_liters=60.0,
        fuel_price_home=1.75,
        fuel_price_samnaun=1.30,
    )

    assert result.worth_it is True
    assert result.net_savings > 0


def test_evaluate_trip_not_worth_it_due_to_distance() -> None:
    result = evaluate_trip(
        round_trip_distance_km=320.0,
        consumption_l_per_100km=7.0,
        tank_size_liters=45.0,
        fuel_price_home=1.62,
        fuel_price_samnaun=1.45,
    )

    assert result.worth_it is False
    assert result.net_savings < 0


def test_evaluate_trip_with_time_cost() -> None:
    result = evaluate_trip(
        round_trip_distance_km=120.0,
        consumption_l_per_100km=6.0,
        tank_size_liters=55.0,
        fuel_price_home=1.70,
        fuel_price_samnaun=1.35,
        time_cost_per_hour=25.0,
        travel_time_hours=2.0,
        average_speed_kmh=70.0,
    )

    assert result.trip_fuel_cost == pytest.approx(12.24)
    assert result.net_savings == pytest.approx(-42.99, abs=0.01)


def test_evaluate_trip_uses_reserve_canister_rule() -> None:
    result = evaluate_trip(
        round_trip_distance_km=120.0,
        consumption_l_per_100km=6.0,
        tank_size_liters=55.0,
        fuel_price_home=1.70,
        fuel_price_samnaun=1.35,
        include_reserve_canister=True,
        reserve_canister_rule="austria",
    )

    assert result.reserve_canister_liters_used == pytest.approx(10.0)
    assert result.total_refuel_volume_liters == pytest.approx(65.0)
    assert result.gross_savings == pytest.approx(22.75, abs=0.01)


def test_evaluate_trip_break_even_zero_when_no_price_difference() -> None:
    result = evaluate_trip(
        round_trip_distance_km=120.0,
        consumption_l_per_100km=6.0,
        tank_size_liters=50.0,
        fuel_price_home=1.50,
        fuel_price_samnaun=1.50,
    )

    assert result.break_even_round_trip_km == pytest.approx(0.0)
    assert result.worth_it is False
