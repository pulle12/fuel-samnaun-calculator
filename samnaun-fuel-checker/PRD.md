# Product Requirements Document (PRD)

## 1. Problem Statement
Drivers near the Alps often assume that lower fuel prices in Samnaun always justify the trip. In reality, travel distance, fuel consumption, and optional time valuation can eliminate or reverse savings. Users need a transparent and quick way to decide whether the trip is economically beneficial.

## 2. Target Users
- Private car owners in Austria/Switzerland border regions
- Commuters and frequent drivers comparing refueling options
- Cost-conscious travelers planning Alpine routes

## 3. Value Proposition
Samnaun Fuel Checker gives a clear, explainable answer to one question: Is driving to Samnaun to refuel worth it? It combines price advantage with trip cost and exposes the full calculation path.

## 4. Features

### MVP
- Input of start location, fuel consumption, tank size, and both fuel prices
- Optional time cost per hour
- Round-trip distance retrieval via distance service (mock)
- Deterministic calculator logic:
  - Fuel needed for trip
  - Fuel trip cost
  - Gross savings from lower Samnaun price
  - Net savings or loss
  - Break-even round-trip distance
- API response including:
  - worth_it (boolean)
  - net_savings (EUR)
  - explanation (human-readable)

### Future Scope
- Real routing API integration with traffic-aware travel times
- Real fuel price API integrations by fuel type
- Multi-stop route optimization
- Historical trend analysis for fuel prices
- Frontend dashboard and scenario comparison

## 5. User Stories
1. As a driver, I want to enter my car consumption and tank size so that the result matches my vehicle.
2. As a user, I want a simple true/false decision so that I can decide quickly.
3. As a user, I want to see net savings in EUR so that I can quantify the benefit.
4. As a user, I want an explanation of the calculation so that I can trust the result.
5. As a planner, I want a break-even distance so that I can understand when the trip stops being profitable.

## 6. Success Metrics
- Calculation correctness verified by unit tests
- API response time below 300 ms for mock services
- Explanation completeness: includes all core variables in output
- User decision confidence: binary recommendation and net EUR in every response
