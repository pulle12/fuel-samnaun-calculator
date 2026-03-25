# Samnaun Fuel Checker

A structured Python prototype that evaluates whether driving to Samnaun for refueling is financially beneficial.

## What the app does

- Uses route distance (mock service) for a start location
- Uses user-provided fuel prices (home vs. Samnaun)
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

- Prompt 1 (original specification): `copilot_prompt.md`
- Prompt 2 (Extension incl. GUI and README-hint): `02-prompt.md`

## Project Structure

```text
samnaun-fuel-checker/
├── app/
│   ├── main.py
│   ├── calculator.py
│   ├── models.py
│   └── services/
│       ├── fuel_api.py
│       └── distance_api.py
├── tests/
│   └── test_calculator.py
├── README.md
├── PRD.md
├── 02-prompt.md
├── copilot_prompt.md
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

- The current distance service is a mock map-based implementation.
- The fuel API service contains both a simulated price source and a placeholder for real API integration.
- A browser GUI is available on the root endpoint `/` to enter values and inspect results visually.
