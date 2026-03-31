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
- Review of all AI-generated code for correctness and maintainability by clicking on "Behalten" (english: "Keep") or "Rückgängig" (english: "Revert") in the window popups after each code generation step.

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

Additional quality check:
- Related prompts: [prompts/16-prompt.md](prompts/16-prompt.md)
- Case: for `start_location=Zams` with `fuel_type=benzin95` and `fuel_type=benzin98`, ENI home price could become identical because the E-Control by-address query value `SUP` corresponds to Super 95.
- Check: validated endpoint behavior with live API calls and response labels (`SUP` -> `Super 95`), and confirmed unsupported fuelType variants are rejected by API validation.
- Fix: removed SUP proxy for `benzin98`; in this integration `benzin98` now uses deterministic 98-specific fallback instead of E-Control SUP.
- Acceptance: regression test added in `tests/test_fuel_api.py` ensuring `benzin98` in Zams does not use E-Control SUP proxy.

Additional quality check:
- Related prompts: [prompts/18-prompt.md](prompts/18-prompt.md), [prompts/19-prompt.md](prompts/19-prompt.md), [prompts/20-prompt.md](prompts/20-prompt.md)
- Case: configured example-style URL for `benzin98` was not a real Austria/Tirol-focused source and led to fallback usage (`eni_zams_fallback_98`) instead of a live API source.
- Check: endpoint behavior was revalidated; public E-Control `search/*` endpoint still exposes `SUP` as Super 95 only, while authenticated E-Control API routes exist and require credentials.
- Fix: removed misleading example hook and implemented a real API priority for `benzin98`: authenticated E-Control endpoint (`/sprit/1.0/gas-stations/by-address`) with credentials, then SUP95-based derived 98 estimate from live E-Control data, then optional custom endpoint (`HOME_BENZIN98_PRICE_API_URL`), then fallback.
- Acceptance: regression tests added for authenticated and derived `benzin98` resolution paths in `tests/test_fuel_api.py`.
- Clarification: source values like `econtrol_derived_benzin98_from_sup95_*` are estimates (derived from live SUP95 API data plus configurable premium delta), not direct 98-octane API price fields. (Estimation is done in fuel_api.py:369-373)

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
│   ├── 13-prompt.md
│   ├── 14-prompt.md
│   ├── 15-prompt.md
│   ├── 16-prompt.md
│   ├── 17-prompt.md
│   ├── 18-prompt.md
│   ├── 19-prompt.md
│   ├── 20-prompt.md
│   ├── 21-prompt.md
│   └── 22-prompt.md
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

## Docker

This project can be built and deployed as a container image.

### Variante 1 (einfach): Fertiges Image von DockerHub nutzen

```bash
docker pull paulsumm/samnaun-calculator:latest
docker run --rm -p 8080:8000 -d --name samnaun-calculator paulsumm/samnaun-calculator:latest
```

Then open:

- App UI: `http://127.0.0.1:8080/`
- API docs: `http://127.0.0.1:8080/docs`

If the DockerHub repository is public, no extra access must be granted.
Anyone can run `docker pull` without credentials.

### Variante 2: Lokal selbst bauen

```bash
docker build -t samnaun-calculator .
docker run --rm -p 8080:8000 -d --name samnaun-calculator samnaun-calculator
```

Then open:

- App UI: `http://127.0.0.1:8080/`
- API docs: `http://127.0.0.1:8080/docs`

### CI/CD image publishing (GitHub Actions -> DockerHub)

On each push to `main`, GitHub Actions builds and pushes Docker images to DockerHub.

Current target platforms:

- `linux/amd64`
- `linux/arm/v7`

Required GitHub repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

### Deploy on a home server (Proxmox VM)

1. Create a Linux VM in Proxmox (Debian/Ubuntu recommended).
2. Install Docker and Compose in that VM.
3. Copy `docker-compose.yml` to the VM.
4. In the VM directory, start services:

```bash
docker compose up -d
```

5. Access the app from your network using VM IP + port:

- App UI: `http://<VM_IP>:8080/`
- API docs: `http://<VM_IP>:8080/docs`

Example: if VM IP is `192.168.178.50`, open `http://192.168.178.50:8080/`.

If your image is private on DockerHub, run `docker login` on the VM first.

### Automatic updates on server

`docker-compose.yml` includes Watchtower. It periodically checks for new image versions and updates the running container automatically.

## API

### POST /calculate

Request body:

```json
{
  "start_location": "Landeck",
  "fuel_type": "diesel",
  "consumption": 6.2,
  "tank_size": 55,
  "include_reserve_canister": false,
  "reserve_canister_rule": "austria",
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
  "break_even_round_trip_km": 69.2,
  "reserve_canister_liters_used": 0.0,
  "total_refuel_volume_liters": 55.0
}
```

## Notes

- Optional reserve canister logic can be included in gross savings:
  - `reserve_canister_rule="austria"` -> 10 L
  - `reserve_canister_rule="switzerland"` -> 25 L
  - If disabled (`include_reserve_canister=false`), 0 L are added.
- Rule background (as stated by Samnaun tourism information): besides full tank, additional reserve fuel transport is possible with country-specific limits.

- Distance source priority: Google Distance Matrix (if `GOOGLE_MAPS_API_KEY` is set) -> OSRM open routing -> internal fallback map.
- Home fuel source priority:
  - Manual input if provided
  - If `start_location` is `Zams`: E-Control nearest ENI station near Zams
  - Otherwise: E-Control nearest station around geocoded start location
  - Fallback simulation if no live result is available
- Supported `fuel_type` values: `diesel`, `benzin95`, `benzin98`
- Note for `benzin98`: E-Control by-address data is not used to avoid conflating Super 95 (`SUP`) with 98-octane prices.
- `benzin98` home price source priority:
  - Manual input if provided
  - Authenticated E-Control endpoint (`/sprit/1.0/gas-stations/by-address`) when credentials are configured
  - Derived estimate from live E-Control SUP95 data (`home_source` starts with `econtrol_derived_benzin98_from_sup95_...`)
  - Configured external API via `HOME_BENZIN98_PRICE_API_URL` (supports placeholders `{location}`, `{lat}`, `{lon}`)
  - Deterministic fallback values
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

- Public data services may be rate-limited or temporarily unavailable.
- Nominatim policy limits heavy use and states an absolute maximum of about 1 request/second on the public endpoint.
- Google Distance Matrix uses quota/billing limits (for example documented element/request limits); configuration is project-specific in Google Cloud.
- The public OSRM demo server is community provided and should not be treated as unlimited production infrastructure.
- Google routing is optional and requires a valid API key and billing-enabled account.
- The exact SOCAR Samnaun live price is only available if a dedicated endpoint is configured.
- Official Samnaun price pages can change layout; parser resilience is improved but not guaranteed forever.
- Fuel station naming and matching (e.g., ENI in Zams) depends on third-party API data quality.

## API-Limit Notes by Service

- Google Distance Matrix: quota and billing controlled via Google Cloud project settings (documented per-request and per-minute limits).
- Nominatim (public OSM endpoint): strict usage policy with low-rate expectations and valid identifying User-Agent requirement.
- OSRM public demo endpoint: no SLA for heavy production usage; treat as best-effort and keep fallback active.
- E-Control Sprit API: endpoint may enforce access restrictions/availability constraints; this app therefore keeps deterministic fallback prices.

## Optional Environment Variables

- `GOOGLE_MAPS_API_KEY`: enables Google Distance Matrix routing.
- `SAMNAUN_SOCAR_PRICE_API_URL`: optional JSON endpoint for live SOCAR Samnaun price.
- `SAMNAUN_BP_PRICE_API_URL`: legacy alias, still supported for backward compatibility.
- `HOME_BENZIN98_PRICE_API_URL`: optional endpoint for home-side Super 98 price lookup.
- `ECONTROL_USERNAME`: username for authenticated E-Control endpoints.
- `ECONTROL_PASSWORD`: password for authenticated E-Control endpoints.
- `ECONTROL_BENZIN98_FUEL_TYPES`: ordered list of benzin98 fuelType candidates for authenticated endpoint lookup (default: `SUP_PLUS,SUP98,ROZ98,PLUS,SUP`).
