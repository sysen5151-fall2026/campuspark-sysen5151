"""Tests for the second level of F.5 Recheck and Record Reservation (Chapter 9).

One test per function requirement of the Reservation Subsystem Specification that the F.5 module
carries out step by step: RS.1.4.1 (F.5.1), RS.1.4.2 (F.5.2) and RS.1.4.4 (F.5.4). RS.1.4.3
(F.5.3) and RS.2.5 are tested against the C.5.3 Capacity Ledger in tests/test_c5_3_*.py.
Each test calls F.5 through its contract signature, as the booking route does.
"""

import pytest

from functions.f5_recheck_and_record_reservation import (
    ReservationStore,
    recheck_and_record_reservation,
)

DRIVER = "student01"
RULES = {
    "version": 1,
    "pools": {
        "P-NORTH": {"name": "North Lot", "capacity": 1, "permits": ["student"],
                    "closures": [{"start": 720, "end": 780}]},
        "P-STAFF": {"name": "Staff Lot", "capacity": 5, "permits": ["staff"], "closures": []},
    },
}


class RulesNotToBeRead(dict):
    """IO.17 that fails the test if F.5 reads it."""

    def get(self, *args, **kwargs):
        raise AssertionError("approved rules were read for a request that failed screening")

    def __getitem__(self, key):
        raise AssertionError("approved rules were read for a request that failed screening")


def request(request_id="req-1", pool_id="P-NORTH", start=540, end=660, driver_id=DRIVER):
    return {"request_id": request_id, "driver_id": driver_id, "pool_id": pool_id,
            "start": start, "end": end}


def eligible(permit="student", status="eligible", driver_id=DRIVER):
    return {"driver_id": driver_id, "status": status, "permit": permit}


def book(req, store, elig=None, rules=RULES):
    return recheck_and_record_reservation(req, eligibility=elig or eligible(),
                                          approved_rules=rules, reservation_store=store)


@pytest.mark.parametrize("change", [
    {"request_id": ""}, {"pool_id": None}, {"driver_id": ""}, {"start": None},
    {"end": None}, {"start": 660, "end": 540}, {"start": 600, "end": 600},
])
def test_RS_1_4_1_incomplete_request_is_refused_before_any_rule_is_read(change):
    """RS.1.4.1 Screen Reservation Request [F.5.1, C.5.1 Request Validation Service]

    Passes when a request missing a request ID, pool, identity reference or a period that ends
    after it starts is refused with missing_data, nothing is saved, and the approved rules are
    never read.
    """
    store = ReservationStore()
    bad = request()
    bad.update(change)
    record, refusal, records = book(bad, store, rules=RulesNotToBeRead())
    assert record is None
    assert refusal["reason"] == "missing_data"
    assert store.all() == [] and records == []


def test_RS_1_4_2_permit_status_and_closures_are_rechecked_for_the_whole_period():
    """RS.1.4.2 Recheck Booking Eligibility [F.5.2, C.5.2 Permit Validation Service]

    Passes when a permit the pool does not accept, an eligibility answer that is not "eligible",
    and a period that crosses a closure are all refused, and a period that ends exactly when the
    closure starts is booked.
    """
    store = ReservationStore()

    _, refusal, _ = book(request("req-a", pool_id="P-STAFF"), store)
    assert refusal["reason"] == "not_eligible"

    for n, status in enumerate(("unknown", "invalid")):
        _, refusal, _ = book(request("req-b%d" % n), store, elig=eligible(status=status))
        assert refusal["reason"] == "not_eligible"
    for n, status in enumerate(("failed", "missing")):
        _, refusal, _ = book(request("req-c%d" % n), store, elig=eligible(status=status))
        assert refusal["reason"] == "missing_data"

    _, refusal, _ = book(request("req-d", start=700, end=760), store)
    assert refusal["reason"] == "closed"
    assert store.all() == []

    record, refusal, _ = book(request("req-e", start=600, end=720), store)
    assert refusal is None and record["status"] == "confirmed"


def test_RS_1_4_4_every_refusal_names_its_specific_reason_and_saves_nothing():
    """RS.1.4.4 Issue Booking Refusal [F.5.4, C.5.4 Refusal Notice Builder]

    Passes when missing_data, not_eligible, closed and pool_full each give a notice with that
    reason and a message in words, and no refused request adds a record.
    """
    store = ReservationStore()
    first, _, _ = book(request("req-full"), store)
    assert first is not None

    cases = {
        "missing_data": (request("req-1", start=None), eligible()),
        "not_eligible": (request("req-2", pool_id="P-STAFF"), eligible()),
        "closed": (request("req-3", start=700, end=760), eligible()),
        "pool_full": (request("req-4", start=600, end=700), eligible()),
    }
    for reason, (req, elig) in cases.items():
        record, refusal, records = book(req, store, elig=elig)
        assert record is None, reason
        assert refusal["reason"] == reason
        assert isinstance(refusal["message"], str) and len(refusal["message"].split()) >= 5
        assert records == [first], reason
