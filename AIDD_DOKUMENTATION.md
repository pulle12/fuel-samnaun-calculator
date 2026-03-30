# AIDD-Dokumentation: Samnaun Fuel Checker

## 1. Ziel und Kontext
Diese Datei dokumentiert den aktuellen Stand des Projekts aus AIDD-Sicht (AI-Driven Development):
- welche Anforderungen iterativ entstanden sind,
- welche Technologien und Datenquellen genutzt werden,
- wie Daten verarbeitet werden,
- welche Quality-Checks und Regression-Fixes eingebaut wurden.
**Anmerkung**: Diese Dokumentation ist nicht als Nutzer- oder Entwicklerhandbuch gedacht, sondern als transparente Darstellung des Entwicklungsprozesses und der getroffenen Entscheidungen im Kontext von AI-gestützter Entwicklung. Dazu überschneidet sie sich teilweise mit Inhalten aus README.md und PRD.md, bietet aber zusätzlich Einblicke in die AIDD-spezifischen Aspekte und ist dazu auf Deutsch verfasst im Gegensatz zu den englischen Dokumenten.

## 2. AIDD-Workflow im Projekt
Das Projekt wurde in mehreren Prompt-Iterationen erweitert. Jede Iteration hat entweder neue Features, bessere Datenqualität oder bessere Transparenz eingeführt.

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
- [prompts/14-prompt.md](prompts/14-prompt.md)
- [prompts/15-prompt.md](prompts/15-prompt.md)
- [prompts/16-prompt.md](prompts/16-prompt.md)
- [prompts/17-prompt.md](prompts/17-prompt.md)
- [prompts/18-prompt.md](prompts/18-prompt.md)
- [prompts/19-prompt.md](prompts/19-prompt.md)
- [prompts/20-prompt.md](prompts/20-prompt.md)
- [prompts/21-prompt.md](prompts/21-prompt.md)
- [prompts/22-prompt.md](prompts/22-prompt.md)

Begleitdokumente:
- [PRD.md](PRD.md)
- [README.md](README.md)

## 3. Eingesetzte Technologien

### 3.1 Backend und API
- Python 3.11+
- FastAPI für API und UI-Auslieferung
- Pydantic für Request/Response-Validierung
- requests für externe HTTP-Quellen

### 3.2 Tests und Qualitaet
- pytest für Unit- und Service-Tests
- Fokus auf deterministische Kernlogik in [app/calculator.py](app/calculator.py)
- Regressionstests für Datenquellen-/Parser-Probleme in [tests/test_fuel_api.py](tests/test_fuel_api.py)

### 3.3 Laufzeit
- uvicorn als ASGI-Server

## 4. Architektur und Verantwortlichkeiten

### 4.1 Kernlogik
- [app/calculator.py](app/calculator.py): reine Berechnungslogik (trip cost, gross/net savings, break-even)
- Erweitert um optionale Reservekanister-Logik für Bruttoersparnis:
1. deaktiviert: +0 L
2. Regel Österreich: +10 L
3. Regel Schweiz: +25 L

### 4.2 Datenmodelle
- [app/models.py](app/models.py): Eingabe-/Ausgabe-Schemas inkl. fuel_type (`diesel`, `benzin95`, `benzin98`)

### 4.3 Distanz-Service
- [app/services/distance_api.py](app/services/distance_api.py): Route-Informationen
- Priorität:
1. Google Distance Matrix (optional via API Key)
2. OSRM
3. interner Fallback

### 4.4 Fuel-Service
- [app/services/fuel_api.py](app/services/fuel_api.py): Preisauflösung und Quellen-Tracking

Home-Preis Priorität:
1. manuelle Eingabe
2. bei Startort Zams: ENI-Priorisierung via E-Control
3. sonst nächste E-Control-Station am Startort
4. Fallback-Werte

Samnaun-Preis Priorität:
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

### 5.3 Österreichische Treibstoffpreise
- E-Control API

### 5.4 Samnaun-Treibstoffpreise (Live)
Aktuell wird ein Scraping-Mechanismus verwendet, weil keine stabile, frei verfügbare, offizielle JSON-API für genau diese Samnaun-Stationen integriert ist.

Quellenkette:
1. Hangl Mobility Seite (primäre Live-Quelle)
2. Interzegg Tankstellen-Seite (sekundäre Live-Quelle)
3. optionaler Custom Endpoint (`SAMNAUN_SOCAR_PRICE_API_URL`)
4. simulierte Fallback-Werte

Wichtiger technischer Punkt:
- Der Parser in [app/services/fuel_api.py](app/services/fuel_api.py) wurde von label-basiertem Matching auf block-basiertes Matching umgestellt (Diesel -> Super95 -> Super98 mit CHF-Werten), um False-Matches durch i18n/Template-Texte zu vermeiden.

## 6. UI und Favicon

### 6.1 Browser-UI
- Root-Route [app/main.py](app/main.py) liefert eine HTML-UI zur Eingabe und Ergebnisanzeige.

### 6.2 Favicon-Strategie
- Favicon wird über [app/main.py](app/main.py) robust ausgeliefert:
1. bevorzugt aus `app/static/favicon.ico`
- zusätzlich ist `/static` gemountet für statische Assets.
- gegen Browser-Cache wurde zusätzlich ein Cache-Buster (`?v=...`) in den Icon-Links eingebaut.
- `/favicon.ico` liefert explizite `Cache-Control` Header, damit Updates sichtbar werden.

## 7. End-to-End Datenfluss
1. User sendet Eingaben über UI oder `POST /calculate`.
2. Pydantic validiert Input.
3. Distanz-Service bestimmt Strecke/Zeiten + Quelle.
4. Fuel-Service bestimmt Home/Samnaun-Preis + Quellen.
5. Calculator ermittelt net savings und Entscheidung `worth_it`.
6. API antwortet mit Kennzahlen + Erklärung + Quellenkontext.

## 8. Quality-Checks und bekannte Fixes

### 8.1 Zams/ENI Regression
- Problem: ENI-Eintrag vorhanden, aber ohne gültigen Live-Preis.
- Fix: nächste gültige Live-Station in Zams verwenden statt direkt harter Fallback.
- Absicherung: Test in [tests/test_fuel_api.py](tests/test_fuel_api.py).

### 8.2 Hangl Parser Regression (Benzin 95)
- Problem: Diesel und 98 wurden gefunden, 95 fiel teilweise auf Fallback.
- Root Cause: Parser matchte u. a. Template-/Übersetzungslabels statt den realen Preisblock.
- Fix: block-basiertes Regex-Matching auf echte Reihenfolge und CHF-Werte.
- Absicherung: Tests mit Label-Rauschen in [tests/test_fuel_api.py](tests/test_fuel_api.py).

### 8.3 Favicon Sichtbarkeit in Browser-Tab
- Problem: favicon Datei vorhanden, in der Tab-Leiste aber weiterhin nicht sichtbar.
- Root Cause: Browser-caching auf `/favicon.ico` zeigte stale Ergebnis.
- Fix: cache-busting Query-Parameter in HTML plus no-cache Header auf der favicon Route.
- Ergebnis: Route zeigt korrekt auf `app/static/favicon.ico` und Browser kann aktualisiertes Icon laden.

### 8.4 E-Control SUP Proxy Regression (Zams, Benzin 95 vs 98)
- Problem: Bei `start_location=Zams` wurden für `benzin95` und `benzin98` teils identische ENI-Preise geliefert.
- Root Cause: E-Control by-address Integration lieferte für `SUP` den Labelwert `Super 95`; ein SUP-Proxy für `benzin98` führte damit zu 95/98-Verwechslung.
- Check: Live-API-Verhalten geprüft (SUP-Label `Super 95`, weitere FuelType-Codes abgelehnt), danach Reproduktions- und Regressionstest umgesetzt.
- Fix: SUP-Proxy für `benzin98` entfernt; `benzin98` wird in dieser Integration nicht mehr über E-Control aufgelöst, sondern über den 98-spezifischen Fallback (oder manuelle Eingabe).
- Absicherung: Neuer Test in [tests/test_fuel_api.py](tests/test_fuel_api.py).

### 8.5 Benzin98 API-Quelle statt Beispiel-URL
- Problem: Für `benzin98` war eine beispielhafte URL-Konfiguration nicht als echte produktive Quelle geeignet; dadurch griff die Auflösung häufig auf Fallbackwerte.
- Root Cause: Public E-Control Search-Endpunkte liefern im Integrationskontext für Benzin nur `SUP` (Super 95); gleichzeitig war kein authentifizierter 98-spezifischer API-Pfad in der Priorität aktiv.
- Check: Endpunktverhalten verifiziert (public search vs. auth-required routes), danach Prioritätskette mit echtem API-Pfad implementiert.
- Fix: Neue Priorität für `benzin98` Home-Preis: manuell -> authentifizierter E-Control Endpoint (`/sprit/1.0/gas-stations/by-address`) -> aus E-Control-SUP95 abgeleiteter 98-Wert (konfigurierbarer Aufschlag) -> optionaler benutzerdefinierter Endpoint (`HOME_BENZIN98_PRICE_API_URL`) -> Fallback.
- Absicherung: Neue Tests in [tests/test_fuel_api.py](tests/test_fuel_api.py) für authentifizierte und abgeleitete `benzin98`-Auflösung.
- Klarstellung: Quellen mit Präfix `econtrol_derived_benzin98_from_sup95_*` sind explizit geschätzte Werte (SUP95 Live-API + Aufschlag) und keine direkt gelieferten Super-98-API-Felder. (Schätzung erfolgt in fuel_api.py:369-373)

## 9. Konfiguration
- `GOOGLE_MAPS_API_KEY`: aktiviert Google-Routing
- `SAMNAUN_SOCAR_PRICE_API_URL`: optionaler Samnaun-Live-Endpoint
- `SAMNAUN_BP_PRICE_API_URL`: Legacy-Alias

## 10. Grenzen des aktuellen Ansatzes
- Externe Websites/APIs können Rate Limits oder Struktur-Änderungen haben.
- Nominatim Public Endpoint hat eine strikte Usage Policy (niedrige Request-Rate, identifizierbarer User-Agent, Caching).
- Google Distance Matrix arbeitet mit projektbezogenen Quotas/Billing-Limits.
- Public OSRM ist Best-Effort ohne harte Verfügbarkeitszusagen für produktive Last.
- HTML-Scraping hat kein garantiertes API-Vertragsniveau.
- Deshalb bleibt eine transparente Fallback-Strategie zwingend.

## 11. Beitrag und Transparenz
Eigener Beitrag (Projektsteuerung):
- Anforderungen, Priorisierung, Prompt-Iteration
- Architekturentscheidungen und Fallback-Strategie
- Validation/Abnahme anhand Tests und nachvollziehbarer Quellenketten

AI-Unterstützung:
- Codeentwurf, Refactoring und Dokumentationsvorschläge
- iterative Umsetzung entlang der Prompt-Historie
