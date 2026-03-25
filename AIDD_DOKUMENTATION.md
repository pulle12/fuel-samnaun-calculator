# AIDD-Dokumentation: Vorgehen, Tech-Stack, Datenquellen und Verarbeitung

## 1. Ziel dieser Dokumentation
Diese Datei beschreibt, wie das Projekt mit AIDD (AI-Driven Development) aufgebaut wurde, welche Technologien eingesetzt sind, woher die Daten kommen und wie sie im System verarbeitet werden.

## 2. Was bedeutet AIDD in diesem Projekt?
AIDD bedeutet hier: Die Entwicklung erfolgte iterativ über klar abgegrenzte Prompts, die jeweils neue Anforderungen eingefuehrt haben.

Eingesetzte Prompt-Dateien im Projekt:
- `prompts/01-prompt.md`: Urspruengliche Produktanforderung und Grundstruktur
- `prompts/02-prompt.md`: GUI-Erweiterung und README-Hinweise
- `prompts/03-prompt.md`: Genauere Live-Datenanforderungen (Distanzen, Preise, Favicon)
- `prompts/04-prompt.md`: Wunsch nach umfassender technischer Erklaerung
- `prompts/05-prompt.md` bis `prompts/11-prompt.md`: weitere iterative Erweiterungen und Qualitaetsanpassungen

Begleitende Spezifikationen:
- `PRD.md`: Produktanforderungen (Problem, Nutzer, MVP, Metriken)

## 3. Entwicklungsprozess (AIDD-Workflow)
1. Anforderungen in Prompt-Form erfassen.
2. Projektstruktur erzeugen und lauffaehigen Prototyp liefern.
3. Business-Logik testbar halten (separate Calculator-Funktionen).
4. API und GUI schrittweise aufbauen.
5. Externe Datenquellen iterativ integrieren (mit klaren Fallbacks).
6. Tests erweitern, bis alle zentralen Rechenpfade abgesichert sind.
7. Dokumentation fortlaufend nachziehen.

## 4. Eingesetzter Tech-Stack

### 4.1 Sprache und Runtime
- Python 3.11+

### 4.2 Backend
- FastAPI: HTTP-API und Browser-UI-Auslieferung
- Pydantic: Request/Response-Validierung
- requests: Aufrufe externer Web-APIs

### 4.3 Testen
- pytest: Unit-Tests fuer Rechenlogik und Preisauflosung

### 4.4 Ausfuehrung
- uvicorn: ASGI-Server fuer lokale Entwicklung (`uvicorn app.main:app --reload`)

## 5. Architektur und Verantwortlichkeiten

### 5.1 `app/calculator.py`
- Reine Business-Logik
- Deterministische Berechnungen ohne Framework-Abhaengigkeit
- Kernkennzahlen:
  - Round-trip Distanz
  - Trip Fuel (Liter)
  - Trip Fuel Cost
  - Bruttoersparnis
  - Nettoersparnis
  - Break-even Distanz

### 5.2 `app/services/distance_api.py`
- Ermittelt Streckendaten zur SOCAR Samnaun
- Quelle-Prioritaet:
  1. Google Distance Matrix (wenn `GOOGLE_MAPS_API_KEY` gesetzt)
  2. OSRM (offener Routing-Dienst)
  3. Interner Fallback aus statischer Distanzmap
- Geocoding ueber Nominatim (Startort -> Koordinaten)
- Liefert auch `route_source` zur Transparenz

### 5.3 `app/services/fuel_api.py`
- Ermittelt Spritpreise fuer Zuhause und Samnaun
- Home-Preis Prioritaet:
  1. Manuelle Eingabe
  2. Bei `start_location = zams`: ENI-Priorisierung via E-Control-Stationen in Zams
  3. Sonst: naechste Station via E-Control rund um den geocodeten Startort
  4. Simulierter Fallback
- Samnaun-Preis Prioritaet:
  1. Manuelle Eingabe
  2. Optionaler Endpoint (`SAMNAUN_SOCAR_PRICE_API_URL`, legacy: `SAMNAUN_BP_PRICE_API_URL`)
  3. Simulierter Fallback
- Liefert Quellenkennzeichnung (`home_source`, `samnaun_source`)

### 5.4 `app/main.py`
- FastAPI-Endpoints:
  - `GET /`: Browser-GUI
  - `POST /calculate`: Hauptberechnung
  - `GET /favicon.ico`: Favicon-Auslieferung
- Fuehrt Distanz- und Preisservice zusammen und ruft dann die Rechenlogik auf
- Erweiterte Erklaerung im Ergebnis inkl. Datenquellen

### 5.5 `app/models.py`
- Pydantic-Modelle fuer Input/Output
- Validierung von Pflichtfeldern und numerischen Grenzen

### 5.6 `tests/`
- `test_calculator.py`: Rechenfunktionen und Edge Cases
- `test_fuel_api.py`: Preisauflosung, Prioritaeten und Fallback-Verhalten

## 6. Datenquellen im Detail

### 6.1 Distanzdaten
- Google Distance Matrix API (offiziell, key-basiert)
- OSRM Public Routing API (offen)
- Fallback-Map (lokale Distanzwerte)

### 6.2 Geocoding
- Nominatim (OpenStreetMap) fuer Ortsaufloesung in Koordinaten

### 6.3 Kraftstoffpreise (AT)
- E-Control Spritpreis-Endpoint (Stationssuche nach Koordinaten und FuelType)
- Spezieller Fokus fuer Zams: ENI-Station priorisiert

### 6.4 Kraftstoffpreise (Samnaun)
- Priorisiert veroeffentlichte Preisdarstellung der offiziellen Betreiberseiten (Hangl Mobility, dann Interzegg)
- Optionaler konfigurierbarer Endpoint fuer SOCAR Samnaun
- Ohne verfuegbare Live-Quelle: simulierter Fallback

## 7. Datenverarbeitung: End-to-End Flow
1. Nutzer gibt Eingaben in GUI oder per API.
2. `POST /calculate` validiert Request ueber Pydantic.
3. Distanzservice bestimmt Round-trip Distanz, Zeit und Routenquelle.
4. Fuelservice bestimmt Home- und Samnaun-Preis inkl. Quellenlabel.
5. Calculator berechnet Kosten, Ersparnis, Netto und Break-even.
6. API liefert strukturierte Antwort:
   - `worth_it` (bool)
   - `net_savings` (EUR)
   - `explanation` (inkl. Quellen)
   - zusaetzliche Kennzahlen fuer Nachvollziehbarkeit

## 8. Warum Fallbacks wichtig sind
Externe APIs koennen zeitweise nicht verfuegbar sein, Limits haben oder strukturell variieren. Das Projekt ist daher absichtlich resilient gebaut:
- Wenn Live-Daten fehlen, bleibt die Anwendung mit plausiblen Defaultwerten funktionsfaehig.
- Die Antwort zeigt Quellen, damit die Entscheidung nachvollziehbar bleibt.

## 9. Qualitaetssicherung
- Unit-Tests fuer Rechenkern und Service-Logik
- Klare Trennung von Business-Logik und Integrationscode
- Typisierung in allen Kernmodulen
- Lesbare, wartbare Struktur ohne Overengineering

## 10. Relevante Konfiguration
Optionale Umgebungsvariablen:
- `GOOGLE_MAPS_API_KEY`: Aktiviert Google-Distanzberechnung
- `SAMNAUN_SOCAR_PRICE_API_URL`: Optionaler Live-Preisendpoint fuer Samnaun SOCAR
- `SAMNAUN_BP_PRICE_API_URL`: Legacy-Name, weiterhin unterstuetzt

## 11. Zusammenfassung
Das System kombiniert AIDD-gestuetzte, iterative Entwicklung mit einer sauberen Python-Architektur. Die Kernberechnung ist deterministisch und testbar, waehrend externe Datenquellen flexibel angebunden sind. Durch Quellen-Priorisierung und Fallbacks bleibt die Anwendung praktisch nutzbar, transparent und robust.

## 12. Eigener Beitrag vs AI-Unterstuetzung
Diese Abgrenzung ist fuer Portfolio-Transparenz bewusst explizit dokumentiert.

Eigener Beitrag:
- Problemdefinition, Zielbild und Priorisierung der Anforderungen
- Prompt-Strategie und Iterationssteuerung (01 bis 04)
- Auswahl und Bewertung der Datenquellen (offiziell/offen/fallback)
- Architekturentscheidungen (Separation of Concerns, Fallback-Design, Erklaerbarkeit)
- Qualitaetskriterien und Testabdeckung als Abnahmegrundlage

AI-Unterstuetzung:
- Vorschlaege und Entwurf von Codebausteinen
- Umsetzung einzelner Iterationsschritte nach Promptvorgaben
- Entwuerfe fuer technische Dokumentation

Abnahmeprinzip:
- Änderungen gelten erst als uebernommen, wenn sie inhaltlich geprueft, getestet und gegen die Produktziele bewertet wurden.
