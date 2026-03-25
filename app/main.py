from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi import Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.responses import HTMLResponse

from app.calculator import evaluate_trip
from app.models import CalculationRequest, CalculationResponse
from app.services.distance_api import get_route_info
from app.services.fuel_api import resolve_fuel_prices

app = FastAPI(title="Samnaun Fuel Checker", version="0.1.0")
STATIC_DIR = Path(__file__).resolve().parent / "static"
FAVICON_VERSION = "20260325-2"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    favicon_path = STATIC_DIR / "favicon.ico"
    if favicon_path.exists():
        return FileResponse(
            favicon_path,
            media_type="image/x-icon",
            headers={"Cache-Control": "no-cache, no-store, must-revalidate"},
        )
    return Response(status_code=204)


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return """
<!doctype html>
<html lang="de">
<head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Samnaun Fuel Checker</title>
    <link rel="icon" type="image/x-icon" href="/favicon.ico?v=__FAVICON_VERSION__" />
    <link rel="shortcut icon" type="image/x-icon" href="/favicon.ico?v=__FAVICON_VERSION__" />
    <style>
        :root {
            --bg-1: #f4efe6;
            --bg-2: #e8f1ea;
            --card: #fffdf8;
            --ink: #1f2a2e;
            --muted: #57686d;
            --accent: #0f7b6c;
            --accent-2: #dc6a3f;
            --ok: #1f8a4c;
            --bad: #b33a3a;
            --ring: rgba(15, 123, 108, 0.25);
        }

        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: "Segoe UI", "Trebuchet MS", sans-serif;
            color: var(--ink);
            background:
                radial-gradient(circle at 20% 20%, rgba(220, 106, 63, 0.18), transparent 45%),
                radial-gradient(circle at 80% 10%, rgba(15, 123, 108, 0.16), transparent 40%),
                linear-gradient(165deg, var(--bg-1), var(--bg-2));
            min-height: 100vh;
            display: grid;
            place-items: center;
            padding: 24px;
        }

        .app-shell {
            width: min(980px, 100%);
            background: var(--card);
            border: 1px solid rgba(31, 42, 46, 0.08);
            border-radius: 22px;
            box-shadow: 0 18px 40px rgba(31, 42, 46, 0.12);
            overflow: hidden;
            animation: rise 500ms ease-out;
        }

        @keyframes rise {
            from { transform: translateY(10px); opacity: 0; }
            to { transform: translateY(0); opacity: 1; }
        }

        .header {
            background: linear-gradient(110deg, #173038, #0f7b6c 70%, #dc6a3f);
            color: #f7faf9;
            padding: 24px;
        }

        .header h1 {
            margin: 0;
            font-size: clamp(1.4rem, 2.4vw, 2rem);
            letter-spacing: 0.2px;
        }

        .header p {
            margin: 10px 0 0;
            color: rgba(247, 250, 249, 0.92);
            max-width: 760px;
        }

        .content {
            display: grid;
            grid-template-columns: 1.1fr 0.9fr;
            gap: 0;
        }

        .panel {
            padding: 22px;
        }

        .panel + .panel {
            border-left: 1px solid rgba(31, 42, 46, 0.08);
            background: #fcf8f1;
        }

        form {
            display: grid;
            gap: 14px;
        }

        .field {
            display: grid;
            gap: 6px;
        }

        label {
            font-weight: 650;
            font-size: 0.95rem;
        }

        input, select {
            border: 1px solid rgba(31, 42, 46, 0.2);
            border-radius: 10px;
            padding: 10px 12px;
            font-size: 0.98rem;
            background: #fff;
            color: var(--ink);
            transition: border-color 150ms ease, box-shadow 150ms ease;
        }

        input:focus, select:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 4px var(--ring);
            outline: none;
        }

        button {
            margin-top: 4px;
            border: 0;
            border-radius: 12px;
            padding: 12px 14px;
            font-size: 1rem;
            font-weight: 700;
            background: linear-gradient(120deg, var(--accent), #0f9a86);
            color: #f5fffd;
            cursor: pointer;
            transition: transform 120ms ease, filter 120ms ease;
        }

        button:hover {
            transform: translateY(-1px);
            filter: brightness(1.03);
        }

        .hint {
            color: var(--muted);
            font-size: 0.9rem;
            margin: 0;
        }

        .result-card {
            border: 1px solid rgba(31, 42, 46, 0.1);
            border-radius: 14px;
            padding: 14px;
            background: #fff;
            min-height: 220px;
        }

        .result-title {
            margin: 2px 0 10px;
            font-size: 1rem;
            color: var(--ink);
        }

        .price-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
            margin: 10px 0 12px;
        }

        .price-card {
            border: 1px solid rgba(31, 42, 46, 0.1);
            border-radius: 12px;
            padding: 10px;
            background: #fffaf1;
        }

        .price-card h4 {
            margin: 0 0 4px;
            font-size: 0.9rem;
            color: var(--muted);
        }

        .price-value {
            margin: 0;
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--ink);
        }

        .source-note {
            margin: 3px 0 0;
            font-size: 0.78rem;
            color: var(--muted);
        }

        .detail-list {
            margin: 10px 0 0;
            padding-left: 18px;
            color: var(--muted);
            line-height: 1.4;
            font-size: 0.92rem;
        }

        .badge {
            display: inline-block;
            border-radius: 999px;
            padding: 4px 10px;
            font-size: 0.8rem;
            font-weight: 700;
            margin-bottom: 10px;
            background: rgba(15, 123, 108, 0.14);
            color: var(--accent);
        }

        .badge.bad {
            background: rgba(179, 58, 58, 0.14);
            color: var(--bad);
        }

        .metric {
            margin: 8px 0;
            color: var(--ink);
        }

        .explain {
            margin-top: 12px;
            color: var(--muted);
            line-height: 1.45;
            font-size: 0.95rem;
        }

        @media (max-width: 860px) {
            .content { grid-template-columns: 1fr; }
            .panel + .panel { border-left: 0; border-top: 1px solid rgba(31, 42, 46, 0.08); }
        }
    </style>
</head>
<body>
    <main class="app-shell">
        <section class="header">
            <h1>Samnaun Fuel Checker</h1>
            <p>Prufe mit wenigen Eingaben, ob sich die Fahrt zum Tanken nach Samnaun wirtschaftlich lohnt.</p>
        </section>

        <section class="content">
            <div class="panel">
                <form id="calc-form">
                    <div class="field">
                        <label for="start_location">Startort</label>
                        <input id="start_location" name="start_location" value="Landeck" required />
                    </div>

                    <div class="field">
                        <label for="fuel_type">Kraftstofftyp</label>
                        <select id="fuel_type" name="fuel_type">
                            <option value="diesel" selected>Diesel</option>
                            <option value="benzin95">Benzin 95 (Super)</option>
                            <option value="benzin98">Benzin 98 (Super Plus)</option>
                        </select>
                    </div>

                    <div class="field">
                        <label for="consumption">Verbrauch (L/100 km)</label>
                        <input id="consumption" name="consumption" type="number" step="0.1" min="0.1" value="6.2" required />
                    </div>

                    <div class="field">
                        <label for="tank_size">Tankgroesse (L)</label>
                        <input id="tank_size" name="tank_size" type="number" step="0.1" min="1" value="55" required />
                    </div>

                    <div class="field">
                        <label for="fuel_price_home">Preis zuhause (EUR/L, optional)</label>
                        <input id="fuel_price_home" name="fuel_price_home" type="number" step="0.001" min="0.1" placeholder="automatisch ermitteln" />
                    </div>

                    <div class="field">
                        <label for="fuel_price_samnaun">Preis Samnaun (EUR/L, optional)</label>
                        <input id="fuel_price_samnaun" name="fuel_price_samnaun" type="number" step="0.001" min="0.1" placeholder="automatisch ermitteln" />
                    </div>

                    <div class="field">
                        <label for="time_cost_per_hour">Zeitkosten pro Stunde (EUR, optional)</label>
                        <input id="time_cost_per_hour" name="time_cost_per_hour" type="number" step="0.1" min="0" value="0" />
                    </div>

                    <button type="submit">Berechnung starten</button>
                    <p class="hint">Tipp: Leere Preisfelder nutzen Live-/Fallback-Preise. Bei Ort Zams wird fuer zuhause bevorzugt ENI Zams verwendet.</p>
                </form>
            </div>

            <div class="panel">
                <div id="result" class="result-card">
                    <p class="hint">Noch keine Berechnung. Form ausfuellen und starten.</p>
                </div>
            </div>
        </section>
    </main>

    <script>
        const form = document.getElementById("calc-form");
        const resultEl = document.getElementById("result");

        function renderResult(data) {
            const worthItClass = data.worth_it ? "" : "bad";
            const worthItText = data.worth_it ? "Lohnt sich" : "Lohnt sich nicht";
            const netClass = data.net_savings >= 0 ? "var(--ok)" : "var(--bad)";
            const fuelTypeLabelMap = {
                diesel: "Diesel",
                benzin95: "Benzin 95",
                benzin98: "Benzin 98",
            };
            const fuelTypeLabel = fuelTypeLabelMap[data.fuel_type] || data.fuel_type;
            const priceDiffPerLiter = data.fuel_price_home_used - data.fuel_price_samnaun_used;

            resultEl.innerHTML = `
                <span class="badge ${worthItClass}">${worthItText}</span>
                <h3 class="result-title">Ergebnis fuer ${fuelTypeLabel}</h3>
                <p class="metric"><strong>Nettoersparnis:</strong> <span style="color:${netClass}; font-weight:700;">${data.net_savings.toFixed(2)} EUR</span></p>
                <div class="price-grid">
                    <div class="price-card">
                        <h4>Preis lokal</h4>
                        <p class="price-value">${data.fuel_price_home_used.toFixed(3)} EUR/L</p>
                        <p class="source-note">Quelle: ${data.home_price_source}</p>
                    </div>
                    <div class="price-card">
                        <h4>Preis Samnaun</h4>
                        <p class="price-value">${data.fuel_price_samnaun_used.toFixed(3)} EUR/L</p>
                        <p class="source-note">Quelle: ${data.samnaun_price_source}</p>
                    </div>
                </div>
                <p class="metric"><strong>Round-trip Distanz:</strong> ${data.round_trip_distance_km.toFixed(1)} km</p>
                <p class="metric"><strong>Trip-Fuel:</strong> ${data.trip_fuel_liters.toFixed(2)} L</p>
                <p class="metric"><strong>Trip-Kosten (Fahrt):</strong> ${data.trip_fuel_cost.toFixed(2)} EUR</p>
                <p class="metric"><strong>Bruttoersparnis Tanken:</strong> ${data.gross_savings.toFixed(2)} EUR</p>
                <p class="metric"><strong>Break-even Distanz:</strong> ${data.break_even_round_trip_km.toFixed(1)} km</p>
                <ul class="detail-list">
                    <li>Preisvorteil pro Liter: ${priceDiffPerLiter.toFixed(3)} EUR/L</li>
                    <li>Routenquelle: ${data.route_source}</li>
                    <li>Interpretation: Nettoersparnis = Bruttoersparnis minus Fahrkosten.</li>
                </ul>
                <p class="explain"><strong>Erklaerung:</strong> ${data.explanation}</p>
            `;
        }

        function renderError(message) {
            resultEl.innerHTML = `<span class="badge bad">Fehler</span><p class="explain">${message}</p>`;
        }

        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const payload = {
                start_location: form.start_location.value,
                fuel_type: form.fuel_type.value,
                consumption: Number(form.consumption.value),
                tank_size: Number(form.tank_size.value),
                fuel_price_home: form.fuel_price_home.value ? Number(form.fuel_price_home.value) : null,
                fuel_price_samnaun: form.fuel_price_samnaun.value ? Number(form.fuel_price_samnaun.value) : null,
                time_cost_per_hour: Number(form.time_cost_per_hour.value || 0),
            };

            resultEl.innerHTML = '<p class="hint">Berechnung laeuft...</p>';

            try {
                const response = await fetch("/calculate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) {
                    const body = await response.text();
                    renderError(`API-Fehler (${response.status}): ${body}`);
                    return;
                }

                const data = await response.json();
                renderResult(data);
            } catch (error) {
                renderError("Keine Verbindung zur API oder ungueltige Eingaben.");
            }
        });
    </script>
</body>
</html>
""".replace("__FAVICON_VERSION__", FAVICON_VERSION)


@app.post("/calculate", response_model=CalculationResponse)
def calculate(request: CalculationRequest) -> CalculationResponse:
    route = get_route_info(request.start_location)
    prices = resolve_fuel_prices(
        start_location=request.start_location,
        manual_home_price=request.fuel_price_home,
        manual_samnaun_price=request.fuel_price_samnaun,
        fuel_type=request.fuel_type,
    )

    result = evaluate_trip(
        round_trip_distance_km=route.round_trip_distance_km,
        consumption_l_per_100km=request.consumption,
        tank_size_liters=request.tank_size,
        fuel_price_home=prices.fuel_price_home,
        fuel_price_samnaun=prices.fuel_price_samnaun,
        time_cost_per_hour=request.time_cost_per_hour,
        travel_time_hours=route.travel_time_hours,
        average_speed_kmh=route.average_speed_kmh,
    )

    explanation_with_sources = (
        f"{result.explanation} "
        f"Price sources: home={prices.home_source}, samnaun={prices.samnaun_source}. "
        f"Route source: {route.route_source}. Fuel type: {request.fuel_type}."
    )

    return CalculationResponse(
        worth_it=result.worth_it,
        net_savings=result.net_savings,
        explanation=explanation_with_sources,
        fuel_type=request.fuel_type,
        fuel_price_home_used=prices.fuel_price_home,
        fuel_price_samnaun_used=prices.fuel_price_samnaun,
        home_price_source=prices.home_source,
        samnaun_price_source=prices.samnaun_source,
        route_source=route.route_source,
        round_trip_distance_km=result.round_trip_distance_km,
        trip_fuel_liters=result.trip_fuel_liters,
        trip_fuel_cost=result.trip_fuel_cost,
        gross_savings=result.gross_savings,
        break_even_round_trip_km=result.break_even_round_trip_km,
    )
