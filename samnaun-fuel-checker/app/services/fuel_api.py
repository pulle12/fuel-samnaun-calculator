from __future__ import annotations

from typing import Optional

import requests


SIMULATED_PRICES_EUR_PER_L: dict[str, float] = {
    "austria": 1.62,
    "samnaun": 1.34,
}


def fetch_fuel_price_from_api(
    location: str,
    fuel_type: str = "diesel",
    timeout_seconds: float = 2.0,
) -> Optional[float]:
    """
    Example external API hook.
    Returns None when API data is unavailable so callers can fall back to simulation.
    """
    url = "https://example.com/fuel-prices"
    params = {"location": location, "fuel_type": fuel_type}

    try:
        response = requests.get(url, params=params, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
        price = float(payload["price_eur_per_l"])
        if price <= 0:
            return None
        return price
    except (requests.RequestException, KeyError, TypeError, ValueError):
        return None


def get_simulated_fuel_price(location: str) -> float:
    return SIMULATED_PRICES_EUR_PER_L.get(location.strip().lower(), SIMULATED_PRICES_EUR_PER_L["austria"])
