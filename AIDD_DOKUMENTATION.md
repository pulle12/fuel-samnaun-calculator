# AIDD-Dokumentation: Samnaun Fuel Checker

## 1. Ziel und Kontext
Diese Datei dokumentiert den aktuellen Stand des Projekts aus AIDD-Sicht (AI-Driven Development):
- welche Anforderungen iterativ entstanden sind,
- welche Technologien und Datenquellen genutzt werden,
- wie Daten verarbeitet werden,
- welche Quality-Checks und Regression-Fixes eingebaut wurden.

## 2. AIDD-Workflow im Projekt
Das Projekt wurde in mehreren Prompt-Iterationen erweitert. Jede Iteration hat entweder neue Features, bessere Datenqualitaet oder bessere Transparenz eingefuehrt.

Prompt-Archiv:
- [prompts/01-prompt.md](prompts/01-prompt.md)
- [prompts/02-prompt.md](prompts/02-prompt.md)
- [prompts/03-prompt.md](prompts/03-prompt.md)
- [prompts/04-prompt.md](prompts/04-prompt.md)
- [prompts/05-prompt.md](prompts/05-prompt.md)
- [prompts/06-prompt.md](prompts/06-prompt.md)
- [prompts/07-prompt.md](prompts/07-prompt.md)
- [prompts/08-prompt.md](prompts/08-prompt.md)
- [prompts/09-prompt.md](prompts/09-prompt.md)
- [prompts/10-prompt.md](prompts/10-prompt.md)
- [prompts/11-prompt.md](prompts/11-prompt.md)
- [prompts/12-prompt.md](prompts/12-prompt.md)
- [prompts/13-prompt.md](prompts/13-prompt.md)

Begleitdokumente:
- [PRD.md](PRD.md)
- [README.md](README.md)

## 3. Eingesetzte Technologien

### 3.1 Backend und API
- Python 3.11+
- FastAPI fuer API und UI-Auslieferung
- Pydantic fuer Request/Response-Validierung
- requests fuer externe HTTP-Quellen

### 3.2 Tests und Qualitaet
- pytest fuer Unit- und Service-Tests
- Fokus auf deterministische Kernlogik in [app/calculator.py](app/calculator.py)
- Regressionstests fuer Datenquellen-/Parser-Probleme in [tests/test_fuel_api.py](tests/test_fuel_api.py)

### 3.3 Laufzeit
- uvicorn als ASGI-Server

## 4. Architektur und Verantwortlichkeiten

### 4.1 Kernlogik
- [app/calculator.py](app/calculator.py): reine Berechnungslogik (trip cost, gross/net savings, break-even)

### 4.2 Datenmodelle
- [app/models.py](app/models.py): Eingabe-/Ausgabe-Schemas inkl. fuel_type (`diesel`, `benzin95`, `benzin98`)

### 4.3 Distanz-Service
- [app/services/distance_api.py](app/services/distance_api.py): Route-Informationen
- Prioritaet:
1. Google Distance Matrix (optional via API Key)
2. OSRM
3. interner Fallback

### 4.4 Fuel-Service
- [app/services/fuel_api.py](app/services/fuel_api.py): Preisaufloesung und Quellen-Tracking

Home-Preis Prioritaet:
1. manuelle Eingabe
2. bei Startort Zams: ENI-Priorisierung via E-Control
3. sonst naechste E-Control-Station am Startort
4. Fallback-Werte

Samnaun-Preis Prioritaet:
1. manuelle Eingabe
2. Live-Scraping offizieller Betreiberseiten (HTML Parsing)
3. optionaler konfigurierbarer Endpoint
4. Fallback-Werte

## 5. Datenquellen im Detail

### 5.1 Distanz
- Google Distance Matrix (optional)
- OSRM (offen)
- interne Distanz-Fallbacks

### 5.2 Geocoding
- Nominatim (OSM)

### 5.3 Oesterreichische Treibstoffpreise
- E-Control API

### 5.4 Samnaun-Treibstoffpreise (Live)
Aktuell wird ein Scraping-Mechanismus verwendet, weil keine stabile, frei verfuegbare, offizielle JSON-API fuer genau diese Samnaun-Stationen integriert ist.

Quellenkette:
1. Hangl Mobility Seite (primaere Live-Quelle)
2. Interzegg Tankstellen-Seite (sekundaere Live-Quelle)
3. optionaler Custom Endpoint (`SAMNAUN_SOCAR_PRICE_API_URL`)
4. simulierte Fallback-Werte

Wichtiger technischer Punkt:
- Der Parser in [app/services/fuel_api.py](app/services/fuel_api.py) wurde von label-basiertem Matching auf block-basiertes Matching umgestellt (Diesel -> Super95 -> Super98 mit CHF-Werten), um False-Matches durch i18n/Template-Texte zu vermeiden.

## 6. UI und Favicon

### 6.1 Browser-UI
- Root-Route [app/main.py](app/main.py) liefert eine HTML-UI zur Eingabe und Ergebnisanzeige.

### 6.2 Favicon-Strategie
- Favicon wird ueber [app/main.py](app/main.py) robust ausgeliefert:
1. bevorzugt aus `app/static/favicon.ico`
- zusaetzlich ist `/static` gemountet fuer statische Assets.
- gegen Browser-Cache wurde zusaetzlich ein Cache-Buster (`?v=...`) in den Icon-Links eingebaut.
- `/favicon.ico` liefert explizite `Cache-Control` Header, damit Updates sichtbar werden.

## 7. End-to-End Datenfluss
1. User sendet Eingaben ueber UI oder `POST /calculate`.
2. Pydantic validiert Input.
3. Distanz-Service bestimmt Strecke/Zeiten + Quelle.
4. Fuel-Service bestimmt Home/Samnaun-Preis + Quellen.
5. Calculator ermittelt net savings und Entscheidung `worth_it`.
6. API antwortet mit Kennzahlen + Erklaerung + Quellenkontext.

## 8. Quality-Checks und bekannte Fixes

### 8.1 Zams/ENI Regression
- Problem: ENI-Eintrag vorhanden, aber ohne gueltigen Live-Preis.
- Fix: naechste gueltige Live-Station in Zams verwenden statt direkt harter Fallback.
- Absicherung: Test in [tests/test_fuel_api.py](tests/test_fuel_api.py).

### 8.2 Hangl Parser Regression (Benzin 95)
- Problem: Diesel und 98 wurden gefunden, 95 fiel teilweise auf Fallback.
- Root Cause: Parser matchte u. a. Template-/Uebersetzungslabels statt den realen Preisblock.
- Fix: block-basiertes Regex-Matching auf echte Reihenfolge und CHF-Werte.
- Absicherung: Tests mit Label-Rauschen in [tests/test_fuel_api.py](tests/test_fuel_api.py).

### 8.3 Favicon Sichtbarkeit in Browser-Tab
- Problem: favicon Datei vorhanden, in der Tab-Leiste aber weiterhin nicht sichtbar.
- Root Cause: Browser-caching auf `/favicon.ico` zeigte stale Ergebnis.
- Fix: cache-busting Query-Parameter in HTML plus no-cache Header auf der favicon Route.
- Ergebnis: Route zeigt korrekt auf `app/static/favicon.ico` und Browser kann aktualisiertes Icon laden.

## 9. Konfiguration
- `GOOGLE_MAPS_API_KEY`: aktiviert Google-Routing
- `SAMNAUN_SOCAR_PRICE_API_URL`: optionaler Samnaun-Live-Endpoint
- `SAMNAUN_BP_PRICE_API_URL`: Legacy-Alias

## 10. Grenzen des aktuellen Ansatzes
- Externe Websites/APIs koennen Rate Limits oder Struktur-Aenderungen haben.
- HTML-Scraping hat kein garantiertes API-Vertragsniveau.
- Deshalb bleibt eine transparente Fallback-Strategie zwingend.

## 11. Beitrag und Transparenz
Eigener Beitrag (Projektsteuerung):
- Anforderungen, Priorisierung, Prompt-Iteration
- Architekturentscheidungen und Fallback-Strategie
- Validation/Abnahme anhand Tests und nachvollziehbarer Quellenketten

AI-Unterstuetzung:
- Codeentwurf, Refactoring und Dokumentationsvorschlaege
- iterative Umsetzung entlang der Prompt-Historie
