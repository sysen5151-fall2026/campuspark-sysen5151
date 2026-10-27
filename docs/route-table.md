# Entry points and the use cases they serve

Chapter 6 audit. Every route, endpoint or user-triggered entry point in the repository, mapped to
the use case it serves in the Innoslate model (UC.1 Driver Finds and Reserves Campus Parking,
UC.2 Maintain Parking Rules and Capacity). The enumeration was read out of the code by the
assistant; the use-case column is the team's mapping against the model and is open for review in
the pull request.

## Entry points

| # | Entry point | Triggered by | Handler | Use case | Steps |
| --- | --- | --- | --- | --- | --- |
| 1 | `GET /` | Campus Driver opens CampusPark in a browser | `api/main.py` `home()` serves `web/index.html` | UC.1 | UC.1.1 (where the driver submits the trip) |
| 2 | `GET /api/destinations` | Page load of `web/index.html` | `api/main.py` `destinations()` | UC.1 | UC.1.1: fills the destination list the driver chooses from |
| 3 | `POST /api/options` | "Find parking" button | `api/main.py` `options()` | UC.1 | UC.1.1 to UC.1.6 |
| 4 | `POST /api/reserve` | "Reserve this one" button | `api/main.py` `reserve()` | UC.1 | UC.1.7 to UC.1.9 (UC.1.10 is the driver reading the result) |

Not entry points, and why: `integrations/permit/client.py` and `integrations/map/client.py` are
reached only through rows 3 and 4; the seven modules in `functions/` are not reached by any entry
point yet (see below); `tools/gen_stubs.py` is a developer tool that rewrites
`contracts/generated/` and is never run by a driver or administrator.

## Orphans

None. Each of the four entry points serves a step of UC.1. Row 2 was the closest call: it exists
only to fill a form field, but that field is the destination in UC.1.1, so it traces.

## Use cases with no entry point

| Use case | Status | Note |
| --- | --- | --- |
| UC.2 Maintain Parking Rules and Capacity | Planned | F.1 and F.7 have bodies and tests (1.4.1.1, 1.4.1.7) but no administrator route calls them. An administrator route needs the approved-account check from 2.1.4 in front of it, so it is added together with the deployment work in Chapter 8. |

## Reconciling the counts

The model has two use cases, UC.1 with ten steps and UC.2. The repository has four entry points,
all on UC.1, and none on UC.2. UC.1.10 has no entry point of its own because it is the driver
reading the confirmation that row 4 returns.

One finding is not about orphans but about duplication. The walking skeleton routes still call the
Chapter 2 helpers in `api/eligibility.py`, `api/ranking.py` and `api/reservations.py`, while the
model's functions now live in `functions/`. Both pass their own tests, but the same rules exist
twice. The routes move onto `functions/` as the Chapter 8 data access work replaces the stubs, and
the three helpers are removed then, not now, so the skeleton tests stay green between steps.
