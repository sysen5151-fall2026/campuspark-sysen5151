"""First-level functions of F.0 Provide Campus Parking Reservations.

One module per function on the first-level IDEF0 in the Innoslate model (Chapter 7):

    F.1  Apply Parking Controls                      f1_apply_parking_controls
    F.2  Validate Trip Eligibility                   f2_validate_trip_eligibility
    F.3  Gather Lot Location and Route Data          f3_gather_lot_location_and_route_data
    F.4  Present Eligible Parking Options            f4_present_eligible_parking_options
    F.5  Recheck and Record Reservation              f5_recheck_and_record_reservation
    F.6  Provide Confirmation and Route Guidance     f6_provide_confirmation_and_route_guidance
    F.7  Report Reservations and Affected Bookings   f7_report_reservations_and_affected_bookings

Signatures follow the ICOM translation in the Lab Manual: inputs are positional parameters,
controls are keyword-only configuration, outputs are return values, and mechanisms are injected
dependencies. Times are minutes since midnight on one day, as in the walking skeleton, and every
booked period is the half-open interval [start, end).
"""
