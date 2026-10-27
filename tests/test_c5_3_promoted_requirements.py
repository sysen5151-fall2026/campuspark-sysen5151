"""Tests for the requirements promoted from the C.5.3 deviation log (docs/deviation-log.md).

Written after reconciliation from the amended RS.1.4.3 and the new RS.1.4.5, so that every promoted
assumption is checked as a requirement and not only as a property of the generated code.
"""
from functions.f5_3_commit_capacity_hold import CapacityLedger, commit_capacity_hold


def rules(capacity, pool_id="P1"):
    return {"version": 1, "pools": {pool_id: {"name": "North Lot", "capacity": capacity,
                                              "permits": ["student"], "closures": []}}}


def request(request_id, start=540, end=660, pool_id="P1", driver_id="student01"):
    return {"request_id": request_id, "driver_id": driver_id, "pool_id": pool_id, "start": start, "end": end}


def test_RS_1_4_3_repeat_returns_saved_reservation_even_when_capacity_data_are_now_missing():
    """RS.1.4.3 (amended, D2): a repeated request ID gets its saved reservation whatever the capacity data."""
    ledger = CapacityLedger()
    saved, _, refusal = commit_capacity_hold(request("a"), approved_rules=rules(1), ledger=ledger)
    assert refusal is None
    for later_rules in ({"version": 2, "pools": {}}, rules(None), rules(0)):
        again, records, refusal = commit_capacity_hold(request("a"), approved_rules=later_rules, ledger=ledger)
        assert again == saved and refusal is None and records == [saved]


def test_RS_1_4_5_capacity_cut_keeps_saved_holds_and_refuses_full_minutes():
    """RS.1.4.5 (new, D4): saved reservations stay when capacity falls below them; full minutes are refused."""
    ledger = CapacityLedger()
    kept = [commit_capacity_hold(request(r), approved_rules=rules(3), ledger=ledger)[0] for r in ("a", "b", "c")]
    assert all(kept)
    _, records, refusal = commit_capacity_hold(request("d", start=600, end=630), approved_rules=rules(1), ledger=ledger)
    assert refusal == {"request_id": "d", "reason": "pool_full"}
    assert records == kept == ledger.records()
    confirmed, _, refusal = commit_capacity_hold(request("e", start=660, end=720), approved_rules=rules(1), ledger=ledger)
    assert refusal is None and confirmed["request_id"] == "e"


def test_negative_capacity_is_invalid_data_not_a_full_pool():
    """D5 correction: the contract sets capacity minimum 0, so a negative value is missing data (RS.2.3)."""
    _, records, refusal = commit_capacity_hold(request("a"), approved_rules=rules(-1), ledger=CapacityLedger())
    assert refusal == {"request_id": "a", "reason": "missing_data"} and records == []
