"""GENERATED from contracts/api-v1.yaml by tools/gen_stubs.py. Do not edit by hand."""

from typing import Dict, List, Optional, TypedDict


class Window(TypedDict, total=False):
    start: int
    end: int


class PoolRule(TypedDict, total=False):
    name: str
    capacity: int
    permits: List[str]
    closures: List[Window]


class ApprovedParkingRules(TypedDict, total=False):  # IO.17
    version: int
    pools: Dict[str, PoolRule]


class ControlChangeResult(TypedDict, total=False):  # IO.19
    accepted: bool
    reason: Optional[str]
    version: int
    pool_id: str
    windows: List[Window]


class TripDetails(TypedDict, total=False):  # IO.14
    driver_id: str
    destination: str
    start: Optional[int]
    end: Optional[int]
    missing: List[str]


class CandidateLot(TypedDict, total=False):
    pool_id: str
    name: str
    address: Optional[str]
    walk_minutes: Optional[int]


class CandidateParkingData(TypedDict, total=False):  # IO.15
    trip: TripDetails
    lots: List[CandidateLot]
    route_status: str


class RouteGuidanceData(TypedDict, total=False):  # IO.16
    destination: str
    status: str
    routes: Dict[str, Optional[str]]
    addresses: Dict[str, Optional[str]]


class ConfirmedReservationRecord(TypedDict, total=False):  # IO.8
    reservation_id: str
    request_id: str
    driver_id: str
    pool_id: str
    start: int
    end: int
    status: str

ReservationRecords = List[ConfirmedReservationRecord]  # IO.18


class ParkingRulesAndCapacityChange(TypedDict, total=False):  # IO.10 (crosses the CampusPark boundary)
    account: str
    pool_id: str
    capacity: Optional[int]
    permits: Optional[List[str]]
    closures: Optional[List[Window]]


class ParkingRequest(TypedDict, total=False):  # IO.1 (crosses the CampusPark boundary)
    driver_id: str
    destination: str
    arrival: str
    hours: int


class IdentityPermitValidationRequest(TypedDict, total=False):  # IO.2 (crosses the CampusPark boundary)
    driver_id: str


class IdentityPermitEligibility(TypedDict, total=False):  # IO.3 (crosses the CampusPark boundary)
    driver_id: str
    status: str
    permit: Optional[str]


class LocationRouteRequest(TypedDict, total=False):  # IO.4 (crosses the CampusPark boundary)
    destination: str


class ParkingLocationsRouteInformation(TypedDict, total=False):  # IO.5 (crosses the CampusPark boundary)
    status: str
    lots: List[CandidateLot]


class EligibleParkingOptions(TypedDict, total=False):  # IO.6 (crosses the CampusPark boundary)
    status: str
    reason: Optional[str]
    options: List[dict]


class ReservationRequest(TypedDict, total=False):  # IO.7 (crosses the CampusPark boundary)
    request_id: str
    driver_id: str
    pool_id: str
    start: int
    end: int


class ScreenedBookingRequest(TypedDict, total=False):  # IO.20
    request_id: str
    driver_id: str
    pool_id: str
    start: int
    end: int


class EligibleBookingRequest(TypedDict, total=False):  # IO.21
    request_id: str
    driver_id: str
    pool_id: str
    start: int
    end: int


class BookingRefusalReason(TypedDict, total=False):  # IO.22
    request_id: Optional[str]
    reason: str


class BookingRefusalNotice(TypedDict, total=False):  # IO.13 (crosses the CampusPark boundary)
    reason: str
    message: str


class ReservationConfirmationGuidance(TypedDict, total=False):  # IO.9 (crosses the CampusPark boundary)
    reservation_id: str
    lot: str
    address: Optional[str]
    start: int
    end: int
    guidance: Optional[str]
    warning: Optional[str]


class ControlUpdateAcknowledgement(TypedDict, total=False):  # IO.11 (crosses the CampusPark boundary)
    accepted: bool
    version: int
    pool_id: str
    reason: Optional[str]


class ReservationReports(TypedDict, total=False):  # IO.12 (crosses the CampusPark boundary)
    pool_id: str
    affected: List[ConfirmedReservationRecord]
    confirmed_count: int

