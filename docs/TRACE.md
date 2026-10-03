# Tracing the code back to the model

Milestone Check 1 asks two things this file is meant to answer. Can a reviewer
follow one stakeholder need through a requirement to the use case and then to
the code that runs it. And is there any software in the repository that no
need, requirement or use case asks for.

IDs come from `docs/SPEC.md` and the Innoslate model: needs are N.x, stakeholder
requirements are SR.x, UC.1 steps are UC.1.1 to UC.1.10, acceptance criteria are
AC-Nx-SRy.

A word on what "covered" means here. Each row below can point at code and at a
developer test in `tests/test_skeleton.py`. That shows the skeleton behaves the
way its own code says. It does not mean the SR is met. Every acceptance test in
`tests/test_spec_acceptance.py` is still red, because each one needs reviewed
cases, real users or a field pilot that we haven't run.

## One need, all the way through

**N.2 Approved parking eligibility**, from the Campus Driver and University
Transportation / Parking Services: "I need parking choices and bookings that
follow the approved permit and time rules."

That need traces to **SR.2**: CampusPark shall confirm a reservation only when
the approved permit and time rules allow the driver to use the selected pool
for the full booked period.

In UC.1 this is two steps. **UC.1.2 and UC.1.3**, where CampusPark asks the
Campus Identity & Permit System for the driver's permit before showing
anything. And **UC.1.8**, where it checks again just before recording the
booking, because a permit or a rule can change in between.

In the code:

| Step | Code | What it does |
| --- | --- | --- |
| UC.1.2, UC.1.3 | `integrations/permit/client.py` `validate()` | Returns the permit profile, or nothing when the ID is blank or unknown |
| UC.1.6 | `api/eligibility.py` `eligible_lots()` | Keeps only lots whose permit list includes the driver's permit |
| UC.1.8 | `api/eligibility.py` `is_still_eligible()`, called from `api/main.py` `reserve()` | Runs the same check again at booking time |

Developer tests that exercise it: `test_student_gets_only_student_lots_nearest_first`,
`test_different_permits_get_different_lots`, `test_unconfirmed_identity_gets_no_options`,
`test_unconfirmed_identity_cannot_book`, `test_recheck_blocks_a_lot_the_permit_does_not_cover`.

Acceptance: **AC-N2-SR2 is red.** Its criterion is 100 cases reviewed by the
permit owner and the Parking Administrator, including periods that cross a rule
change. We have no reviewed cases and the skeleton has no time rules yet, only
permit types.

To see it run: start the app, look up parking as `student01`, then as
`visitor01`. The two get lots that don't overlap at all. Then try to reserve a
visitor lot while signed in as a student; the second check refuses it.

## Every need, and where it stands in code

| Need | SR | UC.1 step | Code today | Developer tests | Acceptance |
| --- | --- | --- | --- | --- | --- |
| N.1 Faster parking decisions | SR.1 | whole flow | The flow exists; no timing study | none | red, needs 40 matched driver tasks |
| N.1 | SR.3 | UC.1.6 | Walk times labelled as estimates, missing ones shown as unavailable, capacity basis stated | `test_unknown_destination_shows_walk_time_as_unavailable`, `test_lots_without_an_estimate_sort_after_lots_with_one`, `test_route_text_says_when_walk_time_is_missing` | red, needs 20 reviewed summaries and rule facts the skeleton doesn't have |
| N.2 Approved parking eligibility | SR.2 | UC.1.2, 1.3, 1.8 | Permit-type filter and recheck, unknown IDs refused | see above | red, needs owner-reviewed cases and time rules |
| N.3 Usable confirmed booking | SR.4 | UC.1.8 | Same-day interval overlap with peak counting | `test_overlapping_booking_is_refused_when_pool_is_full`, `test_back_to_back_bookings_do_not_overlap`, `test_capacity_counts_places_held_at_the_same_time_not_every_touching_booking`, `test_full_lot_drops_out_of_the_options` | red, needs dates, repeat-request IDs and 100 rounds of competing requests |
| N.3 | SR.5 | UC.1.9 | Confirmation shows lot, booked period and record limit | `test_reservation_returns_confirmation_with_booked_period` | red, conditions and staff contact are not approved data yet |
| N.3, N.12 | SR.7 | after UC.1.10 | none, this is an on-site pilot outcome | none | red, needs a field pilot |
| N.4 Future booking cancellation | SR.6 | not in UC.1 | none | none | red |
| N.5 Current parking controls | SR.8 | not in UC.1 | none | none | red |
| N.6 Affected booking review | SR.9 | not in UC.1 | none | none | red |
| N.7 Useful reservation records | SR.10 | not in UC.1 | none; `all_reservations()` exists but nothing exposes it | none | red |
| N.8 Unaided main flow | SR.11 | whole flow | none, needs a user study | none | red |
| N.9 Accessible main flow | SR.12 | whole flow | Native form controls and a polite live region for results; not reviewed | none | red, needs keyboard and screen-reader runs |
| N.10 Protected data and staff controls | SR.13, SR.14 | not in UC.1 | none | none | red |
| N.11 Clear source-failure limits | SR.15 | UC.1.3, 1.8 | Unknown identity can't get options or a booking; no timeout path | `test_unconfirmed_identity_cannot_book` | red, needs timeouts and capacity failures |
| N.11 | SR.16 | UC.1.9 | none | none | red |
| N.12 Pilot acceptance evidence | SR.1, SR.7 | whole flow | none, pilot evidence | none | red |
| N.13 Trusted AI parking help | SR.17, SR.18 | not in UC.1 | none; the Lab Manual puts this in Chapter 8 | none | red |

## Every piece of code, and what asks for it

The reverse direction: if something here had no row, it would be a capability
nobody asked for.

| Code | Asked for by |
| --- | --- |
| `api/main.py` `/api/options` | UC.1.1 to UC.1.6 |
| `api/main.py` `/api/reserve` | UC.1.7 to UC.1.9 |
| `api/main.py` `/api/destinations` | UC.1.1, so the form only offers destinations the map fixture knows |
| `api/main.py` request validation | UC.1.1 trip facts; the "end after start" rule in the SPEC's planned trip-input contract |
| `api/eligibility.py` | UC.1.6, UC.1.8; SR.2 |
| `api/ranking.py` | UC.1.6. The ordering itself is a placeholder; no SR sets a ranking rule yet |
| `api/reservations.py` | UC.1.8, UC.1.9; SR.4 |
| `api/reservations.py` `all_reservations()` | Nothing calls it from outside. It is kept for SR.10 later and for tests |
| `integrations/permit/client.py` | UC.1.2, UC.1.3; external system X.C.3 |
| `integrations/map/client.py` | UC.1.4, UC.1.5, UC.1.9; external system X.C.4 |
| `web/index.html` | UC.1.1, UC.1.7, UC.1.10; the driver side of UC.1 |

Nothing in the repository implements cancellation, administrator screens,
login, data export, payments, sensors or an AI model. Those either have SRs that
are still red with no code, or are out of scope in the BMA report.
