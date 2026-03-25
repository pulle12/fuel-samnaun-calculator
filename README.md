# Samnaun Fuel Checker

A structured Python prototype that evaluates whether driving to Samnaun for refueling is financially beneficial.

## What the app does

- Uses live route distance for a start location (Google Distance Matrix if API key is set, otherwise OSRM), with fallback map distances
- Uses manual fuel prices or auto-resolved prices with source tracking
- Calculates trip fuel, trip cost, gross savings, net savings, and break-even distance
- Returns a clear recommendation and explanation via FastAPI

## Tech Stack

- Python 3.11+
- FastAPI
- pydantic
- requests
- pytest

## AIDD Workflow Note

This Project was developed using an AI-Driven Development (AIDD) approach, where the initial requirements and subsequent enhancements were guided by structured prompts. The prompts are documented in the following files:

- Prompt archive folder: `prompts/`

Detailed process, links to prompts and architecture explanation:

- [AIDD_DOKUMENTATION.md](AIDD_DOKUMENTATION.md)

## Contribution Transparency (My Role vs AI)

This project was built using AI-assisted development.

My contribution:
- Problem framing and scope definition
- Prompt design and iterative requirement refinement
- Architecture and fallback strategy decisions
- Validation of outputs, testing strategy, and acceptance checks
- Documentation structure and project narrative

Example quality checks implemented:
- Related prompts: [prompts/07-prompt.md](prompts/07-prompt.md), [prompts/08-prompt.md](prompts/08-prompt.md), [prompts/09-prompt.md](prompts/09-prompt.md)
- Case: `start_location=Zams` sometimes returned very low net savings because ENI entries were present but had no live price payload.
- Check: compared runtime output (`home_source`, `fuel_price_home`, `net_savings`) against expected live-data behavior.
- Fix: if ENI has no live price, use nearest live-priced station in Zams area before simulated fallback.
- Acceptance: regression test added in `tests/test_fuel_api.py` to keep behavior stable.

Additional quality check:
- Related prompts: [prompts/10-prompt.md](prompts/10-prompt.md), [prompts/11-prompt.md](prompts/11-prompt.md)
- Case: Hangl source parsing returned values for Diesel and 98, but not reliably for 95, causing Samnaun fallback.
- Root cause: parser matched translation labels in page content instead of the actual rendered fuel-price block.
- Fix: block-based extraction requiring the ordered pattern `Dieselpreise -> Benzinpreise (Super 95) -> Benzinpreise (Super 98)` with CHF values.
- Acceptance: parser tests updated to include translation-label noise and verify correct CHF extraction for all three fuel types.

Additional quality check:
- Related prompts: [prompts/12-prompt.md](prompts/12-prompt.md), [prompts/13-prompt.md](prompts/13-prompt.md)
- Case: favicon was served but still not visible in browser tab due to aggressive favicon caching.
- Fix: cache-busting query in HTML icon links plus explicit `Cache-Control` headers on `/favicon.ico` response.
- Acceptance: favicon endpoint resolves to `app/static/favicon.ico` with `image/x-icon` content type.

AI contribution:
- Draft implementation of modules and API wiring
- Iterative code changes based on prompt updates
- Initial test scaffolding and documentation drafts

Why this matters:
- The repository intentionally demonstrates practical AI-assisted software engineering, not manual coding-only development.

## Project Structure

```text
fuel-samnaun-calculator/
├── app/
│   ├── main.py
│   ├── calculator.py
│   ├── models.py
│   ├── static/
│   └── services/
│       ├── fuel_api.py
│       └── distance_api.py
├── tests/
│   ├── test_calculator.py
│   └── test_fuel_api.py
├── README.md
├── PRD.md
├── prompts/
│   ├── 01-prompt.md
│   ├── 02-prompt.md
│   ├── 03-prompt.md
│   ├── 04-prompt.md
│   ├── 05-prompt.md
│   ├── 06-prompt.md
│   ├── 07-prompt.md
│   ├── 08-prompt.md
│   ├── 09-prompt.md
│   ├── 10-prompt.md
│   ├── 11-prompt.md
│   ├── 12-prompt.md
│   └── 13-prompt.md
└── requirements.txt
```

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the API:

```bash
uvicorn app.main:app --reload
```

4. Open the browser GUI:

- Local app UI: `http://127.0.0.1:8000/`
- Interactive API docs: `http://127.0.0.1:8000/docs`

## API

### POST /calculate

Request body:

```json
{
  "start_location": "Landeck",
  "fuel_type": "diesel",
  "consumption": 6.2,
  "tank_size": 55,
  "fuel_price_home": 1.68,
  "fuel_price_samnaun": 1.34,
  "time_cost_per_hour": 20
}
```

Example response:

```json
{
  "worth_it": false,
  "net_savings": -24.39,
  "explanation": "Round trip: 120.0 km, fuel needed: 7.44 L, trip cost: 32.50 EUR (fuel: 12.50 EUR, time: 20.00 EUR), gross savings at pump: 18.70 EUR, net savings: -13.80 EUR, break-even round-trip distance: 69.2 km.",
  "round_trip_distance_km": 120.0,
  "trip_fuel_liters": 7.44,
  "trip_fuel_cost": 12.5,
  "gross_savings": 18.7,
  "break_even_round_trip_km": 69.2
}
```

## Notes

- Distance source priority: Google Distance Matrix (if `GOOGLE_MAPS_API_KEY` is set) -> OSRM open routing -> internal fallback map.
- Home fuel source priority:
  - Manual input if provided
  - If `start_location` is `Zams`: E-Control nearest ENI station near Zams
  - Otherwise: E-Control nearest station around geocoded start location
  - Fallback simulation if no live result is available
- Supported `fuel_type` values: `diesel`, `benzin95`, `benzin98`
- Note for `benzin98`: E-Control endpoint is queried with `SUP` (best available proxy for 98 octane on this endpoint).
- Samnaun SOCAR source priority:
  - Manual input if provided
  - Official Samnaun sources via published website data parsing:
    - `hangl-mobility.ch` (SOCAR/Mobility Center live displayed prices)
    - `interzegg.ch/de/tankstellen` as secondary live source
  - Optional custom endpoint via `SAMNAUN_SOCAR_PRICE_API_URL`
  - Fallback simulation
- Why a fallback still exists: the official websites are human-facing pages (not guaranteed stable API contracts), so parsing may occasionally fail.
- A browser GUI is available on the root endpoint `/` to enter values and inspect results visually.

## Known Limitations

- Public data services (e.g., OSRM/Nominatim) may be rate-limited or temporarily unavailable.
- Google routing is optional and requires a valid API key and billing-enabled account.
- The exact SOCAR Samnaun live price is only available if a dedicated endpoint is configured.
- Official Samnaun price pages can change layout; parser resilience is improved but not guaranteed forever.
- Fuel station naming and matching (e.g., ENI in Zams) depends on third-party API data quality.

## Optional Environment Variables

- `GOOGLE_MAPS_API_KEY`: enables Google Distance Matrix routing.
- `SAMNAUN_SOCAR_PRICE_API_URL`: optional JSON endpoint for live SOCAR Samnaun price.
- `SAMNAUN_BP_PRICE_API_URL`: legacy alias, still supported for backward compatibility.
