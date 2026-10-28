# Component and deployment view

Chapter 8. What runs where and what talks to what, for the pilot. Built from the first-level
physical architecture in the Innoslate model: C.0 CampusPark Campus Parking & Reservation Platform
with seven subsystems, the four context conduits to the external systems, and the eleven internal
conduits of the first-level asset diagram.

## Deployment

One machine runs the whole pilot.

```
 Campus Driver's browser                       Pilot machine
 ┌────────────────────┐   HTTP (Driver Web    ┌──────────────────────────────────────────────┐
 │ web/index.html     │ ─ Interface conduit) ─▶│ uvicorn api.main:app  (one Python process)    │
 └────────────────────┘                        │   api/          routes, one per entry point   │
                                               │   functions/    F.1 to F.7, one module each   │
                                               │   data/         SQLite data access (C.5)      │
                                               │   integrations/ permit and map clients        │
                                               │        │                                      │
                                               │        ▼                                      │
                                               │   campuspark.db (SQLite file, not committed)  │
                                               └──────────────────────────────────────────────┘
 Campus Identity & Permit System (X.C.3)   reached through integrations/permit, fixture data today
 Campus Map & Navigation Service (X.C.4)   reached through integrations/map, fixture data today
```

Nothing leaves the machine. Both external systems are fixtures until Campus IT and the map owner
approve access (SPEC, data contract). There is no language model process; see ADR-0005.

## Subsystems and where they run

| Subsystem | Performs | Code | State it owns |
| --- | --- | --- | --- |
| C.1 Parking Control Subsystem | F.1 | `functions/f1_apply_parking_controls.py` | Approved rules and approved staff accounts (`RulesStore`, in memory) |
| C.2 Trip Validation Subsystem | F.2 | `functions/f2_validate_trip_eligibility.py` | none |
| C.3 Location Data Subsystem | F.3 | `functions/f3_gather_lot_location_and_route_data.py`, `integrations/map/client.py` | none |
| C.4 Option Selection Subsystem | F.4 | `functions/f4_present_eligible_parking_options.py` | none |
| C.5 Reservation Subsystem | F.5 | `functions/f5_recheck_and_record_reservation.py`, `data/reservation_db.py`, `data/schema.sql` | Saved reservations (SQLite) |
| C.6 Confirmation Subsystem | F.6 | `functions/f6_provide_confirmation_and_route_guidance.py` | none |
| C.7 Reporting Subsystem | F.7 | `functions/f7_report_reservations_and_affected_bookings.py` | none |

C.5 is decomposed in Chapter 9 into C.5.1 to C.5.4. The first of those built from its specification
is C.5.3 Capacity Ledger (`functions/f5_3_commit_capacity_hold.py`).

## Conduits and how each is carried

| Conduit | Transfers | Carried by |
| --- | --- | --- |
| Driver Web Interface | IO.1, IO.6, IO.7, IO.9, IO.13 | HTTP routes in `api/main.py` (`docs/route-table.md`) |
| Administrator Console Interface | IO.10, IO.11, IO.12 | `web/admin.html` and `/api/admin/*` routes |
| Permit Eligibility Data Link | IO.2, IO.3 | `integrations/permit/client.validate()` |
| Map and Route Data Link | IO.4, IO.5 | `integrations/map/client.py` |
| The eleven internal conduits | IO.8, IO.14 to IO.19 | in-process function calls, in the shapes of `contracts/api-v1.yaml` |

Because every internal conduit is a function call inside one process, the 60 s rule-change budget
(2.1.5) and the 5 s booking budget (2.1.8) are spent almost entirely on the external links and the
database, not on the conduits.

## Data source and model

| Interface | In the model | In the repository |
| --- | --- | --- |
| Saved reservations | C.5, IO.8 and IO.18 | `data/reservation_db.py` behind the same interface as the in-memory store; table limited to the RS.2.1 fields; `tests/test_data_access.py` |
| Permit and map sources | X.C.3, X.C.4 and their data links | fixtures; replaced when owners approve access |
| Language model | no function, no asset, no interface (AI help is candidate F.9) | not built; ADR-0005 |

## Where this stands

- The routes run the functions in `functions/` through `api/service.py`, in the order of each use
  case (`docs/route-table.md`). Saved reservations are in `data/campuspark.db` and survive a restart;
  set `CAMPUSPARK_DB` to use another file.
- The approved rules (C.1) are still held in memory, so a change made in the staff console lasts
  until the server restarts. Persisting them is the next data access step.
- F.5 checks capacity and then saves. `api/service.py` serializes bookings with one lock so the two
  steps cannot interleave between requests; C.5.3 Capacity Ledger, which does both in one step
  (RS.1.4.3, RS.2.5), is built and tested but not yet on the booking path.
- The staff check is the fixture account `admin01`, not a sign-in. Real staff accounts come from
  Campus IT (2.1.4).
