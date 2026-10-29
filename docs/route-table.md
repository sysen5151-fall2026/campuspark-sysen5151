# Entry points and the use cases they serve

Chapter 6 audit, brought up to date after the Chapter 8 wiring. Every route, endpoint or
user-triggered entry point in the repository, mapped to the use case it serves in the Innoslate
model (UC.1 Driver Finds and Reserves Campus Parking, UC.2 Maintain Parking Rules and Capacity).

## Entry points

| # | Entry point | Triggered by | Runs | Use case | Steps |
| --- | --- | --- | --- | --- | --- |
| 1 | `GET /` | Campus Driver opens CampusPark | serves `web/index.html` with the trip search | UC.1 | UC.1.1 |
| 1a | `GET /find` | the search on the home page | serves `web/find.html`: results list, map and lot details | UC.1 | UC.1.1 to UC.1.6 |
| 1b | `GET /review` | "Reserve a place here" | serves `web/review.html`: the booking checked before it is made | UC.1 | UC.1.7 |
| 1c | `GET /booking/{id}` | a confirmed booking, or a booking opened again | serves `web/booking.html`: confirmation and pass | UC.1 | UC.1.9, UC.1.10 |
| 1d | `GET /bookings` | "My bookings" | serves `web/bookings.html` | UC.1 | UC.1.10 |
| 2 | `GET /api/destinations` | page load of `web/index.html` | map fixture destination list | UC.1 | UC.1.1: the destination the driver chooses |
| 3 | `POST /api/options` | "Find parking" | F.2, X.F.3, F.3, X.F.4, F.4 | UC.1 | UC.1.1 to UC.1.6 |
| 4 | `POST /api/reserve` | "Reserve ..." | F.2, X.F.3, F.5, F.6 | UC.1 | UC.1.7 to UC.1.9 |
| 5 | `GET /api/reservations/{id}` | "Find my booking" | F.6 on a saved record, for its own driver only | UC.1 | UC.1.10: the driver reviews the confirmation |
| 5a | `GET /api/map` | page load of `web/index.html` | approximate map positions from the map fixture | UC.1 | UC.1.6: the options shown on the map, display only |
| 6 | `GET /admin` | Parking Administrator opens the staff console | serves `web/admin.html` | UC.2 | |
| 7 | `GET /api/admin/pools` | staff console load | IO.17 now in force | UC.2 | the administrator reviews current controls |
| 8 | `POST /api/admin/controls` | "Apply change" | F.1, then F.7 | UC.2 | change applied, acknowledged (IO.11), affected bookings reported (IO.12) |

Not entry points: `/static/` serves the stylesheet both pages load; `integrations/` is reached only
through rows 3 and 4; `tools/gen_stubs.py` is a developer tool.

## Orphans

None. Rows 5, 7 and 8 are new since the first audit. Row 5 was the closest call: it exists so a
driver can see a confirmation again, which is UC.1.10, and it answers only when the driver ID matches
the booking. A list of "all my bookings" was left out because no use case step asks for one.

## Use cases with no entry point

None. UC.2 was planned at the first audit and now has rows 6 to 8.

## Reconciling the counts

Two use cases in the model, thirteen entry points: ten on UC.1 (five pages and five data routes) and three on UC.2. Every function F.1 to
F.7 is reached from at least one route. The Chapter 2 helpers that duplicated the rules
(`api/eligibility.py`, `api/ranking.py`, `api/reservations.py`) were removed when the routes moved
onto `functions/`.
