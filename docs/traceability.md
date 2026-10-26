# Function to module traceability

One row per function on the first-level IDEF0 of F.0 Provide Campus Parking Reservations in the
Innoslate model (Chapter 7). Each function has exactly one module. The API routes in `api/main.py`
are not on this list because they are not functions on the IDEF0: they call these modules in the
order a use case needs, the way a mechanism would.

| Function ID | Function name | Module |
| --- | --- | --- |
| F.1 | Apply Parking Controls | `functions/f1_apply_parking_controls.py` |
| F.2 | Validate Trip Eligibility | `functions/f2_validate_trip_eligibility.py` |
| F.3 | Gather Lot Location and Route Data | `functions/f3_gather_lot_location_and_route_data.py` |
| F.4 | Present Eligible Parking Options | `functions/f4_present_eligible_parking_options.py` |
| F.5 | Recheck and Record Reservation | `functions/f5_recheck_and_record_reservation.py` |
| F.6 | Provide Confirmation and Route Guidance | `functions/f6_provide_confirmation_and_route_guidance.py` |
| F.7 | Report Reservations and Affected Bookings | `functions/f7_report_reservations_and_affected_bookings.py` |

Requirement and test columns are added in the Chapter 5 increment.
