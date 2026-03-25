from __future__ import annotations

from app.services import fuel_api


def test_resolve_fuel_prices_uses_manual_values() -> None:
    prices = fuel_api.resolve_fuel_prices(
        start_location="Zams",
        manual_home_price=1.75,
        manual_samnaun_price=1.33,
    )

    assert prices.fuel_price_home == 1.75
    assert prices.fuel_price_samnaun == 1.33
    assert prices.home_source == "manual_input"
    assert prices.samnaun_source == "manual_input"


def test_resolve_fuel_prices_zams_prefers_eni_from_econtrol(monkeypatch) -> None:
    def fake_fetch_econtrol_stations(latitude: float, longitude: float, fuel_type: str) -> list[dict]:
        return [
            {
                "name": "Some Other Station",
                "distance": 0.01,
                "prices": [{"fuelType": "DIE", "amount": 1.90}],
            },
            {
                "name": "ENI",
                "distance": 0.05,
                "prices": [{"fuelType": "DIE", "amount": 1.80}],
            },
        ]

    monkeypatch.setattr(fuel_api, "_fetch_econtrol_stations", fake_fetch_econtrol_stations)

    prices = fuel_api.resolve_fuel_prices(
        start_location="Zams",
        manual_home_price=None,
        manual_samnaun_price=None,
    )

    assert prices.fuel_price_home == 1.80
    assert prices.home_source.startswith("econtrol_eni_zams")


def test_resolve_fuel_prices_fallback_when_no_live_data(monkeypatch) -> None:
    monkeypatch.setattr(fuel_api, "_fetch_econtrol_stations", lambda latitude, longitude, fuel_type: None)
    monkeypatch.setattr(fuel_api, "_geocode_location", lambda location: None)

    prices = fuel_api.resolve_fuel_prices(
        start_location="UnknownTown",
        manual_home_price=None,
        manual_samnaun_price=None,
    )

    assert prices.home_source == "austria_fallback"
    assert prices.samnaun_source == "samnaun_socar_fallback"


def test_resolve_fuel_prices_zams_uses_nearest_live_when_eni_has_no_price(monkeypatch) -> None:
    def fake_fetch_econtrol_stations(latitude: float, longitude: float, fuel_type: str) -> list[dict]:
        return [
            {
                "name": "ENI",
                "distance": 0.01,
                "prices": [],
            },
            {
                "name": "AVANTI",
                "distance": 0.30,
                "prices": [{"fuelType": "DIE", "amount": 2.20}],
            },
        ]

    monkeypatch.setattr(fuel_api, "_fetch_econtrol_stations", fake_fetch_econtrol_stations)

    prices = fuel_api.resolve_fuel_prices(
        start_location="Zams",
        manual_home_price=None,
        manual_samnaun_price=None,
    )

    assert prices.fuel_price_home == 2.20
    assert prices.home_source.startswith("econtrol_nearest_zams")


def test_resolve_fuel_prices_supports_benzin98_simulation(monkeypatch) -> None:
    monkeypatch.setattr(fuel_api, "_fetch_econtrol_stations", lambda latitude, longitude, fuel_type: None)
    monkeypatch.setattr(fuel_api, "_geocode_location", lambda location: None)

    prices = fuel_api.resolve_fuel_prices(
        start_location="UnknownTown",
        manual_home_price=None,
        manual_samnaun_price=None,
        fuel_type="benzin98",
    )

    assert prices.fuel_price_home == fuel_api.SIMULATED_PRICES_EUR_PER_L["benzin98"]["austria"]
