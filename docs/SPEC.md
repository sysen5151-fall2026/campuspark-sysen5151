# CampusPark specification

SYSEN 5151, Team 25 — Chapter 3, Section 3.5

## Source and review status

This file is the build's source for later prompts. Keep the canonical file at `docs/SPEC.md`; do not create a second specification at the repository root.

The Chapter 3 source is the saved CampusPark model and report: `N.1–N.13`, `SR.1–SR.18`, and 20 need-to-requirement links. The system is `C.0 CampusPark`. Reuse `X.C.1 Campus Driver`, `X.C.2 Parking Administrator`, `X.C.3 Campus Identity & Permit System`, and `X.C.4 Campus Map & Navigation Service`. The two other major stakeholder roles are `S.3 University Transportation / Parking Services` and `S.4 Campus IT / System Support`.

The user asked the assistant to reuse the current proposed needs, requirements, MOEs, and validation criteria in this file. These statements remain proposed for team and stakeholder review. This work does not claim that interviews, team adoption, owner approval, live source access, field tests, or passed acceptance tests took place. The named red tests are Chapter 3 placeholders, as shown in the Lab Manual. A red placeholder records an unmet acceptance criterion; it does not show that the running service was tested against that criterion.

The original specification covered the UC.1 success path and cited the imported ORD 5.x labels. The path and component links below keep that record. The new acceptance criteria use the current N and SR identifiers. Check older ORD labels in the model before using them as authority for new work.

### Target changes for review

| Source | Earlier target or limit | Current Chapter 3 proposal | Review needed |
| --- | --- | --- | --- |
| Previous repository specification | Parking search time reduced by at least 20% | SR.1: at least 30% lower median time to choose an eligible option; 40 matched driver tasks; no increase in wrong or unfinished task rates | The threshold and task definition differ. The team and owner must confirm the current proposed target. |
| Previous repository specification | At least 90% of displayed recommendations usable by the driver | SR.2: all 100 owner-reviewed eligibility cases pass, including blocked and unknown cases | A case-based rule check is not the same measure as sampled recommendation accuracy. The team must decide whether the older measure is kept separately or retired. No extra requirement or test is claimed here. |
| Previous success-path specification | Cancellations, outages, and administrative rule changes not yet specified or built | SR.6, SR.8–SR.10, and SR.14–SR.16 now set proposed outcomes and checks | The specification now describes these outcomes; the current application still lacks these complete paths. Approved staff record updates do not let CampusPark change university permit rights. |

Use the current proposed SR wording below for this Chapter 3 draft. Keep these source differences visible until the team resolves them. Do not describe a target change as approved.

## Scope and current build

CampusPark helps a driver choose a valid lot and request a place in an approved pool for a stated period. A confirmation does not create a permit or promise a specific marked bay. A live pool and staff duties still need Parking Services approval.

The current code is a walking skeleton for `UC.1 Driver Finds and Reserves Campus Parking`. It uses permit and map fixtures. Bookings live in memory and vanish on restart. It has no sensors, cameras, plate readers, gates, payments, or parking enforcement. It does not change university permit policy.

The skeleton filters by permit type, ranks by walk time and then remaining recorded capacity, and rechecks at booking. Bookings are same-day half-open intervals in minutes, and remaining capacity is the configured places minus the most bookings held at any one moment in the requested period. It does not yet handle dates, repeat-request IDs, cancellations, administrative updates, outage recovery, or AI replies. It does not prove the proposed driver, access, data-protection, or field-pilot outcomes.

### Existing UC.1 path

| Step | What happens | Existing source link |
| --- | --- | --- |
| 1 | Driver submits identity, destination, arrival time, and parking duration | UC.1.1; ORD 5.1.1.1 and 5.1.1.3 |
| 2 | CampusPark requests identity and permit validation | UC.1.2; ORD 5.1.2.2 |
| 3 | The permit system returns identity and permit eligibility | UC.1.3; ORD 5.1.1.2 |
| 4 | CampusPark requests lot locations and routes | UC.1.4; ORD 5.1.2.4 |
| 5 | The map service returns locations and routes | UC.1.5; ORD 5.1.1.4 |
| 6 | CampusPark applies rules, permit limits, location, and capacity, then shows eligible options | UC.1.6; ORD 5.1.4.2 and 5.1.4.3 |
| 7 | The driver chooses an option and requests a reservation | UC.1.7 |
| 8 | CampusPark rechecks eligibility and capacity, then records the reservation | UC.1.8; ORD 5.1.4.4 |
| 9 | CampusPark returns confirmation and guidance | UC.1.9; ORD 5.1.2.5 and 5.1.2.16 |
| 10 | The driver reviews confirmation and guidance | UC.1.10 |

Step 8 repeats the checks because conditions can change after a search. The current model clarifies full-period capacity and repeat-request behavior. The skeleton now counts overlapping same-day bookings over the full requested period, but it still has no dates, repeat-request IDs, or competing-request handling, so it does not implement that full outcome.

### Existing components

| Component | Current duty and source | Open work |
| --- | --- | --- |
| `api/eligibility.py` | Filters lots by permit type and repeats the same check before booking; UC.1.2 and UC.1.8; ORD 5.1.4.1 and 5.1.1.2 | Approved time rules and unavailable eligibility cases under SR.2 and SR.15 |
| `api/ranking.py` | Orders permitted lots by fixture walk time, then remaining capacity; lots with no walk estimate go last; UC.1.6 | The order is a placeholder. No new ranking weight is approved by this specification. SR.1 and SR.3 measure the result and explanation. |
| `api/reservations.py` | Holds a record in memory and reports remaining capacity as configured places minus the peak number held during the requested same-day period; UC.1.8 and UC.1.9; ORD 5.1.2.6 | Dates, competing requests, repeat IDs, cancellation, complete confirmation, and record summaries |
| `integrations/permit/client.py` | Reads a permit fixture; returns no profile for a blank or unknown ID; it does not write to X.C.3 | Live source access, complete rule fields, and agreed failure meanings |
| `integrations/map/client.py` | Reads lot fixtures and makes a route sentence; returns no walk estimate for an unlisted destination; it does not write to X.C.4 | Approved lot addresses, route records, source age, and route-only failure |
| `web/` | Shows the trip form, option list with estimates and capacity basis labelled, and confirmation with the booked period | Complete required fields, remaining failure messages, and keyboard and screen-reader review |

## Needs and Acceptance Criteria

Each need below has its existing statement, stakeholder, linked requirements, and preliminary MOEs. Each saved trace pair has one acceptance ID and one named red test. This gives 20 acceptance cases for 13 needs and 18 requirements. SR.1 and SR.7 each support two needs; their criteria are repeated to show those links. A later validation record can be shared across both links rather than counted as two independent studies.

The acceptance text and MOEs are copied from the current Chapter 3 draft. New case counts and retained M1–M6 targets stay proposed. Tests for SR.1, SR.7, SR.11, and SR.12 will need observed human or field evidence as specified. A software placeholder or simulation cannot establish those outcomes.

### N.1 — Faster parking decisions

Need statement: I need to find a valid parking option for my trip with less effort than the current process.

Stakeholder: Campus Driver

Traces to: SR.1, SR.3.

Preliminary MOEs for this need:

- SR.1: M1: at least 30% lower median decision time; wrong and unfinished task rates do not increase.
- SR.3: Proposed: all 20 reviewed option summaries match the approved test data.

#### AC-N1-SR1

Requirement: SR.1 — Faster correct parking choice

Requirement statement: CampusPark shall reduce the median time to choose an eligible parking option by at least 30% compared with the current process.

Preliminary MOE: M1: at least 30% lower median decision time; wrong and unfinished task rates do not increase.

Acceptance criterion: Use 40 drivers and matched trips under the same rules and similar demand. Half use current tools first; half use CampusPark first. Measure elapsed time to a correct choice. Compute 100 × (baseline median − CampusPark median) / baseline median. Pass at 30% or more, with no increase in wrong or unfinished task rates. Report sample limits and subgroup counts.

Named red test: `test_N1_SR1_faster_correct_parking_choice` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M1 target from Chapter 1.

#### AC-N1-SR3

Requirement: SR.3 — Clear parking options

Requirement statement: CampusPark shall show the rule and trip facts used to select each parking option shown to the driver.

Preliminary MOE: Proposed: all 20 reviewed option summaries match the approved test data.

Acceptance criterion: Prepare 20 trips with varied permits, destinations, time limits, and missing route or estimate data. Compare each shown summary with the test record. Pass if each available fact matches its source, each missing fact is marked unavailable, and each estimate is marked as an estimate. Do not treat estimated availability as guaranteed capacity.

Named red test: `test_N1_SR3_clear_parking_options` in `tests/test_spec_acceptance.py`.

Target source: New proposed check based on UC.1 step 6 and proposal recommendation feature.

### N.2 — Approved parking eligibility

Need statement: I need parking choices and bookings that follow the approved permit and time rules.

Stakeholder: Campus Driver; University Transportation / Parking Services

Traces to: SR.2.

Preliminary MOEs for this need:

- SR.2: M2: all 100 approved eligibility cases pass.

#### AC-N2-SR2

Requirement: SR.2 — Approved parking eligibility

Requirement statement: CampusPark shall confirm a reservation only when the approved permit and time rules allow the driver to use the selected pool for the full booked period.

Preliminary MOE: M2: all 100 approved eligibility cases pass.

Acceptance criterion: The permit owner and Parking Administrator review 100 cases: 60 eligible and 40 blocked or unknown. Cover permit type, allowed lot, start time, end time, and a period that crosses a rule change. Pass only if all eligible cases receive the expected eligibility result and all blocked or unknown cases cannot receive a confirmed booking.

Named red test: `test_N2_SR2_approved_parking_eligibility` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M2 target from Chapter 1.

### N.3 — Usable confirmed booking

Need statement: I need a confirmed booking that is backed by an approved pool and states what I can use and when.

Stakeholder: Campus Driver; Parking Administrator; University Transportation / Parking Services

Traces to: SR.4, SR.5, SR.7.

Preliminary MOEs for this need:

- SR.4: M3: exactly one success in each of 100 rounds of 100 eligible requests for one remaining place; zero overbooked intervals.
- SR.5: Proposed: all 20 tested confirmations contain the required fields and match the saved booking.
- SR.7: M6: at least 95% successful on-time arrivals among at least 40 confirmed arrivals.

#### AC-N3-SR4

Requirement: SR.4 — Capacity-safe bookings

Requirement statement: CampusPark shall confirm a new reservation only when the approved pool has capacity for the full booked period.

Preliminary MOE: M3: exactly one success in each of 100 rounds of 100 eligible requests for one remaining place; zero overbooked intervals.

Acceptance criterion: Run 100 rounds with 100 eligible requests competing for one remaining place in the same period. Reset the pool between rounds. Pass if exactly one request is confirmed in every round and the count never exceeds capacity. Also check partial overlaps, repeated request IDs, and cancellation followed by a new request. Repeated IDs must return the existing result without adding another booking.

Named red test: `test_N3_SR4_capacity_safe_bookings` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M3 target from Chapter 1.

#### AC-N3-SR5

Requirement: SR.5 — Clear booking confirmation

Requirement statement: CampusPark shall provide a confirmation record for each confirmed reservation.

Preliminary MOE: Proposed: all 20 tested confirmations contain the required fields and match the saved booking.

Acceptance criterion: Create 20 eligible bookings with varied pools and times. Compare the displayed record with the saved booking and approved pool terms. Pass if all fields are present, correct, and consistent, and the pool-place limit is shown. A failed or blocked request must not be shown as confirmed.

Named red test: `test_N3_SR5_clear_booking_confirmation` in `tests/test_spec_acceptance.py`.

Target source: New proposed count; content retained from Chapter 1 UC.1 steps 9–10.

#### AC-N3-SR7

Requirement: SR.7 — Usable booked pool on arrival

Requirement statement: The CampusPark pilot shall provide a usable place in the approved pool to at least 95% of on-time drivers with confirmed bookings.

Preliminary MOE: M6: at least 95% successful on-time arrivals among at least 40 confirmed arrivals.

Acceptance criterion: Run an owner-approved field pilot with at least 40 confirmed arrivals in the stated window. Staff record whether each driver can use a place in the booked pool. Divide successful arrivals by all confirmed arrivals in the window. Pass at 95% or more. With 40 arrivals, at least 38 must succeed. Report late arrivals, no-shows, causes of failures, and sample limits separately. Simulation cannot establish this field result.

Named red test: `test_N3_SR7_usable_booked_pool_on_arrival` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M6 target from Chapter 1.

### N.4 — Future booking cancellation

Need statement: I need to cancel a future booking so its place can be used by someone else.

Stakeholder: Campus Driver; Parking Administrator

Traces to: SR.6.

Preliminary MOEs for this need:

- SR.6: Proposed: all 20 future-cancellation cases release exactly the capacity held by the cancelled booking.

#### AC-N4-SR6

Requirement: SR.6 — Future booking cancellation

Requirement statement: CampusPark shall release the capacity held by a future reservation when the driver cancels that reservation.

Preliminary MOE: Proposed: all 20 future-cancellation cases release exactly the capacity held by the cancelled booking.

Acceptance criterion: Run 20 cases with varied future start times and partial overlaps. Record capacity before booking, after booking, and after cancellation. Pass if the booking becomes cancelled, the held capacity is released for its whole period, and a repeated cancellation causes no further release. Test an already-started booking separately under the owner-reviewed operating rule; it is outside this future-booking requirement.

Named red test: `test_N4_SR6_future_booking_cancellation` in `tests/test_spec_acceptance.py`.

Target source: New proposed count; cancellation behavior retained from Chapter 1.

### N.5 — Current parking controls

Need statement: I need approved rule, capacity, and closure changes to take effect before the service makes new promises.

Stakeholder: Parking Administrator; University Transportation / Parking Services

Traces to: SR.8.

Preliminary MOEs for this need:

- SR.8: M5: all 20 approved changes apply within 60 seconds.

#### AC-N5-SR8

Requirement: SR.8 — Current approved parking controls

Requirement statement: CampusPark shall apply an approved parking-control change within 60 seconds after the Parking Administrator saves it.

Preliminary MOE: M5: all 20 approved changes apply within 60 seconds.

Acceptance criterion: Time 20 saved changes, including rules, capacity reductions, and closures. Record the save time and the time each change governs new search and confirmation results. Pass if all changes take effect within 60 seconds and every closed pool blocks new bookings for the affected period. Use SR.9 to check affected existing bookings.

Named red test: `test_N5_SR8_current_approved_parking_controls` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M5 target from Chapter 1.

### N.6 — Affected booking review

Need statement: I need to find bookings affected by a closure or a capacity reduction so staff can resolve them.

Stakeholder: Parking Administrator

Traces to: SR.9.

Preliminary MOEs for this need:

- SR.9: M5 supporting check: no missing affected booking in the 20 change cases; every flag appears within 60 seconds.

#### AC-N6-SR9

Requirement: SR.9 — Affected booking list

Requirement statement: CampusPark shall identify every reservation affected by an approved closure or capacity reduction within 60 seconds after the change is saved.

Preliminary MOE: M5 supporting check: no missing affected booking in the 20 change cases; every flag appears within 60 seconds.

Acceptance criterion: Use the 20 SR.8 changes with a known set of confirmed and cancelled reservations. Before each change, calculate the affected confirmed reservation IDs using the overlap rules in this requirement. Compare the saved staff list with that reference set. Pass if every affected ID is flagged within 60 seconds with the correct reason, no unrelated booking is flagged, and no booking is automatically cancelled by the flag. Record staff resolution separately.

Named red test: `test_N6_SR9_affected_booking_list` in `tests/test_spec_acceptance.py`.

Target source: Retained M5 timing; detailed list comparison is proposed.

### N.7 — Useful reservation records

Need statement: I need a reservation summary that supports staff work and shows what the record can and cannot tell us.

Stakeholder: Parking Administrator; University Transportation / Parking Services

Traces to: SR.10.

Preliminary MOEs for this need:

- SR.10: Proposed: all counts match the reference record in 10 test summaries; every estimate has a source and time basis.

#### AC-N7-SR10

Requirement: SR.10 — Correct reservation summary

Requirement statement: CampusPark shall provide the Parking Administrator with a reservation summary for a selected pool and time period.

Preliminary MOE: Proposed: all counts match the reference record in 10 test summaries; every estimate has a source and time basis.

Acceptance criterion: Load 10 known booking-record sets with varied pools, booked periods, cancelled bookings, and estimates. Include periods that partly overlap a window and periods that touch only its start or end. Count each unique reservation ID once in its current confirmed or cancelled status. Generate the summaries and compare them with the reference counts. Pass if all counts match, each estimate has a source and time basis, and no booking count is described as live measured occupancy.

Named red test: `test_N7_SR10_correct_reservation_summary` in `tests/test_spec_acceptance.py`.

Target source: New proposed check based on original proposal and Chapter 1 no-sensor limit.

### N.8 — Unaided main flow

Need statement: I need to complete the parking search and booking flow without help.

Stakeholder: Campus Driver

Traces to: SR.11.

Preliminary MOEs for this need:

- SR.11: M4: at least 36 of 40 users finish the main flow without help.

#### AC-N8-SR11

Requirement: SR.11 — Unaided main-flow completion

Requirement statement: CampusPark shall allow at least 90% of a 40-user test group to complete the main parking search and booking flow without help.

Preliminary MOE: M4: at least 36 of 40 users finish the main flow without help.

Acceptance criterion: Observe 40 users drawn from students, faculty and staff, and visitors, including users with access needs. Give each a matched valid trip task. Help means a tester gives task steps or operates controls for the user. Pass if at least 36 finish without help. Report group counts, errors, and unfinished steps. Run SR.12 access checks separately.

Named red test: `test_N8_SR11_unaided_main_flow_completion` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M4 target from Chapter 1.

### N.9 — Accessible main flow

Need statement: I need to use the main parking flow with keyboard or screen-reader controls.

Stakeholder: Campus Driver; University Transportation / Parking Services

Traces to: SR.12.

Preliminary MOEs for this need:

- SR.12: M4 access check: zero blocking issues in the reviewed keyboard and screen-reader tasks.

#### AC-N9-SR12

Requirement: SR.12 — Accessible main-flow controls

Requirement statement: CampusPark shall allow the main parking search and booking flow to be completed in both keyboard-only and screen-reader modes.

Preliminary MOE: M4 access check: zero blocking issues in the reviewed keyboard and screen-reader tasks.

Acceptance criterion: Have users or access reviewers run the normal valid trip once with keyboard-only controls and once with the owner-selected screen reader and browser. Cover all main-flow controls and messages. Pass only when each required task can be completed and every blocking issue found in the review is fixed and retested. Record the tools used and limits of the review. This is not a claim of full standards certification.

Named red test: `test_N9_SR12_accessible_main_flow_controls` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M4 keyboard/screen-reader no-blocker check.

### N.10 — Protected data and staff controls

Need statement: I need the service to use only needed personal data and to limit parking-control changes to approved staff.

Stakeholder: Campus IT / System Support; Campus Driver

Traces to: SR.13, SR.14.

Preliminary MOEs for this need:

- SR.13: Proposed: zero unapproved personal-data fields in stored records, logs, and exported reports.
- SR.14: Proposed: all 20 allowed or blocked staff-access cases produce the approved result.

#### AC-N10-SR13

Requirement: SR.13 — Limited personal data

Requirement statement: CampusPark shall keep only the personal-data fields approved by Campus IT for the parking task.

Preliminary MOE: Proposed: zero unapproved personal-data fields in stored records, logs, and exported reports.

Acceptance criterion: Use the proposed closed field list as the draft reference. Send test inputs that include extra personal fields. Inspect stored records, access logs, and exported reports after search, booking, cancellation, and failure cases. Pass the draft field check if no field outside the listed record schemas is retained and no password or card detail is retained. Repeat against the IT-approved list before live acceptance. A live pass also requires the approved retention rule; its duration is still an open owner decision.

Named red test: `test_N10_SR13_limited_personal_data` in `tests/test_spec_acceptance.py`.

Target source: New proposed check based on Chapter 1 C4.

#### AC-N10-SR14

Requirement: SR.14 — Approved staff changes

Requirement statement: CampusPark shall allow only approved Parking Administrator accounts to change parking controls.

Preliminary MOE: Proposed: all 20 allowed or blocked staff-access cases produce the approved result.

Acceptance criterion: Prepare 20 access cases that include an approved administrator, a driver account, an unapproved staff account, and a signed-out request. Attempt a rule, capacity, or closure change. Pass if approved accounts can make the allowed change and all other cases leave the control unchanged. Check both the displayed result and the saved record.

Named red test: `test_N10_SR14_approved_staff_changes` in `tests/test_spec_acceptance.py`.

Target source: New proposed check based on Chapter 1 staff role and IT access review.

### N.11 — Clear source-failure limits

Need statement: I need a source failure to leave me with a clear result and no unsupported booking.

Stakeholder: Campus Driver; Campus IT / System Support

Traces to: SR.15, SR.16.

Preliminary MOEs for this need:

- SR.15: Proposed: zero confirmed bookings in 20 required-data failure cases.
- SR.16: Proposed: all 10 route-only failure cases retain the correct booking status.

#### AC-N11-SR15

Requirement: SR.15 — No booking from unavailable required data

Requirement statement: CampusPark shall block reservation confirmation when required eligibility or capacity data are unavailable.

Preliminary MOE: Proposed: zero confirmed bookings in 20 required-data failure cases.

Acceptance criterion: Run 20 cases covering identity or permit timeouts, unknown rights, missing approved pool capacity, invalid capacity, and missing or failed confirmed-booking records for the requested period. Pass if none creates a confirmed reservation and each gives a clear status message. Recheck normal bookings after valid required data returns. Route-guidance-only failure is tested separately under SR.16.

Named red test: `test_N11_SR15_no_booking_from_unavailable_required_data` in `tests/test_spec_acceptance.py`.

Target source: New proposed count; failure behavior retained from Chapter 1.

#### AC-N11-SR16

Requirement: SR.16 — Booking retained after route failure

Requirement statement: CampusPark shall retain a valid confirmed reservation when route guidance alone is unavailable.

Preliminary MOE: Proposed: all 10 route-only failure cases retain the correct booking status.

Acceptance criterion: Create 10 valid confirmed bookings and make X.C.4 unavailable for route guidance. Keep permit, lot address, and capacity records valid. Pass if each booking remains confirmed and its terms are unchanged, while the shown guidance is replaced by the lot address and warning. Test required-data failure separately under SR.15.

Named red test: `test_N11_SR16_booking_retained_after_route_failure` in `tests/test_spec_acceptance.py`.

Target source: New proposed count; behavior retained from Chapter 1.

### N.12 — Pilot acceptance evidence

Need statement: I need clear evidence that the pilot improves driver decisions and supports usable bookings before wider use.

Stakeholder: University Transportation / Parking Services

Traces to: SR.1, SR.7.

Preliminary MOEs for this need:

- SR.1: M1: at least 30% lower median decision time; wrong and unfinished task rates do not increase.
- SR.7: M6: at least 95% successful on-time arrivals among at least 40 confirmed arrivals.

#### AC-N12-SR1

Requirement: SR.1 — Faster correct parking choice

Requirement statement: CampusPark shall reduce the median time to choose an eligible parking option by at least 30% compared with the current process.

Preliminary MOE: M1: at least 30% lower median decision time; wrong and unfinished task rates do not increase.

Acceptance criterion: Use 40 drivers and matched trips under the same rules and similar demand. Half use current tools first; half use CampusPark first. Measure elapsed time to a correct choice. Compute 100 × (baseline median − CampusPark median) / baseline median. Pass at 30% or more, with no increase in wrong or unfinished task rates. Report sample limits and subgroup counts.

Named red test: `test_N12_SR1_faster_correct_parking_choice` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M1 target from Chapter 1.

#### AC-N12-SR7

Requirement: SR.7 — Usable booked pool on arrival

Requirement statement: The CampusPark pilot shall provide a usable place in the approved pool to at least 95% of on-time drivers with confirmed bookings.

Preliminary MOE: M6: at least 95% successful on-time arrivals among at least 40 confirmed arrivals.

Acceptance criterion: Run an owner-approved field pilot with at least 40 confirmed arrivals in the stated window. Staff record whether each driver can use a place in the booked pool. Divide successful arrivals by all confirmed arrivals in the window. Pass at 95% or more. With 40 arrivals, at least 38 must succeed. Report late arrivals, no-shows, causes of failures, and sample limits separately. Simulation cannot establish this field result.

Named red test: `test_N12_SR7_usable_booked_pool_on_arrival` in `tests/test_spec_acceptance.py`.

Target source: Retained proposed M6 target from Chapter 1.

### N.13 — Trusted AI parking help

Need statement: I need AI parking help that follows approved parking data and stays useful when the AI reply fails.

Stakeholder: Campus Driver; Campus IT / System Support

Traces to: SR.17, SR.18.

Preliminary MOEs for this need:

- SR.17: Proposed: all 20 reviewed answers agree with the supplied record and add zero unsupported parking facts.
- SR.18: Proposed: all 10 missing or malformed reply cases produce the correct fallback.

#### AC-N13-SR17

Requirement: SR.17 — Data-based AI parking help

Requirement statement: CampusPark shall base each AI parking answer on the approved parking data supplied for the user's request.

Preliminary MOE: Proposed: all 20 reviewed answers agree with the supplied record and add zero unsupported parking facts.

Acceptance criterion: Review 20 test requests against fixed approved records, including valid choices, closures, unknown rights, and missing data. List the supported facts before the test. Pass if every stated parking fact matches that list, no answer grants new rights or capacity, and missing information is described as unavailable. Repeat after a model or prompt change.

Named red test: `test_N13_SR17_data_based_ai_parking_help` in `tests/test_spec_acceptance.py`.

Target source: New proposed check based on original proposal AI feature.

#### AC-N13-SR18

Requirement: SR.18 — AI reply fallback

Requirement statement: CampusPark shall provide a fixed message built from the approved parking record when an AI reply is missing or fails the approved response format.

Preliminary MOE: Proposed: all 10 missing or malformed reply cases produce the correct fallback.

Acceptance criterion: Inject 10 missing or malformed replies: empty reply, invalid JSON, missing message, wrong field type, or blank message. Compare the shown fallback with the approved parking record. Pass if all cases show the fixed source-based message and no raw reply or internal error. If the record itself is unavailable, show the fixed unavailable message and apply SR.15 to any booking request.

Named red test: `test_N13_SR18_ai_reply_fallback` in `tests/test_spec_acceptance.py`.

Target source: New proposed check based on proposal AI feature and Chapter 3 fallback example.

## Data Contract

### Current skeleton: source and shape

This section describes the checked repository code. The types below describe its current records. They are not a claim that live source owners have agreed to the schema.

| Source and call | Fields and types | Units and current values | Refresh cadence |
| --- | --- | --- | --- |
| Driver request: `OptionsRequest` in `api/main.py` | `driver_id`: string; `destination`: string; `arrival`: string matching 24-hour `HH:MM`; `hours`: integer, at least 1. All four are required. | Identity reference; destination label; arrival clock time on an undated day; duration in hours | Submitted on every options or reservation request |
| Reservation request: `ReserveRequest` | All `OptionsRequest` fields plus `lot_id`: string | Fixture lot identifier | Submitted for each booking attempt |
| Permit fixture: `permit_client.validate(driver_id)` | `driver_id`: string; `name`: string; `permit`: string | Identity reference; sample display name; permit value `student`, `staff`, or `visitor` | Read at each options request and again at each reservation request; fixtures change only when their file changes |
| Map fixture: `map_client.LOTS` | `id`: string; `name`: string; `permits`: list of strings; `capacity`: integer; `walk_minutes`: object from destination string to integer | Lot ID and label; allowed permit types; places; estimated walk minutes | Read at each options and reservation request; fixtures change only when their file changes |
| Candidate map view: `lots_near(destination)` | Same lot fields; `walk_minutes` becomes one integer, or null when the fixture has no estimate for that destination | Estimated minutes for that destination | Built again on each call |
| Destination list: `/api/destinations` | `destinations`: list of strings | `Duffield Hall`, `Statler Hotel`, `Vet School` | Loaded by the page on opening |
| Internal booking record: `api/reservations.py` | `id`, `driver_id`, `lot_id`, `lot_name`, `destination`, `start`, `end`: strings; `start_min`, `end_min`: integers | `id` is an 8-character UUID prefix; `start_min` and `end_min` are minutes since midnight forming a half-open interval; `start` and `end` are clock labels, with `next day` added past midnight | Added on a successful booking; kept only in process memory |
| Ranking output: `ranking.rank(...)` | Candidate lot fields plus `remaining`: integer | Configured places minus the peak number of bookings held at one moment in the requested period for the same lot | Recomputed during each options request and booking check |
| Options response: `/api/options` | `permit`, `start`, `end`, `capacity_basis`: strings; `options`: list of objects with `lot_id`, `name`: strings, `walk_minutes`: integer or null, `remaining`, `capacity`: integers | Lot label, estimated walk minutes or null, remaining recorded places out of configured places, and a fixed note that places come from booking records | Returned for each request |
| Reservation response: `/api/reserve` | `confirmation`, `lot`, `start`, `end`, `guidance`, `note`: strings | Record ID, lot name, booked period, fixture route sentence, and record-limit note | Returned after each successful booking |
| Error response from the explicit failure branches | `error`: string | A fixed user message | Returned when the current code finds a blank or unknown driver, an absent lot, a denied permit, or a pool with no place left for the whole period |
| Validation response from FastAPI | `detail`: list | Pydantic field errors, HTTP 422 | Returned when a required field is missing, `arrival` is not `HH:MM`, or `hours` is below 1 |

The API request fields have no defaults. The web form uses a time picker and sets a minimum of one hour; neither the form nor the API sets an upper limit, because no limit has been approved. The API checks the clock format and that the stay ends after it starts; it does not check a date, time zone, or rule period. Do not treat the current checks or the lack of an upper limit as approved requirements.

### Current null, missing-value, and failure behavior

- The permit fixture returns `None` for a blank, whitespace-only, or unknown ID, and the API then returns a fixed error with no options and no booking. An earlier version gave a blank ID the student profile; that was removed because it handed out rights the permit source had not confirmed. This is not yet the full SR.15 outcome, which also covers timeouts and missing capacity.
- An unlisted destination gets `walk_minutes: null`. The page shows "walk time unavailable", ranks those lots after lots with an estimate, and labels every walk time it does show as an estimate. An earlier version filled in 15 minutes. These labels are a start on SR.3, not a reviewed summary.
- The current fixture functions have no live timeout path or source-status record. Missing required lot or profile dictionary keys can raise an error. Missing or malformed request fields get an HTTP 422 from FastAPI; the page turns that into a short form message, and any other non-200 response into a message that nothing was booked.
- The booking store has no unavailable-source signal, stored status, or repeat-request ID. A restart clears it. `all_reservations()` returns a copy of the list. It is not a physical occupancy source.
- Route guidance is a string built from the lot label and fixture walk minutes, and says so when no walk time is known. No route-only outage branch exists. A route error after saving a booking is not yet handled as SR.16 requires.
- The permit fixture has a sample `name`; the current API does not return it. The booking store still keeps `lot_name` and `destination` in addition to other fields. These current records are not proof of the proposed closed stored-data list under SR.13.

### Planned contract needed for the stakeholder requirements

The following fields and rules state the next contract work. They do not claim that the current skeleton implements them. Field names, formats, source agreements, and the live retention rule still need team and owner review. Keep the outcome in the cited SR unchanged when deciding the final field shape.

| Planned record or view | Fields and proposed types | Units, meaning, and source | Basis |
| --- | --- | --- | --- |
| Trip input | Identity reference: string; permit result: approved result record; destination: string; arrival and end times: date-time values | Identity from X.C.3; trip from the driver. End must be after start. The campus time zone and exact date-time format remain open owner decisions. | SR.2, SR.13 |
| Approved eligibility | Identity result and permit result; permitted pool ID: string; allowed start and end: date-time values; applicable condition text: string | X.C.3 and approved parking controls determine rights over the full booked period. Unknown, missing, failed, or invalid results cannot support a booking. Exact source response fields remain open. | SR.2, SR.15 |
| Approved pool controls | Pool ID: string; capacity: nonnegative integer; rule and closure records with start and end times | Places in the approved pool, from Parking Administrator controls. A closure blocks new bookings in its period. These updates apply approved policy; they do not create permit rights. | SR.4, SR.8, SR.14, SR.15 |
| Booking record: proposed closed stored list | Reservation ID: string; identity reference: string; pool ID: string; booked start and end: date-time values; status: `confirmed` or `cancelled`; applicable parking conditions: approved condition text; request ID: string | Each unique request ID adds at most one commitment. Counts use overlapping intervals. Cancellation of a future booking releases its held capacity once. No additional stored personal fields are approved by this draft. | SR.4, SR.6, SR.10, SR.13 |
| Access log: proposed closed stored list | Identity reference: string; role: string; event time: date-time value; action: string; result: string | Role and allowed staff account list from IT and Parking Services. Retention duration remains open. | SR.13, SR.14 |
| Option display view | Lot or pool label: string; permit limit: string; allowed time: approved interval or condition text; route distance: number or unavailable; capacity basis: string | Route distance needs a stated unit in the source record. The owner must agree that unit; this draft adds no new distance target. Walk minutes may also be shown as a labeled estimate. A missing fact is shown as unavailable. | SR.3 |
| Confirmation display view | Reservation ID, lot or pool, start time, end time, applicable conditions, and staff contact | Build from the saved booking and approved pool record. State the approved-pool place limit. Staff contact and lot label are approved pool data, not extra copied personal fields in the closed booking store. | SR.5, SR.13 |
| Lot address and route view | Lot address: string; route information: approved source view or unavailable; source and time basis for each estimate | X.C.4 supplies map and route data. Keep valid lot-address data available to show with a warning when route guidance alone fails. The exact map schema remains open. | SR.3, SR.16 |
| Affected booking list | Reservation ID, pool, booked period, and flag reason | Derived from confirmed records that overlap a closure or a capacity-shortage interval. A flag does not cancel a booking. | SR.9 |
| Reservation summary | Selected pool and period; separate confirmed and cancelled counts: nonnegative integers; estimate source and time basis, when used | Count unique reservation IDs once by current status. An interval overlaps when its start is before the selected end and its end is after the selected start. Touching endpoints alone do not overlap. Label counts as booking records. | SR.10 |

#### Planned refresh and failure rules

Read or recheck required eligibility, current approved capacity, and overlapping confirmed commitments on each booking attempt. Do not trust an earlier option list. Use the latest approved controls for searches and confirmations. SR.8 and SR.9 require all 20 approved change cases to apply or flag within 60 seconds; that is an application update limit, not an invented polling interval. The live source query cadence and any caching method must be agreed with the source owners. This draft adds no source-age threshold.

Treat a missing field, invalid record, failed response, unknown eligibility result, or unavailable required store as unavailable for confirmation. Show which source or record could not support the request. Do not create a confirmed booking until the required records return valid results. Mark missing optional route or estimate facts as unavailable and label all estimates. When only route guidance fails, keep a valid confirmed booking and show the approved lot address with a warning. If required eligibility or capacity data also fail, apply SR.15 instead of the route-only rule.

Keep only the proposed SR.13 fields in stored records, logs, and exports; exclude passwords and payment-card data. Test extra input fields in search, booking, cancellation, and failure cases. Repeat the field check against the IT-approved list before live acceptance. IT must approve the retention duration before live use; no duration is assumed here.

Use fixture and simulated records until source owners approve access and Parking Services approves a real pool and staff operating plan. Do not label calculated capacity or booking counts as sensed occupancy.

## Model Response Contract

### Status and input

This is the proposed SR.17/SR.18 response contract for later implementation. The current repository has no language-model module or call. This Chapter 3 work needs no model service, API key, or provider purchase. The Lab Manual places implementation in Chapter 8.

The model is asked to explain parking choices and basic rules using only the approved record supplied for the request. Pass the user's parking question and the supported trip, option, rule, and booking facts needed to answer it. Keep a list of supported facts for the 20 reviewed SR.17 requests. Do not pass passwords, payment-card details, access logs, or unnecessary identity details.

The model may explain the record. It may not grant permit rights, change capacity, confirm or cancel bookings, or invent a parking fact. Those decisions stay with the approved source records and normal application controls. If a supporting fact is missing, describe it as unavailable.

### Output schema

Return one JSON object with one field:

```json
{"message": "<plain, source-based parking answer>"}
```

`message` must be a string with text after leading and trailing spaces are removed. A missing reply, invalid JSON, absent `message`, wrong field type, or blank string fails this proposed format. Treat extra fields as outside the proposed one-field schema. The team must review the schema before implementation.

Format checking alone cannot show that every parking fact is supported. SR.17 separately requires checking 20 answers against the fixed supported-fact lists and repeating the review after a model or prompt change. Do not claim that a JSON check proves correct AI content.

### Fixed fallback

If the reply is missing or fails the reviewed format, do not show raw model output or an internal error. Build the displayed message directly from the approved parking record. The proposed fixed template is:

```text
Parking option: {lot_or_pool}. Permit limit: {permit_limit}. Allowed time: {allowed_time}. Capacity basis: {capacity_basis}.
```

The fields come from the same approved option view used for SR.3. Replace an unavailable fact with `unavailable`; label an estimate as an estimate. This template does not promise an empty bay or create a booking. When the approved record itself is unavailable, use the fixed message:

```text
Parking information is unavailable. Check the approved campus parking source.
```

These exact template words are proposed build choices, not a new stakeholder target. The team must review them. Required-data failure still blocks a booking under SR.15. Route-guidance-only failure still retains a valid booking under SR.16. AI failure does not replace either rule.

Inject the 10 SR.18 missing or malformed reply cases named in the acceptance criterion. The source-based fallback must match the supplied record in all cases. No raw reply or internal error may reach the driver. Do not replace the 20-case grounding review with this separate 10-case format check.

## Named red suite and automatic check

`tests/acceptance_cases.json` carries the 20 acceptance IDs, need and requirement statements, exact MOEs and validation criteria, and test names. `tests/test_spec_acceptance.py` contains the matching 20 named placeholder tests. Every acceptance test contains an explicit failing assertion for this Chapter 3 increment. Do not mark it skipped or xfail, and do not soften the CI result to hide an unmet criterion.

Run from the repository root:

```text
python -m pytest tests/ -v
```

The coverage check verifies that all 13 needs, 18 requirements, 20 saved trace pairs, and 20 test names are represented, and that each acceptance criterion appears in this canonical file. A passing coverage check does not mean the acceptance criteria pass.

`tests/test_skeleton.py` holds developer tests for the walking skeleton. They check that the code does what its own docstrings say, such as refusing an unconfirmed identity or an overlapping booking in a full pool. They are kept out of `test_spec_acceptance.py` on purpose: the coverage check expects that file to hold exactly the 20 named tests, and a passing developer test is not acceptance evidence for any SR. Install `requirements.txt` as well as `requirements-dev.txt` before running them, because they start the FastAPI app.

The GitHub workflow must run this suite on every push and pull request. The intended Chapter 3 result is a red acceptance check with the named placeholder failures. Import errors, missing dependencies, and workflow setup errors are not evidence of an unmet acceptance criterion. Save the commit ID and the actual CI run link and result in the product-build record after pushing. Do not write a successful or failed run claim before observing it.

Later chapters replace each placeholder with a real check of the same criterion and turn that test green as the outcome is implemented. Human and field criteria need real reviewed evidence; they cannot be replaced by a passing unit-test assertion. Keep the N and SR identifiers when replacing test bodies.

## Team and owner review still needed

The repository scaffold can be committed before all stakeholder decisions are approved, provided its draft status stays clear. Team members must review and adopt this specification as the source for later prompts. Their awareness and agreement are not claimed by the assistant.

Open decisions include the older-to-current target changes, live source fields and failure meanings, exact date-time format and campus time zone, source query cadence and caching, staff account approvals, personal-data list and retention, screen-reader and browser versions, AI schema and template words, pilot pool and staff duties, and the planned human and field samples. Keep the criteria unchanged unless the team and responsible owners approve a change. Then update the model, this file, the manifest, tests, and report together.

Record the actual assistant request, reused sources, checks, edits, and review limits in `docs/prompt-log.md`. Do not report an assistant draft as team-authored stakeholder judgment.

