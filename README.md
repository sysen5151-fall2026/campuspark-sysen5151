# CampusPark

Permit-aware campus parking recommendation and reservation platform. Course project for SYSEN 5151, Team 25.

The product runs end to end from this repository: search, booking with a second check, the pass, cancellation, and a staff console that changes the rules. The permit and map services are still fixture data. The [status table](#status) says what works, what is partial and what is not built yet.

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
api/                  Web routes (main.py) and the wiring that runs the functions in use-case order (service.py)
functions/            One module per first-level function, F.1 to F.7, plus C.5.3 Capacity Ledger and SR.6 cancellation
data/                 SQLite schema and data access for saved reservations (C.5)
integrations/permit/  Client for the Campus Identity & Permit System, fixture data for now
integrations/map/     Client for the Campus Map & Navigation Service, fixture data for now
contracts/            api-v1.yaml, the interface contract between functions, and the stubs generated from it
web/                  Driver pages and the staff console
docs/                 SPEC, traceability, route table, deployment view, ADRs, risks, prompt and deviation logs
prompts/              Prompts used to generate components from their specifications
tests/                Tests named by requirement ID, contract checks, Chapter 3 acceptance placeholders
tools/                gen_stubs.py rebuilds contracts/generated from the contract
.github/workflows/    tests.yml (should pass) and chapter3-acceptance.yml (fails on purpose)
```

The layout follows the model. Each function on the first-level IDEF0 has one module in `functions/`, and each external system has one folder in `integrations/`. `docs/traceability.md` maps every function to its module, requirements and tests, and `docs/deployment.md` maps every subsystem to its code.

## Running it

```
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn api.main:app --port 8000
```

Then open http://127.0.0.1:8000. Driver IDs `student01`, `staff01` and `visitor01` hold different permits, so they get different lots back. A blank or made-up ID gets no options, since no permit can be confirmed for it. The staff console is at http://127.0.0.1:8000/admin with the demo account `admin01`.

Bookings are saved in `data/campuspark.db`, which is not committed, and they survive a restart. Staff rule changes are held in memory and reset when the server restarts.

A scenario to try, taken from UC.1 and UC.2:

1. As `student01`, search for Duffield Hall, arriving later today for two hours. Only lots the student permit allows come back, nearest first.
2. Pick Forest Home Drive, reserve it and slide to confirm. The pass shows the booking and how far the walk is.
3. Pick A Lot and stop on the review page. In the staff console, close A Lot for part of that period. Back on the review page, slide to confirm: the booking is refused with the reason, because F.5 rechecks the rules at booking time.
4. Open the Forest Home booking from My bookings and cancel it. The place goes back to the lot.

## Status

As of November 2026. Working means it runs in the product and has passing tests. Partial means it runs but something it depends on is still a stand-in. The OpsCon diagram in Innoslate (the Asset Diagram of 0 Universe) carries the same marks: green for working, orange for partial, gray for not yet built.

| Part | In the model | In the repository | State |
| --- | --- | --- | --- |
| Driver pages | X.C.1 Campus Driver, Driver Web Interface | `web/`, `api/main.py` | Working |
| C.1 Policy Manager | F.1 | `functions/f1_apply_parking_controls.py`, `web/admin.html` | Partial: rules are held in memory, and the staff check is the fixture account `admin01`, not a sign-in |
| C.2 Trip Validation Subsystem | F.2 | `functions/f2_validate_trip_eligibility.py` | Working |
| C.3 Location Data Subsystem | F.3 | `functions/f3_gather_lot_location_and_route_data.py` | Partial: lot locations and walking times come from fixture data |
| C.4 Option Selection Subsystem | F.4 | `functions/f4_present_eligible_parking_options.py` | Working |
| C.5 Reservation Subsystem | F.5, F.5.1 to F.5.4 | `functions/f5_*.py`, `functions/cancel_future_reservation.py`, `data/` | Working: SQLite records, the final place guarded in one write transaction, cancellation before the start |
| C.6 Confirmation Subsystem | F.6 | `functions/f6_provide_confirmation_and_route_guidance.py` | Working |
| C.7 Reporting Subsystem | F.7 | `functions/f7_report_reservations_and_affected_bookings.py` | Working: the staff console lists bookings a change affects |
| Campus Identity & Permit System | X.C.3 | `integrations/permit/` | Partial: fixture permits until Campus IT approves access |
| Campus Map & Navigation Service | X.C.4 | `integrations/map/` | Partial: fixture map data until the map owner approves access |
| Parking Administrator | X.C.2, Administrator Console Interface | `web/admin.html`, `/api/admin/*` | Partial: the console works, but with the fixture account and rules that reset on restart |
| AI parking help | candidate F.9, SR.17, SR.18 | none | Not yet built (ADR-0005) |

## What changed from the concept

- Reservations started in memory and disappeared on restart. They now live in SQLite, and the check for the last place and the save happen in one write transaction, so two drivers cannot get the same place (ADR-0004, ADR-0006, risk RK.1).
- Cancellation was in the specification as SR.6 but had no function in the model. We built it after TA feedback, and adding it to the model is the next model change.
- AI parking help is in the SPEC, but nothing in the model calls for it yet, so no model adapter was built (ADR-0005).

## What is left

- Keep approved rules in the database so staff changes survive a restart.
- Connect the permit and map clients to the real campus services once access is approved.
- Add cancellation and AI help (F.9) to the Innoslate model, then build the AI adapter from the SPEC response contract.
- Support dates. Every booking is for today for now.
- A real staff sign-in instead of the fixture account.
- Lab 13: the integration sequence as an action diagram, Project Task 8, and the integrated build (due December 7).

## Tests

```
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests --ignore=tests/test_spec_acceptance.py
```

157 tests pass, and GitHub Actions runs the same set in `.github/workflows/tests.yml` on every push. Tests are named by the requirement they check, for example `test_FR_1_4_1_5_...` for system requirement 1.4.1.5 and `test_SR_6_...` for cancellation.

`tests/test_spec_acceptance.py` holds the 20 Chapter 3 acceptance placeholders, one per acceptance case in `docs/SPEC.md`. They fail on purpose until real stakeholder or field evidence exists, and `chapter3-acceptance.yml` runs them separately so a red run there is expected. They do not claim the product passed field or user tests.

## Where to read more

| File | What it holds |
| --- | --- |
| `docs/SPEC.md` | Needs, stakeholder requirements, acceptance cases, data and AI response contracts |
| `docs/traceability.md` | Function to module to requirement to test |
| `docs/route-table.md` | Every route and the use case step it serves |
| `docs/deployment.md` | Subsystems, conduits and where each runs |
| `docs/reservation-subsystem-spec.md` | Chapter 9 specification of C.5 |
| `docs/adr/` | Architecture decisions |
| `docs/risks.md` | Product risk register |
| `docs/prompt-log.md`, `docs/deviation-log.md` | How AI-generated code was prompted and reviewed |

## Team

Hangting Zhu, Junjie Luo, Yixuan Zhu, Yuxin Wang
