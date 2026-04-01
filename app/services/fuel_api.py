from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Literal, Optional
from urllib.parse import quote_plus

import requests


FuelType = Literal["diesel", "benzin95", "benzin98"]

# Das sind meine Fallback-Daten falls keine API geht. Kommentar selbst geschrieben.
SIMULATED_PRICES_EUR_PER_L: dict[FuelType, dict[str, float]] = {
    "diesel": {
        "austria": 1.74,
        "samnaun_socar": 1.47,
        "eni_zams": 1.71,
    },
    "benzin95": {
        "austria": 1.87,
        "samnaun_socar": 1.59,
        "eni_zams": 1.83,
    },
    "benzin98": {
        "austria": 2.04,
        "samnaun_socar": 1.76,
        "eni_zams": 1.99,
    },
}

DEFAULT_TIMEOUT_SECONDS = 4.0
NOMINATIM_SEARCH_URL = "https://nominatim.openstreetmap.org/search"
ECONTROL_SEARCH_URL = "https://api.e-control.at/sprit/1.0/search/gas-stations/by-address"
ECONTROL_AUTH_SEARCH_URL = "https://api.e-control.at/sprit/1.0/gas-stations/by-address"
HANGL_MOBILITY_URL = "https://www.hangl-mobility.ch/"
INTERZEGG_TANKSTELLEN_URL = "https://www.interzegg.ch/de/tankstellen"

# E-Control by-address endpoint provides DIE and SUP in this integration context.
# For benzin98 we intentionally avoid SUP proxy usage to prevent 95/98 price conflation.
ECONTROL_FUEL_TYPE_BY_APP: dict[FuelType, Optional[str]] = {
    "diesel": "DIE",
    "benzin95": "SUP",
    "benzin98": None,
}

# ENI station in Zams area (used as priority home source for start_location=zams).
ZAMS_LAT = 47.1569
ZAMS_LON = 10.5897


@dataclass(frozen=True)
class FuelPrices:
    fuel_price_home: float
    fuel_price_samnaun: float
    home_source: str
    samnaun_source: str


def _safe_float(value: object) -> Optional[float]:
    try:
        number = float(value)
        if number <= 0:
            return None
        return number
    except (TypeError, ValueError):
        return None


def _fetch_price_from_json_endpoint(
    url: str,
    timeout_seconds: float = 3.0,
    value_keys: tuple[str, ...] = ("price_eur_per_l", "price", "diesel"),
) -> Optional[float]:
    try:
        response = requests.get(url, timeout=timeout_seconds, headers={"User-Agent": "samnaun-fuel-checker/0.2"})
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    if isinstance(payload, dict):
        for key in value_keys:
            if key in payload:
                parsed = _safe_float(payload.get(key))
                if parsed is not None:
                    return parsed
    return None


def _fetch_page_text(url: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> Optional[str]:
    headers = {"User-Agent": "samnaun-fuel-checker/0.4"}
    try:
        response = requests.get(url, timeout=timeout_seconds, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Keep parsing simple and robust by flattening HTML to text.
    html_text = response.text
    text = re.sub(r"<[^>]+>", " ", html_text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _fetch_page_html(url: str, timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS) -> Optional[str]:
    headers = {"User-Agent": "samnaun-fuel-checker/0.4"}
    try:
        response = requests.get(url, timeout=timeout_seconds, headers=headers)
        response.raise_for_status()
    except requests.RequestException:
        return None
    return response.text


def _parse_price_token(raw: str) -> Optional[float]:
    normalized = raw.strip().replace(" ", "").replace("'", "").replace(",", ".")
    return _safe_float(normalized)


def _extract_hangl_exchange_rate(page_html: str) -> Optional[float]:
    match = re.search(
        r"JS-fuel-prices-container[^>]*data-rate=\"([0-9]{1,2}[\.,][0-9]{1,3})\"",
        page_html,
        flags=re.IGNORECASE,
    )
    if not match:
        return None
    return _parse_price_token(match.group(1))


def _extract_hangl_socar_chf_by_fuel_type(page_html: str, fuel_type: FuelType) -> Optional[float]:
    pattern_by_fuel_type: dict[FuelType, str] = {
        "diesel": r"<span>\s*Dieselpreise\s*</span>.*?<span\s+data-price=\"(\d{1,2}[\.,]\d{2,3})\">",
        "benzin95": r"<span>\s*Benzinpreise\s*\(Super\s*95\)\s*</span>.*?<span\s+data-price=\"(\d{1,2}[\.,]\d{2,3})\">",
        "benzin98": r"<span>\s*Benzinpreise\s*\(Super\s*98\)\s*</span>.*?<span\s+data-price=\"(\d{1,2}[\.,]\d{2,3})\">",
    }
    match = re.search(pattern_by_fuel_type[fuel_type], page_html, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return None
    return _parse_price_token(match.group(1))


def _extract_hangl_price_by_fuel_type(page_html: str, fuel_type: FuelType) -> Optional[float]:
    exchange_rate = _extract_hangl_exchange_rate(page_html)
    if exchange_rate is None:
        return None

    # First price pair in each fuel block is SOCAR; second one is Mobility.
    socar_chf = _extract_hangl_socar_chf_by_fuel_type(page_html, fuel_type)
    if socar_chf is None:
        return None

    return round(socar_chf * exchange_rate, 3)


def _extract_interzegg_price_by_fuel_type(page_text: str, fuel_type: FuelType) -> Optional[float]:
    pattern_by_fuel_type: dict[FuelType, str] = {
        "diesel": r"DIESEL\s*CHF\s*\d{1,2}[\.,]\d{2,3}\s*/\s*(\d{1,2}[\.,]\d{2,3})\s*EUR",
        "benzin95": r"BENZIN\s*95\s*CHF\s*\d{1,2}[\.,]\d{2,3}\s*/\s*(\d{1,2}[\.,]\d{2,3})\s*EUR",
        "benzin98": r"BENZIN\s*98\s*CHF\s*\d{1,2}[\.,]\d{2,3}\s*/\s*(\d{1,2}[\.,]\d{2,3})\s*EUR",
    }

    matches = re.findall(pattern_by_fuel_type[fuel_type], page_text, flags=re.IGNORECASE)
    if not matches:
        return None

    parsed_prices = [_parse_price_token(raw) for raw in matches]
    valid_prices = [price for price in parsed_prices if price is not None]
    if not valid_prices:
        return None

    # Interzegg lists multiple station brands; take the cheapest currently published price.
    return min(valid_prices)


def _fetch_live_samnaun_price(fuel_type: FuelType) -> Optional[tuple[float, str]]:
    hangl_page_html = _fetch_page_html(HANGL_MOBILITY_URL)
    if hangl_page_html:
        hangl_price = _extract_hangl_price_by_fuel_type(hangl_page_html, fuel_type)
        if hangl_price is not None:
            return hangl_price, "samnaun_socar_live_hangl_html"

    interzegg_page_text = _fetch_page_text(INTERZEGG_TANKSTELLEN_URL)
    if interzegg_page_text:
        interzegg_price = _extract_interzegg_price_by_fuel_type(interzegg_page_text, fuel_type)
        if interzegg_price is not None:
            return interzegg_price, "samnaun_live_interzegg_html"

    return None


def _geocode_location(location: str) -> Optional[tuple[float, float]]:
    params = {
        "q": f"{location}, Austria",
        "format": "jsonv2",
        "limit": 1,
    }
    headers = {"User-Agent": "samnaun-fuel-checker/0.3"}

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
        return float(first["lat"]), float(first["lon"])
    except (KeyError, TypeError, ValueError):
        return None


def _fetch_econtrol_stations(latitude: float, longitude: float, fuel_type: FuelType) -> Optional[list[dict]]:
    econtrol_fuel_type = ECONTROL_FUEL_TYPE_BY_APP[fuel_type]
    if econtrol_fuel_type is None:
        return None

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "fuelType": econtrol_fuel_type,
    }
    headers = {"User-Agent": "samnaun-fuel-checker/0.3"}

    try:
        response = requests.get(ECONTROL_SEARCH_URL, params=params, headers=headers, timeout=DEFAULT_TIMEOUT_SECONDS)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    if isinstance(payload, list):
        return payload
    return None


def _fetch_econtrol_stations_authenticated(
    latitude: float,
    longitude: float,
    fuel_type_code: str,
    username: str,
    password: str,
) -> Optional[list[dict]]:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "fuelType": fuel_type_code,
    }
    headers = {"User-Agent": "samnaun-fuel-checker/0.3"}

    try:
        response = requests.get(
            ECONTROL_AUTH_SEARCH_URL,
            params=params,
            headers=headers,
            auth=(username, password),
            timeout=DEFAULT_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError):
        return None

    if isinstance(payload, list):
        return payload
    return None


def _extract_station_price(station: dict, fuel_type: FuelType) -> Optional[float]:
    prices = station.get("prices")
    if not isinstance(prices, list):
        return None

    expected_econtrol_fuel_type = ECONTROL_FUEL_TYPE_BY_APP[fuel_type]
    if expected_econtrol_fuel_type is None:
        return None

    for entry in prices:
        if not isinstance(entry, dict):
            continue
        entry_fuel_type = str(entry.get("fuelType", "")).upper()
        if entry_fuel_type != expected_econtrol_fuel_type:
            continue
        parsed = _safe_float(entry.get("amount"))
        if parsed is not None:
            return parsed
    return None


def _pick_station_price(
    stations: list[dict],
    fuel_type: FuelType,
    brand_contains: Optional[str] = None,
) -> Optional[tuple[float, str]]:
    selected: list[tuple[float, float, str]] = []

    for station in stations:
        if not isinstance(station, dict):
            continue

        name = str(station.get("name", "")).strip()
        if not name:
            continue

        if brand_contains and brand_contains.lower() not in name.lower():
            continue

        price = _extract_station_price(station, fuel_type)
        if price is None:
            continue

        distance = _safe_float(station.get("distance")) or 999999.0
        selected.append((distance, price, name))

    if not selected:
        return None

    selected.sort(key=lambda item: item[0])
    _, price, name = selected[0]
    return price, name


def _extract_station_price_98(station: dict) -> Optional[float]:
    prices = station.get("prices")
    if not isinstance(prices, list):
        return None

    for entry in prices:
        if not isinstance(entry, dict):
            continue

        label = str(entry.get("label", "")).lower()
        entry_fuel_type = str(entry.get("fuelType", "")).upper()
        if "98" not in label and "98" not in entry_fuel_type:
            continue

        parsed = _safe_float(entry.get("amount"))
        if parsed is not None:
            return parsed
    return None


def _pick_station_price_98(
    stations: list[dict],
    brand_contains: Optional[str] = None,
) -> Optional[tuple[float, str]]:
    selected: list[tuple[float, float, str]] = []

    for station in stations:
        if not isinstance(station, dict):
            continue

        name = str(station.get("name", "")).strip()
        if not name:
            continue

        if brand_contains and brand_contains.lower() not in name.lower():
            continue

        price = _extract_station_price_98(station)
        if price is None:
            continue

        distance = _safe_float(station.get("distance")) or 999999.0
        selected.append((distance, price, name))

    if not selected:
        return None

    selected.sort(key=lambda item: item[0])
    _, price, name = selected[0]
    return price, name


def _derive_benzin98_from_sup95_price(sup95_price: float) -> float:
    premium_delta = _safe_float(os.getenv("HOME_BENZIN98_PREMIUM_DELTA_EUR", "0.16"))
    if premium_delta is None:
        premium_delta = 0.16
    return round(sup95_price + premium_delta, 3)


def get_simulated_fuel_price(location: str, fuel_type: FuelType = "diesel") -> float:
    key = location.strip().lower()
    prices_for_fuel = SIMULATED_PRICES_EUR_PER_L[fuel_type]
    if key in prices_for_fuel:
        return prices_for_fuel[key]
    return prices_for_fuel["austria"]


def _resolve_home_price(
    start_location: str,
    manual_home_price: Optional[float],
    fuel_type: FuelType,
) -> tuple[float, str]:
    if manual_home_price is not None:
        return manual_home_price, "manual_input"

    # For benzin98, prefer explicit 98 APIs first; otherwise derive an estimate from live SUP95.
    if fuel_type == "benzin98":
        is_zams = start_location.strip().lower() == "zams"
        search_coords = (ZAMS_LAT, ZAMS_LON) if is_zams else _geocode_location(start_location)

        econtrol_username = os.getenv("ECONTROL_USERNAME", "").strip()
        econtrol_password = os.getenv("ECONTROL_PASSWORD", "").strip()
        econtrol_benzin98_fuel_types = [
            code.strip()
            for code in os.getenv("ECONTROL_BENZIN98_FUEL_TYPES", "SUP_PLUS,SUP98,ROZ98,PLUS,SUP").split(",")
            if code.strip()
        ]

        if econtrol_username and econtrol_password and search_coords is not None:
            lat, lon = search_coords
            for fuel_code in econtrol_benzin98_fuel_types:
                stations = _fetch_econtrol_stations_authenticated(
                    latitude=lat,
                    longitude=lon,
                    fuel_type_code=fuel_code,
                    username=econtrol_username,
                    password=econtrol_password,
                )
                if not stations:
                    continue

                if is_zams:
                    eni_choice = _pick_station_price_98(stations, brand_contains="eni")
                    if eni_choice is not None:
                        price, station_name = eni_choice
                        return price, f"econtrol_auth_eni_benzin98:{station_name}:{fuel_code}"

                nearest_choice = _pick_station_price_98(stations)
                if nearest_choice is not None:
                    price, station_name = nearest_choice
                    return price, f"econtrol_auth_nearest_benzin98:{station_name}:{fuel_code}"

        if search_coords is not None:
            lat, lon = search_coords
            sup_stations = _fetch_econtrol_stations(lat, lon, fuel_type="benzin95")
            if sup_stations:
                if is_zams:
                    eni_sup_choice = _pick_station_price(sup_stations, fuel_type="benzin95", brand_contains="eni")
                    if eni_sup_choice is not None:
                        sup_price, station_name = eni_sup_choice
                        derived_price = _derive_benzin98_from_sup95_price(sup_price)
                        return derived_price, f"econtrol_derived_benzin98_from_sup95_eni_zams:{station_name}"

                nearest_sup_choice = _pick_station_price(sup_stations, fuel_type="benzin95")
                if nearest_sup_choice is not None:
                    sup_price, station_name = nearest_sup_choice
                    derived_price = _derive_benzin98_from_sup95_price(sup_price)
                    return derived_price, f"econtrol_derived_benzin98_from_sup95_nearest:{station_name}"

        benzin98_api_url_template = os.getenv("HOME_BENZIN98_PRICE_API_URL", "").strip()
        if benzin98_api_url_template and search_coords is not None:
            lat, lon = search_coords
            formatted_url = benzin98_api_url_template.format(
                location=quote_plus(start_location.strip()),
                lat=f"{lat:.6f}",
                lon=f"{lon:.6f}",
            )
            benzin98_price = _fetch_price_from_json_endpoint(
                formatted_url,
                value_keys=(
                    "price_eur_per_l",
                    "price",
                    "benzin98",
                    "super98",
                    "premium98",
                    "amount",
                ),
            )
            if benzin98_price is not None:
                return benzin98_price, "home_benzin98_live_api"

        if is_zams:
            return get_simulated_fuel_price("eni_zams", fuel_type=fuel_type), "eni_zams_fallback_98"
        return get_simulated_fuel_price("austria", fuel_type=fuel_type), "austria_fallback_98"

    is_zams = start_location.strip().lower() == "zams"
    if is_zams:
        zams_stations = _fetch_econtrol_stations(ZAMS_LAT, ZAMS_LON, fuel_type=fuel_type)
        if zams_stations:
            eni_choice = _pick_station_price(zams_stations, fuel_type=fuel_type, brand_contains="eni")
            if eni_choice is not None:
                price, station_name = eni_choice
                return price, f"econtrol_eni_zams:{station_name}"

            # If ENI is found but has no valid live price, use nearest live station in Zams area.
            nearest_choice = _pick_station_price(zams_stations, fuel_type=fuel_type)
            if nearest_choice is not None:
                price, station_name = nearest_choice
                return price, f"econtrol_nearest_zams:{station_name}"

        return get_simulated_fuel_price("eni_zams", fuel_type=fuel_type), "eni_zams_fallback"

    coords = _geocode_location(start_location)
    if coords is not None:
        stations = _fetch_econtrol_stations(coords[0], coords[1], fuel_type=fuel_type)
        if stations:
            nearest = _pick_station_price(stations, fuel_type=fuel_type)
            if nearest is not None:
                price, station_name = nearest
                return price, f"econtrol_nearest:{station_name}"

    return get_simulated_fuel_price("austria", fuel_type=fuel_type), "austria_fallback"


def _resolve_samnaun_price(manual_samnaun_price: Optional[float], fuel_type: FuelType) -> tuple[float, str]:
    if manual_samnaun_price is not None:
        return manual_samnaun_price, "manual_input"

    live_price = _fetch_live_samnaun_price(fuel_type)
    if live_price is not None:
        return live_price

    # Optional station-specific endpoint, e.g. an internal proxy to a paid/official provider.
    samnaun_socar_url = os.getenv("SAMNAUN_SOCAR_PRICE_API_URL", "").strip()
    if not samnaun_socar_url:
        # Backward compatibility for previous variable naming.
        samnaun_socar_url = os.getenv("SAMNAUN_BP_PRICE_API_URL", "").strip()

    if samnaun_socar_url:
        live_price = _fetch_price_from_json_endpoint(samnaun_socar_url)
        if live_price is not None:
            return live_price, "samnaun_socar_live_api"

    return get_simulated_fuel_price("samnaun_socar", fuel_type=fuel_type), "samnaun_socar_fallback"


def resolve_fuel_prices(
    start_location: str,
    manual_home_price: Optional[float],
    manual_samnaun_price: Optional[float],
    fuel_type: FuelType = "diesel",
) -> FuelPrices:
    home_price, home_source = _resolve_home_price(start_location, manual_home_price, fuel_type)
    samnaun_price, samnaun_source = _resolve_samnaun_price(manual_samnaun_price, fuel_type)

    return FuelPrices(
        fuel_price_home=home_price,
        fuel_price_samnaun=samnaun_price,
        home_source=home_source,
        samnaun_source=samnaun_source,
    )
