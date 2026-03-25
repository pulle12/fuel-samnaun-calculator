You are a senior Python software engineer.

Your task is to design and implement a structured, production-ready prototype of a fuel price calculator that determines whether it is economically beneficial to drive to Samnaun to refuel.

## Goal

Build a Python application that:

* Retrieves or simulates fuel prices for Austria and Samnaun
* Calculates whether a trip to Samnaun is financially beneficial
* Produces a clear, explainable result

## Core Calculation Logic

The system must include:

* Round-trip distance
* Fuel consumption (L/100km)
* Fuel required for the trip
* Cost of fuel used for the trip
* Savings from lower fuel prices in Samnaun
* Net savings or loss
* Break-even point

Output:

* Boolean: worth_it
* Numeric: net_savings (EUR)
* String: explanation

## Technical Requirements

Language:

* Python 3.11+

Libraries:

* requests
* FastAPI
* pydantic

## Project Structure

/samnaun-fuel-checker
│
├── app/
│   ├── main.py
│   ├── calculator.py
│   ├── models.py
│   ├── services/
│   │   ├── fuel_api.py
│   │   └── distance_api.py
│
├── tests/
│   ├── test_calculator.py
│
├── README.md
├── PRD.md
├── copilot_prompt.md
├── requirements.txt

## File Responsibilities

calculator.py:

* Contains all business logic
* No API or framework dependencies
* Functions must be testable and deterministic

fuel_api.py:

* Fetch or simulate fuel prices

distance_api.py:

* Provide distance calculation (mock implementation allowed)

main.py:

* FastAPI application
* Endpoint: POST /calculate

Input parameters:

* start_location
* consumption
* tank_size
* fuel_price_home
* fuel_price_samnaun
* time_cost_per_hour (optional)

models.py:

* Pydantic models for request and response

test_calculator.py:

* Unit tests for all calculations
* Include edge cases

README.md:

* Project description
* Setup instructions
* Example request/response

PRD.md:
Create a structured Product Requirements Document including:

* Problem statement
* Target users
* Value proposition
* Features (MVP and future scope)
* User stories
* Success metrics

copilot_prompt.md:

* Save this entire prompt in this file

## Code Quality Requirements

* Use type hints throughout
* Keep clear separation of concerns
* Avoid hardcoded constants
* Write readable and maintainable code
* Add comments only where necessary

## Constraints

* Do not overengineer
* Focus on correctness of calculations and clarity of structure

## Task

Generate the complete project with all files and working code.
