"""GENERATED from contracts/api-v1.yaml by tools/gen_stubs.py. Do not edit by hand."""

from typing import Any, List, Optional, Tuple

from contracts.generated.flows import *  # noqa: F401,F403


def apply_parking_controls(*, parking_rules_and_capacity: ParkingRulesAndCapacityChange, rules_store: Any) -> Tuple[ApprovedParkingRules, ControlChangeResult]:
    """applyParkingControls /internal/f1/apply-parking-controls. F.1 Apply Parking Controls (1.4.1.1, 1.4.1.8). Produces IO.17 and IO.19.
    parking_rules_and_capacity = IO.10 (control). mechanism: rules_store.
    Implemented in functions/f1_apply_parking_controls.py."""
    raise NotImplementedError


def validate_trip_eligibility(parking_request: ParkingRequest, *, approved_rules: ApprovedParkingRules) -> Tuple[IdentityPermitValidationRequest, TripDetails]:
    """validateTripEligibility /internal/f2/validate-trip-eligibility. F.2 Validate Trip Eligibility (1.4.1.2, 1.4.1.9). Produces IO.2 and IO.14.
    parking_request = IO.1 (input); approved_rules = IO.17 (control).
    Implemented in functions/f2_validate_trip_eligibility.py."""
    raise NotImplementedError


def request_location_and_route(trip_details: TripDetails, *, eligibility: IdentityPermitEligibility) -> LocationRouteRequest:
    """requestLocationAndRoute /internal/f3/request-location-and-route. F.3 writes IO.4 for an eligible trip (1.4.1.3).
    trip_details = IO.14 (input); eligibility = IO.3 (control).
    Implemented in functions/f3_gather_lot_location_and_route_data.py."""
    raise NotImplementedError


def gather_lot_location_and_route_data(trip_details: TripDetails, locations_and_routes: ParkingLocationsRouteInformation, *, eligibility: IdentityPermitEligibility) -> Tuple[CandidateParkingData, RouteGuidanceData]:
    """gatherLotLocationAndRouteData /internal/f3/gather-lot-location-and-route-data. F.3 turns the map answer into IO.15 and IO.16 (1.4.1.3, 1.4.1.10).
    trip_details = IO.14 (input); locations_and_routes = IO.5 (input); eligibility = IO.3 (control).
    Implemented in functions/f3_gather_lot_location_and_route_data.py."""
    raise NotImplementedError


def present_eligible_parking_options(candidate_parking_data: CandidateParkingData, reservation_records: ReservationRecords, *, eligibility: IdentityPermitEligibility, approved_rules: ApprovedParkingRules) -> EligibleParkingOptions:
    """presentEligibleParkingOptions /internal/f4/present-eligible-parking-options. F.4 Present Eligible Parking Options (1.4.1.4). Produces IO.6.
    candidate_parking_data = IO.15 (input); reservation_records = IO.18 (input); eligibility = IO.3 (control); approved_rules = IO.17 (control).
    Implemented in functions/f4_present_eligible_parking_options.py."""
    raise NotImplementedError


def recheck_and_record_reservation(reservation_request: ReservationRequest, *, eligibility: IdentityPermitEligibility, approved_rules: ApprovedParkingRules, reservation_store: Any) -> Tuple[ConfirmedReservationRecord, BookingRefusalNotice, ReservationRecords]:
    """recheckAndRecordReservation /internal/f5/recheck-and-record-reservation. F.5 Recheck and Record Reservation (1.4.1.5, 1.4.1.11). Produces IO.8 or IO.13, and IO.18.
    reservation_request = IO.7 (input); eligibility = IO.3 (control); approved_rules = IO.17 (control). mechanism: reservation_store.
    Implemented in functions/f5_recheck_and_record_reservation.py."""
    raise NotImplementedError


def provide_confirmation_and_route_guidance(confirmed_record: ConfirmedReservationRecord, route_guidance_data: RouteGuidanceData, *, approved_rules: ApprovedParkingRules) -> ReservationConfirmationGuidance:
    """provideConfirmationAndRouteGuidance /internal/f6/provide-confirmation-and-route-guidance. F.6 Provide Confirmation and Route Guidance (1.4.1.6, 1.4.1.10). Produces IO.9.
    confirmed_record = IO.8 (input); route_guidance_data = IO.16 (input); approved_rules = IO.17 (control).
    Implemented in functions/f6_provide_confirmation_and_route_guidance.py."""
    raise NotImplementedError


def report_reservations_and_affected_bookings(reservation_records: ReservationRecords, control_change_result: ControlChangeResult, *, approved_rules: ApprovedParkingRules) -> Tuple[ControlUpdateAcknowledgement, ReservationReports]:
    """reportReservationsAndAffectedBookings /internal/f7/report-reservations-and-affected-bookings. F.7 Report Reservations and Affected Bookings (1.4.1.7, 1.4.1.11). Produces IO.11 and IO.12.
    reservation_records = IO.18 (input); control_change_result = IO.19 (input); approved_rules = IO.17 (control).
    Implemented in functions/f7_report_reservations_and_affected_bookings.py."""
    raise NotImplementedError

