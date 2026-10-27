# CampusPark

Permit-aware campus parking recommendation and reservation platform. Course project for SYSEN 5151, Team 25.

## What problem this addresses

A campus driver has to answer several questions before every trip. Where am I allowed to park with my permit. How far is that lot from where I am actually going. Will there be a space when I arrive. Today those answers live in different places, so the driver ends up comparing them by hand and often still guesses wrong.

CampusPark brings those pieces into one flow. The driver gives a destination, an arrival time and how long they need to park. The system checks what their permit actually allows, looks up lot locations and routes, applies the parking rules and current capacity, and comes back with options the driver is eligible to use. The driver picks one, requests a reservation, and gets a confirmation and directions.

## How a session runs

This is the normal path, modeled as use case UC.1 in our Innoslate model.

1. Driver submits identity, destination, arrival time and parking duration
2. CampusPark asks the Campus Identity & Permit System to validate identity and permit eligibility
3. CampusPark asks the Campus Map & Navigation Service for lot locations and routes
4. CampusPark applies parking rules, permit limits, location and available capacity, then presents the eligible options
5. Driver selects an option and requests a reservation
6. CampusPark rechecks eligibility and capacity, then records the reservation
7. CampusPark returns the reservation confirmation and navigation guidance

Step 6 matters more than it looks. Conditions can change between the first search and the moment the driver commits, so eligibility and capacity are checked twice rather than once.

## What sits outside the system

Four external participants, taken from the system context diagram in our Business or Mission Analysis report.

| External system or actor | What it gives us | What we send it |
| --- | --- | --- |
| Campus Driver | Destination, arrival time, parking duration, option selection, reservation request | Eligible parking options, reservation confirmation, navigation guidance |
| Campus Identity & Permit System | Identity and permit eligibility | Identity and permit validation requests |
| Campus Map & Navigation Service | Lot locations and route information | Location and route requests |
| Parking Administrator | Lot rules, permit restrictions, reservable capacity | Update acknowledgements |

CampusPark does not own permit data or map data. It reads both and is responsible for turning them into a parking decision.

## Scope

Inside: trip intake, permit-aware filtering, option ranking, reservation records, confirmation and guidance, plus the administrative data that the recommendation depends on.

Outside: cameras, parking sensors, license plate readers, physical gates, payment processing. The system also does not change university permit rules or enforce parking regulations.

That boundary follows from the solution class we picked. Of the three we evaluated, the sensor and gate version gives the best availability data but needs equipment in every lot, and the cost, installation and privacy review put it out of reach for a nine month pilot. We went with the digital-only version instead and accepted its one real weakness: availability is calculated from capacity and reservation records rather than measured, so a confirmed reservation means the platform has set capacity aside, not that a sensor has seen an empty space.

## Repository layout

```
api/                  CampusPark itself: eligibility filtering, option ranking, reservations
integrations/permit/  Client for the Campus Identity & Permit System
integrations/map/     Client for the Campus Map & Navigation Service
web/                  Driver-facing interface
docs/                 SPEC.md, TRACE.md, prompt log: notes that tie code back to the model
tests/                Chapter 3 acceptance cases, trace check, named red tests, skeleton developer tests
.github/workflows/    Automatic Chapter 3 acceptance checks
```

The top-level folders follow the system context rather than a framework's default layout, so each external system in the model has one place in the code where it is dealt with.

## Running it

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn api.main:app --reload
```

Then open http://127.0.0.1:8000. Try driver IDs `student01`, `staff01` and
`visitor01`. They hold different permits, so they get different lots back,
which is the point of the whole system. A blank or made-up ID gets no options
at all, since we can't confirm a permit for it.

## Status

The model is further along than the build, which is the order the course asks for.

Done: business and mission analysis, operational concept, system context and hierarchy, UC.1 as use case, action, activity and sequence diagrams, the operational requirements document imported into Innoslate, and a walking skeleton that runs UC.1 end to end.

The skeleton covers the success path. The permit system and the map service are fixture data, reservations live in memory and disappear on restart, and the ranking is walk time with capacity as a tie breaker rather than anything considered. Bookings are counted over the whole requested period on a single undated day, so two overlapping stays can't push a lot past its capacity.

Chapter 3: `docs/SPEC.md` now links 13 needs to 18 stakeholder requirements through 20 acceptance cases. It contains the data and AI response contracts. Each case has a named red test. One separate test checks that the SPEC, case list, and test names agree. The acceptance tests fail on purpose at this chapter, as the lab manual requires. They do not claim that the product passed field or user tests.

The Chapter 3 measures and contracts are proposed for team and stakeholder review. The SPEC records the earlier 20% search-time and 90% usable-option targets alongside the newer draft measures so the team can review the differences.

Next: review these proposed criteria and implement the named checks in later chapters. The walking skeleton still uses fixtures and memory. Chapter 3 adds the specification and acceptance checks; it does not add unreviewed application behavior.

## Chapter 3 checks

`docs/SPEC.md` is the specification used for later prompts and build work. It is kept at the existing repository path. See `tests/acceptance_cases.json` for the full 20-case need-to-requirement mapping.

```text
python -m pip install -r requirements.txt -r requirements-dev.txt
python -m pytest tests/ -v
```

The Chapter 3 result is one passing trace check, the skeleton developer tests passing, and 20 deliberately failing acceptance placeholders. Each failure names its need and criterion. Replace a placeholder with a real check when that criterion is implemented; the trace check also supports passing acceptance tests.

The developer tests in `tests/test_skeleton.py` only check that the skeleton does what its code says. They are not acceptance evidence, and they live in their own file so the trace check, which expects exactly the 20 named tests in `test_spec_acceptance.py`, keeps passing. `docs/TRACE.md` walks one need all the way to the code and lists what every file is there for.

[GitHub Actions](https://github.com/sysen5151-fall2026/campuspark-sysen5151/actions) runs `.github/workflows/chapter3-acceptance.yml` on pushes and pull requests. It checks trace coverage, runs the developer tests, then runs the red acceptance suite. A failed acceptance test makes the job fail normally, and the run summary says which failures are expected. The workflow does not hide failures or call them passing product tests.

## Team

Hangting Zhu, Junjie Luo, Yixuan Zhu, Yuxin Wang

