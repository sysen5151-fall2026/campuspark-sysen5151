# Function to module traceability

One row per function on the first-level IDEF0 of F.0 Provide Campus Parking Reservations in the
Innoslate model (Chapter 7). Each function has exactly one module. The API routes in `api/main.py`
are not on this list because they are not functions on the IDEF0: they call these modules in the
order a use case needs, the way a mechanism would.

| Function ID | Function name | Module | Requirements | Tests in `tests/test_functional_requirements.py` |
| --- | --- | --- | --- | --- |
| F.1 | Apply Parking Controls | `functions/f1_apply_parking_controls.py` | 1.4.1.1, 1.4.1.8 | `test_FR_1_4_1_1_...`, `test_FR_1_4_1_8_...` |
| F.2 | Validate Trip Eligibility | `functions/f2_validate_trip_eligibility.py` | 1.4.1.2, 1.4.1.9 | `test_FR_1_4_1_2_...`, `test_FR_1_4_1_9_...` |
| F.3 | Gather Lot Location and Route Data | `functions/f3_gather_lot_location_and_route_data.py` | 1.4.1.3, 1.4.1.10 | `test_FR_1_4_1_3_...`, `test_FR_1_4_1_10_...` |
| F.4 | Present Eligible Parking Options | `functions/f4_present_eligible_parking_options.py` | 1.4.1.4 | `test_FR_1_4_1_4_...` |
| F.5 | Recheck and Record Reservation | `functions/f5_recheck_and_record_reservation.py` | 1.4.1.5, 1.4.1.11 | `test_FR_1_4_1_5_...`, `test_FR_1_4_1_11_...` |
| F.6 | Provide Confirmation and Route Guidance | `functions/f6_provide_confirmation_and_route_guidance.py` | 1.4.1.6 | `test_FR_1_4_1_6_...` |
| F.7 | Report Reservations and Affected Bookings | `functions/f7_report_reservations_and_affected_bookings.py` | 1.4.1.7 | `test_FR_1_4_1_7_...` |

Requirements 1.4.1.8 to 1.4.1.11 are the derived requirements from Chapter 5. They are listed
against the function that owns them in the model, but their tests run more than one module:
1.4.1.8 checks that F.4, F.5 and F.7 decide from the same approved rules after a change, 1.4.1.9
follows the trip details from F.2 to F.5, 1.4.1.10 follows route guidance from F.3 to F.6, and
1.4.1.11 checks that every record F.5 saves reaches F.7.
