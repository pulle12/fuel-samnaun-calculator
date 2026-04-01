from __future__ import annotations

import pytest

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
    monkeypatch.setattr(fuel_api, "_fetch_live_samnaun_price", lambda fuel_type: None)

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
    monkeypatch.setattr(fuel_api, "_fetch_live_samnaun_price", lambda fuel_type: None)

    prices = fuel_api.resolve_fuel_prices(
        start_location="UnknownTown",
        manual_home_price=None,
        manual_samnaun_price=None,
        fuel_type="benzin98",
    )

    assert prices.fuel_price_home == fuel_api.SIMULATED_PRICES_EUR_PER_L["benzin98"]["austria"]


def test_resolve_fuel_prices_zams_benzin98_is_derived_from_sup95_when_needed(monkeypatch) -> None:
    monkeypatch.setattr(
        fuel_api,
        "_fetch_econtrol_stations_authenticated",
        lambda latitude, longitude, fuel_type_code, username, password: None,
    )

    def fake_fetch_econtrol_stations(latitude: float, longitude: float, fuel_type: str):
        assert fuel_type == "benzin95"
        return [
            {
                "name": "ENI Zams",
                "distance": 0.1,
                "prices": [{"fuelType": "SUP", "amount": 1.83, "label": "Super 95"}],
            }
        ]

    monkeypatch.setattr(fuel_api, "_fetch_econtrol_stations", fake_fetch_econtrol_stations)
    monkeypatch.setattr(fuel_api, "_fetch_live_samnaun_price", lambda fuel_type: None)

    prices = fuel_api.resolve_fuel_prices(
        start_location="Zams",
        manual_home_price=None,
        manual_samnaun_price=None,
        fuel_type="benzin98",
    )

    assert prices.fuel_price_home == pytest.approx(1.99, abs=0.001)
    assert prices.home_source.startswith("econtrol_derived_benzin98_from_sup95_eni_zams:")


def test_resolve_fuel_prices_benzin98_uses_configured_api(monkeypatch) -> None:
    monkeypatch.setenv(
        "HOME_BENZIN98_PRICE_API_URL",
        "https://example.test/price?lat={lat}&lon={lon}&location={location}",
    )
    monkeypatch.setattr(fuel_api, "_fetch_econtrol_stations", lambda latitude, longitude, fuel_type: None)
    monkeypatch.setattr(fuel_api, "_geocode_location", lambda location: (47.1569, 10.5897))
    monkeypatch.setattr(fuel_api, "_fetch_live_samnaun_price", lambda fuel_type: None)

    captured: dict[str, str] = {}

    def fake_fetch_price_from_json_endpoint(
        url: str,
        timeout_seconds: float = 3.0,
        value_keys: tuple[str, ...] = ("price_eur_per_l", "price", "diesel"),
    ) -> float:
        captured["url"] = url
        return 2.119

    monkeypatch.setattr(fuel_api, "_fetch_price_from_json_endpoint", fake_fetch_price_from_json_endpoint)

    prices = fuel_api.resolve_fuel_prices(
        start_location="Zams",
        manual_home_price=None,
        manual_samnaun_price=None,
        fuel_type="benzin98",
    )

    assert prices.fuel_price_home == 2.119
    assert prices.home_source == "home_benzin98_live_api"
    assert "lat=47.156900" in captured["url"]
    assert "lon=10.589700" in captured["url"]


def test_resolve_fuel_prices_benzin98_uses_authenticated_econtrol_when_available(monkeypatch) -> None:
    monkeypatch.setenv("ECONTROL_USERNAME", "demo-user")
    monkeypatch.setenv("ECONTROL_PASSWORD", "demo-pass")
    monkeypatch.setenv("ECONTROL_BENZIN98_FUEL_TYPES", "SUP98,SUP")

    monkeypatch.setattr(fuel_api, "_geocode_location", lambda location: (47.1569, 10.5897))
    monkeypatch.setattr(fuel_api, "_fetch_live_samnaun_price", lambda fuel_type: None)

    def fake_auth_fetch(latitude: float, longitude: float, fuel_type_code: str, username: str, password: str):
        if fuel_type_code == "SUP98":
            return [
                {
                    "name": "ENI Zams",
                    "distance": 0.1,
                    "prices": [
                        {"fuelType": "SUP98", "label": "Super 98", "amount": 2.229},
                    ],
                }
            ]
        return None

    monkeypatch.setattr(fuel_api, "_fetch_econtrol_stations_authenticated", fake_auth_fetch)

    prices = fuel_api.resolve_fuel_prices(
        start_location="Zams",
        manual_home_price=None,
        manual_samnaun_price=None,
        fuel_type="benzin98",
    )

    assert prices.fuel_price_home == 2.229
    assert prices.home_source.startswith("econtrol_auth_eni_benzin98:")


def test_resolve_fuel_prices_benzin98_derived_from_nearest_sup95(monkeypatch) -> None:
    monkeypatch.setattr(
        fuel_api,
        "_fetch_econtrol_stations_authenticated",
        lambda latitude, longitude, fuel_type_code, username, password: None,
    )
    monkeypatch.setattr(fuel_api, "_geocode_location", lambda location: (47.2, 10.6))
    monkeypatch.setattr(fuel_api, "_fetch_live_samnaun_price", lambda fuel_type: None)

    def fake_fetch_econtrol_stations(latitude: float, longitude: float, fuel_type: str):
        assert fuel_type == "benzin95"
        return [
            {
                "name": "Station A",
                "distance": 1.2,
                "prices": [{"fuelType": "SUP", "amount": 1.90, "label": "Super 95"}],
            }
        ]

    monkeypatch.setattr(fuel_api, "_fetch_econtrol_stations", fake_fetch_econtrol_stations)

    prices = fuel_api.resolve_fuel_prices(
        start_location="Landeck",
        manual_home_price=None,
        manual_samnaun_price=None,
        fuel_type="benzin98",
    )

    assert prices.fuel_price_home == pytest.approx(2.06, abs=0.001)
    assert prices.home_source.startswith("econtrol_derived_benzin98_from_sup95_nearest:")


def test_extract_hangl_price_by_fuel_type_parses_eur_values() -> None:
    page_text = (
        '"fuel_prices":"Benzinpreise (Super 95)","diesel_prices":"Dieselpreise","super_prices":"Benzinpreise (Super 98)",' 
        "Dieselpreise 1.510 CHF 1.631 EUR 1.490 CHF 1.609 EUR "
        "Benzinpreise (Super 95) 1.360 CHF 1.469 EUR 1.340 CHF 1.447 EUR "
        "Benzinpreise (Super 98) 1.480 CHF 1.598 EUR 1.460 CHF 1.577 EUR Aktueller Vorzugskurs"
    )

    assert fuel_api._extract_hangl_price_by_fuel_type(page_text, "diesel") == 1.631
    assert fuel_api._extract_hangl_price_by_fuel_type(page_text, "benzin95") == 1.469
    assert fuel_api._extract_hangl_price_by_fuel_type(page_text, "benzin98") == 1.598


def test_extract_interzegg_price_by_fuel_type_uses_cheapest_entry() -> None:
    page_text = (
        "DIESEL CHF 1,49 / 1,620 EUR BENZIN 95 CHF 1,34 / 1,456 EUR BENZIN 98 CHF 1,46 / 1,586 EUR "
        "DIESEL CHF 1,53 / 1,663 EUR BENZIN 95 CHF 1,38 / 1,500 EUR"
    )

    assert fuel_api._extract_interzegg_price_by_fuel_type(page_text, "diesel") == 1.62
    assert fuel_api._extract_interzegg_price_by_fuel_type(page_text, "benzin95") == 1.456
    assert fuel_api._extract_interzegg_price_by_fuel_type(page_text, "benzin98") == 1.586
