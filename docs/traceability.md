# Function to module traceability

One row per function on the first-level IDEF0 of F.0 Provide Campus Parking Reservations in the
Innoslate model (Chapter 7). Each function has exactly one module. The API routes in `api/main.py`
are not on this list because they are not functions on the IDEF0: they call these modules in the
order a use case needs, the way a mechanism would.

| Function ID | Function name | Module | Requirements | Tests in `tests/test_functional_requirements.py` |
| --- | --- | --- | --- | --- |
| F.1 | Apply Parking Controls | `functions/f1_apply_parking_controls.py` | 1.4.1.1, 1.4.1.8 | `test_FR_1_4_1_1_approved_change_takes_effect_and_unapproved_change_is_rejected`<br>`test_FR_1_4_1_8_all_functions_use_the_same_current_rules_after_a_change` |
| F.2 | Validate Trip Eligibility | `functions/f2_validate_trip_eligibility.py` | 1.4.1.2, 1.4.1.9 | `test_FR_1_4_1_2_flags_missing_trip_facts_and_sends_only_approved_identity_fields`<br>`test_FR_1_4_1_9_trip_details_entered_once_are_carried_to_options_and_booking` |
| F.3 | Gather Lot Location and Route Data | `functions/f3_gather_lot_location_and_route_data.py` | 1.4.1.3, 1.4.1.10 | `test_FR_1_4_1_3_keeps_lots_and_marks_estimates_unavailable_when_map_is_down`<br>`test_FR_1_4_1_10_confirmation_uses_route_guidance_kept_from_the_search` |
| F.4 | Present Eligible Parking Options | `functions/f4_present_eligible_parking_options.py` | 1.4.1.4 | `test_FR_1_4_1_4_presents_only_permitted_open_options_with_selection_facts` |
| F.5 | Recheck and Record Reservation | `functions/f5_recheck_and_record_reservation.py` | 1.4.1.5, 1.4.1.11 | `test_FR_1_4_1_5_refuses_unknown_eligibility_and_keeps_one_record_per_request`<br>`test_FR_1_4_1_11_every_saved_reservation_is_available_to_reports` |
| F.6 | Provide Confirmation and Route Guidance | `functions/f6_provide_confirmation_and_route_guidance.py` | 1.4.1.6 | `test_FR_1_4_1_6_confirmation_shows_booking_facts_and_route_failure_keeps_booking` |
| F.7 | Report Reservations and Affected Bookings | `functions/f7_report_reservations_and_affected_bookings.py` | 1.4.1.7 | `test_FR_1_4_1_7_reports_every_affected_booking_with_matching_counts` |

Requirements 1.4.1.8 to 1.4.1.11 are the derived requirements from Chapter 5. They are listed
against the function that owns them in the model, but their tests run more than one module:
1.4.1.8 checks that F.4, F.5 and F.7 decide from the same approved rules after a change, 1.4.1.9
follows the trip details from F.2 to F.5, 1.4.1.10 follows route guidance from F.3 to F.6, and
1.4.1.11 checks that every record F.5 saves reaches F.7.

## Second level of F.5 Recheck and Record Reservation

F.5 is the function decomposed in Chapter 9. Its second-level IDEF0 has four functions, each
performed by one component of C.5 Reservation Subsystem. The F.5 module carries them out as four
steps, one private function each, and its docstring lists the same mapping. The requirements are
from the Reservation Subsystem Specification (`docs/reservation-subsystem-spec.md`).

| Function ID | Function name | Performed by | Code | Requirements | Tests |
| --- | --- | --- | --- | --- | --- |
| F.5.1 | Screen Reservation Request | C.5.1 Request Validation Service | `functions/f5_recheck_and_record_reservation.py`, `_screen_request` | RS.1.4.1, RS.1.1.1 | `tests/test_f5_second_level.py::test_RS_1_4_1_incomplete_request_is_refused_before_any_rule_is_read` |
| F.5.2 | Recheck Booking Eligibility | C.5.2 Permit Validation Service | `functions/f5_recheck_and_record_reservation.py`, `_recheck_booking_eligibility` | RS.1.4.2, RS.1.1.2, RS.1.1.3 | `tests/test_f5_second_level.py::test_RS_1_4_2_permit_status_and_closures_are_rechecked_for_the_whole_period` |
| F.5.3 | Commit Capacity Hold | C.5.3 Capacity Ledger | `functions/f5_recheck_and_record_reservation.py`, `_commit_capacity_hold`; component built from its specification: `functions/f5_3_commit_capacity_hold.py` | RS.1.4.3, RS.1.4.5, RS.1.2.1, RS.1.2.3, RS.2.5 | `tests/test_c5_3_capacity_ledger.py::test_RS_1_4_3_last_free_place_goes_to_exactly_one_of_100_concurrent_requests`<br>`tests/test_c5_3_capacity_ledger.py::test_RS_2_5_holds_for_any_minute_never_exceed_capacity`<br>`tests/test_c5_3_promoted_requirements.py::test_RS_1_4_5_capacity_cut_keeps_saved_holds_and_refuses_full_minutes` |
| F.5.4 | Issue Booking Refusal | C.5.4 Refusal Notice Builder | `functions/f5_recheck_and_record_reservation.py`, `_issue_booking_refusal` | RS.1.4.4, RS.1.2.2 | `tests/test_f5_second_level.py::test_RS_1_4_4_every_refusal_names_its_specific_reason_and_saves_nothing` |

The internal flows IO.20 Screened Booking Request, IO.21 Eligible Booking Request and IO.22 Booking
Refusal Reason have schemas under `x-c5-internal-flows` in `contracts/api-v1.yaml`, next to the F.5
operation `recheckAndRecordReservation` and the F.5.3 operation for the Capacity Ledger. The driver
reaches F.5 through `POST /api/reserve` (row 4 of `docs/route-table.md`, UC.1.7 to UC.1.9).

The booking route calls the F.5.3 ledger directly. Its SQLite transaction checks the busiest
minute and saves the hold under the same write lock. The component test covers 100 bursts of
100 requests. The store test covers two connections, and the API test covers refusal and retry
after a restart. See ADR-0006 and RK.1 in `docs/risks.md`.

All of these tests run in `.github/workflows/tests.yml`.
