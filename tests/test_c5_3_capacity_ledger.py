"""Requirement tests for C.5.3 Capacity Ledger, which performs F.5.3 Commit Capacity Hold.

Every test comes from docs/reservation-subsystem-spec.md (Reservation Subsystem Specification,
Chapter 9) and from contracts/api-v1.yaml version 1.1 (EligibleBookingRequest, ApprovedParkingRules,
PoolRule, ConfirmedReservationRecord, ReservationRecords, BookingRefusalReason and the
commitCapacityHold operation). The tests were written from those documents before any
implementation of the component existed.

Conventions taken from the contract and the specification:
* Times are minutes since midnight and every period is the half-open interval [start, end), so a
  booking that ends at minute 540 and one that starts at minute 540 never hold a place together.
* Capacity counts the places held at the same minute, not every booking that touches the period
  (C.5.3: "check that the pool has a free place for every minute of the booked period").
* commit_capacity_hold returns (IO.8 or None, IO.18, IO.22 or None); exactly one of IO.8 and IO.22
  is set.

The concurrency tests release 100 threads together with a threading.Barrier (RS.2.5: at least 100
requests arriving at once) and shorten the interpreter's thread switch interval while the threads
run, so that a check-then-save race has a real chance to show up under the GIL. A correct ledger
passes whatever the interval is.
"""

import contextlib
import functools
import json
import math
import random
import sys
import threading
import time
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from functions.f5_3_commit_capacity_hold import (  # noqa: E402
    CapacityLedger,
    commit_capacity_hold,
)

# ConfirmedReservationRecord (IO.8) required fields; RS.2.1 makes this the closed field list.
RECORD_FIELDS = frozenset(
    {"reservation_id", "request_id", "driver_id", "pool_id", "start", "end", "status"}
)
# EligibleBookingRequest (IO.21) fields, which the saved record carries over.
REQUEST_FIELDS = ("request_id", "driver_id", "pool_id", "start", "end")
# BookingRefusalReason (IO.22) reason enum.
REFUSAL_REASONS = frozenset({"missing_data", "not_eligible", "closed", "pool_full"})
MINUTES_PER_DAY = 1440

CONCURRENT_REQUESTS = 100  # RS.2.5: at least 100 requests arriving at once
LAST_PLACE_ROUNDS = 100  # RS.1.4.3 MOP and RS.2.5 verification: 100 rounds
SHORT_ROUNDS = 10  # rounds for the additional RS.2.5 concurrency scenarios
THREAD_TIMEOUT_S = 30.0
RESPONSE_LIMIT_S = 2.0  # RS.2.4
RESPONSE_PERCENTILE = 0.95  # RS.2.4


# ---------------------------------------------------------------------------------------------
# Builders for the contract shapes
# ---------------------------------------------------------------------------------------------


def make_pool_rule(capacity, name="Lot"):
    """One PoolRule of IO.17."""
    return {"name": name, "capacity": capacity, "permits": ["student", "staff"], "closures": []}


def make_rules(capacities, version=1):
    """IO.17 Approved Parking Rules and Capacity with one PoolRule per pool id."""
    return {
        "version": version,
        "pools": {
            pool_id: make_pool_rule(capacity, name="Lot " + pool_id)
            for pool_id, capacity in capacities.items()
        },
    }


def make_request(request_id, pool_id="P", start=480, end=540, driver_id=None):
    """IO.21 Eligible Booking Request."""
    return {
        "request_id": request_id,
        "driver_id": driver_id if driver_id is not None else "drv-" + request_id,
        "pool_id": pool_id,
        "start": start,
        "end": end,
    }


# ---------------------------------------------------------------------------------------------
# Contract shape checks
# ---------------------------------------------------------------------------------------------


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def assert_record_fields(record):
    """IO.8, or one item of IO.18, has the ConfirmedReservationRecord fields and types."""
    assert isinstance(record, dict), "a reservation record must be an object, got %r" % (record,)
    missing = RECORD_FIELDS - set(record)
    assert not missing, "reservation record lacks %s: %r" % (sorted(missing), record)
    assert isinstance(record["reservation_id"], str) and record["reservation_id"], record
    for key in ("request_id", "driver_id", "pool_id"):
        assert isinstance(record[key], str), record
    assert _is_int(record["start"]) and record["start"] >= 0, record
    assert _is_int(record["end"]) and record["end"] >= 1, record
    assert record["status"] == "confirmed", record


def assert_result_shape(result, request):
    """(IO.8 or None, IO.18, IO.22 or None) with exactly one of IO.8 and IO.22 set."""
    assert isinstance(result, tuple) and len(result) == 3, (
        "commit_capacity_hold must return (IO.8 or None, IO.18, IO.22 or None), got %r" % (result,)
    )
    io8, io18, io22 = result
    assert (io8 is None) != (io22 is None), (
        "exactly one of IO.8 and IO.22 must be set, got IO.8=%r IO.22=%r" % (io8, io22)
    )
    assert isinstance(io18, list), "IO.18 must be a list of records, got %r" % (io18,)
    for record in io18:
        assert_record_fields(record)
    if io8 is not None:
        assert_record_fields(io8)
        assert io8["request_id"] == request["request_id"], (io8, request)
    else:
        assert isinstance(io22, dict), "IO.22 must be an object, got %r" % (io22,)
        assert "request_id" in io22 and "reason" in io22, io22
        assert io22["reason"] in REFUSAL_REASONS, io22
        if io22["reason"] == "pool_full":
            assert io22["request_id"] == request["request_id"], (io22, request)
        else:
            assert io22["request_id"] in (request["request_id"], None), (io22, request)


def commit(request, approved_rules, ledger):
    """Call F.5.3 with a copy of IO.21 and check the shape of what comes back."""
    result = commit_capacity_hold(dict(request), approved_rules=approved_rules, ledger=ledger)
    assert_result_shape(result, request)
    return result


def assert_confirmed(result, context=""):
    io8, _, io22 = result
    assert io22 is None and io8 is not None, "%s: expected a confirmation, got refusal %r" % (
        context,
        io22,
    )
    return io8


def assert_refused(result, reason, context=""):
    io8, _, io22 = result
    assert io8 is None and io22 is not None, "%s: expected a %s refusal, got record %r" % (
        context,
        reason,
        io8,
    )
    assert io22["reason"] == reason, "%s: expected reason %s, got %r" % (context, reason, io22)
    return io22


# ---------------------------------------------------------------------------------------------
# Record checks
# ---------------------------------------------------------------------------------------------


def canonical(records):
    """Order-free comparable form of a list of records (the contract gives IO.18 no order)."""
    return sorted(json.dumps(record, sort_keys=True, default=repr) for record in records)


def records_for(ledger, request_id):
    return [record for record in ledger.records() if record["request_id"] == request_id]


def holds_per_minute(records, pool_id):
    counts = [0] * MINUTES_PER_DAY
    for record in records:
        if record["pool_id"] == pool_id:
            for minute in range(record["start"], record["end"]):
                counts[minute] += 1
    return counts


def assert_capacity_respected(records, capacities, context=""):
    for pool_id, capacity in capacities.items():
        counts = holds_per_minute(records, pool_id)
        peak = max(counts)
        assert peak <= capacity, "%s: pool %s holds %d places at minute %d, capacity %d" % (
            context,
            pool_id,
            peak,
            counts.index(peak),
            capacity,
        )


def assert_unique_ids(records, context=""):
    request_ids = [record["request_id"] for record in records]
    reservation_ids = [record["reservation_id"] for record in records]
    assert len(set(request_ids)) == len(request_ids), "%s: duplicate request IDs saved: %s" % (
        context,
        sorted(request_ids),
    )
    assert len(set(reservation_ids)) == len(reservation_ids), (
        "%s: duplicate reservation IDs saved: %s" % (context, sorted(reservation_ids))
    )


# ---------------------------------------------------------------------------------------------
# Concurrency harness
# ---------------------------------------------------------------------------------------------


@contextlib.contextmanager
def frequent_thread_switches(interval=1e-6):
    previous = sys.getswitchinterval()
    sys.setswitchinterval(interval)
    try:
        yield
    finally:
        sys.setswitchinterval(previous)


def run_at_once(calls):
    """Run each zero-argument callable in its own thread; a Barrier releases them together."""
    barrier = threading.Barrier(len(calls))
    results = [None] * len(calls)
    errors = []

    def worker(index, call):
        try:
            barrier.wait(timeout=THREAD_TIMEOUT_S)
            results[index] = call()
        except BaseException as exc:  # re-raised in the calling thread below
            errors.append(exc)
            barrier.abort()

    threads = [
        threading.Thread(target=worker, args=(index, call), daemon=True)
        for index, call in enumerate(calls)
    ]
    with frequent_thread_switches():
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + THREAD_TIMEOUT_S
        for thread in threads:
            thread.join(max(0.0, deadline - time.monotonic()))
    stuck = sum(thread.is_alive() for thread in threads)
    assert stuck == 0, "%d booking calls did not return within %.0f s" % (stuck, THREAD_TIMEOUT_S)
    own_errors = [exc for exc in errors if not isinstance(exc, threading.BrokenBarrierError)]
    if own_errors:
        raise own_errors[0]
    if errors:
        raise errors[0]
    return results


def concurrent_commits(requests, approved_rules, ledger):
    return run_at_once([functools.partial(commit, request, approved_rules, ledger) for request in requests])


# ---------------------------------------------------------------------------------------------
# RS.1.4.3 Commit Capacity Hold
# ---------------------------------------------------------------------------------------------


def test_RS_1_4_3_last_free_place_goes_to_exactly_one_of_100_concurrent_requests():
    """RS.1.4.3: check capacity and save the reservation with its capacity hold in one step.
    MOP: overbookings in 100 rounds of 100 concurrent requests (0); verification: concurrency
    test on the last free place. Each round leaves one free place, releases 100 distinct requests
    for it at once, and expects exactly one confirmation, 99 pool_full refusals that name their
    request IDs, no overbooked minute and no duplicate request IDs."""
    capacity = 5
    start, end = 480, 600
    for round_no in range(LAST_PLACE_ROUNDS):
        context = "round %d" % round_no
        ledger = CapacityLedger()
        rules = make_rules({"P": capacity})
        for k in range(capacity - 1):
            assert_confirmed(
                commit(make_request("pre-%d-%d" % (round_no, k), "P", start, end), rules, ledger),
                context + " setup",
            )
        requests = [
            make_request("r%d-t%d" % (round_no, i), "P", start, end)
            for i in range(CONCURRENT_REQUESTS)
        ]
        results = concurrent_commits(requests, rules, ledger)

        confirmed = [io8 for io8, _, _ in results if io8 is not None]
        assert len(confirmed) == 1, "%s: %d confirmations for the last free place" % (
            context,
            len(confirmed),
        )
        for request, (io8, _, io22) in zip(requests, results):
            if io8 is None:
                assert io22["reason"] == "pool_full", (context, io22)
                assert io22["request_id"] == request["request_id"], (context, io22)
        records = ledger.records()
        assert len(records) == capacity, "%s: %d records for capacity %d" % (
            context,
            len(records),
            capacity,
        )
        assert_unique_ids(records, context)
        assert_capacity_respected(records, {"P": capacity}, context)
        assert records_for(ledger, confirmed[0]["request_id"]) == confirmed, context


def test_RS_1_4_3_repeated_request_id_returns_saved_reservation_without_second_hold():
    """RS.1.4.3: return the saved reservation for a request ID already saved (C.5.3: 'returns the
    saved reservation and adds no second hold'). A repeat comes back as the saved IO.8 even when
    the pool is full with that request's own hold, and repeats never use up another place."""
    rules = make_rules({"ONE": 1, "TWO": 2})
    ledger = CapacityLedger()

    only_place = make_request("repeat-one", "ONE", 480, 540)
    saved = assert_confirmed(commit(only_place, rules, ledger), "first booking")
    for attempt in range(3):
        again = assert_confirmed(commit(only_place, rules, ledger), "repeat %d" % attempt)
        assert again == saved, "a repeat must return the saved reservation"
    assert records_for(ledger, "repeat-one") == [saved]

    repeated = make_request("repeat-two", "TWO", 600, 660)
    saved_two = assert_confirmed(commit(repeated, rules, ledger), "first booking in TWO")
    for attempt in range(3):
        assert commit(repeated, rules, ledger)[0] == saved_two, "repeat %d" % attempt
    assert_confirmed(
        commit(make_request("second-place", "TWO", 600, 660), rules, ledger),
        "the second place in TWO must still be free after repeats",
    )
    assert_refused(
        commit(make_request("third-place", "TWO", 630, 640), rules, ledger),
        "pool_full",
        "TWO holds 2 places at minute 630",
    )
    assert len([r for r in ledger.records() if r["pool_id"] == "TWO"]) == 2
    assert len(ledger.records()) == 3


def test_RS_1_4_3_repeat_with_changed_details_keeps_the_one_saved_reservation():
    """RS.1.4.3 and RS.2.5: a request ID already saved keeps exactly one reservation. The
    specification does not say whether a repeat whose pool or period differs is answered with the
    saved reservation or refused, so this test only checks what it states: the saved reservation
    stays the single, unchanged record for that request ID, and any IO.8 returned is that saved
    record (RS.1.2.1)."""
    rules = make_rules({"P": 3, "Q": 3})
    ledger = CapacityLedger()
    original = make_request("changed", "P", 480, 540)
    saved = assert_confirmed(commit(original, rules, ledger), "first booking")
    for changed in (
        make_request("changed", "P", 600, 660),
        make_request("changed", "Q", 480, 540),
        make_request("changed", "P", 480, 540, driver_id="drv-other"),
    ):
        io8 = commit(changed, rules, ledger)[0]
        if io8 is not None:
            assert io8 == saved, "a repeat returned a record other than the saved one: %r" % (io8,)
        assert records_for(ledger, "changed") == [saved]
    assert len(ledger.records()) == 1


def test_RS_1_4_3_concurrent_repeats_of_one_request_id_save_one_reservation():
    """RS.1.4.3 verification 'plus a repeated request ID', with RS.2.5 'at most one reservation per
    request ID': in each of 100 rounds, 100 copies of one request released at once for the last
    free place leave exactly one saved record, and every copy gets that saved reservation back."""
    capacity = 2
    for round_no in range(LAST_PLACE_ROUNDS):
        context = "round %d" % round_no
        ledger = CapacityLedger()
        rules = make_rules({"P": capacity})
        assert_confirmed(commit(make_request("pre-%d" % round_no, "P", 480, 600), rules, ledger))
        request = make_request("dup-%d" % round_no, "P", 480, 600)
        results = concurrent_commits([request] * CONCURRENT_REQUESTS, rules, ledger)

        saved = records_for(ledger, request["request_id"])
        assert len(saved) == 1, "%s: %d records for one request ID" % (context, len(saved))
        assert len(ledger.records()) == capacity, context
        for io8, _, io22 in results:
            assert io22 is None, "%s: a copy of a saved request was refused: %r" % (context, io22)
            assert io8 == saved[0], context


# ---------------------------------------------------------------------------------------------
# RS.2.5 Capacity Safety Under Concurrent Use
# ---------------------------------------------------------------------------------------------

# (capacity of P, existing bookings as (pool, start, end), new booking in P, expected result)
MINUTE_SCENARIOS = [
    pytest.param(1, [("P", 480, 540)], (540, 600), "confirmed", id="back_to_back_after"),
    pytest.param(1, [("P", 480, 540)], (420, 480), "confirmed", id="back_to_back_before"),
    pytest.param(1, [("P", 480, 540)], (539, 600), "pool_full", id="one_minute_overlap_at_end"),
    pytest.param(1, [("P", 480, 540)], (420, 481), "pool_full", id="one_minute_overlap_at_start"),
    pytest.param(
        2,
        [("P", 480, 540), ("P", 540, 600)],
        (500, 560),
        "confirmed",
        id="touching_bookings_never_held_at_same_minute",
    ),
    pytest.param(
        2,
        [("P", 480, 500), ("P", 500, 520), ("P", 520, 540), ("P", 540, 560)],
        (470, 570),
        "confirmed",
        id="chain_of_bookings_holds_one_place_per_minute",
    ),
    pytest.param(1, [("P", 600, 601)], (480, 720), "pool_full", id="full_for_one_minute_inside"),
    pytest.param(1, [("P", 1439, 1440)], (1400, 1440), "pool_full", id="full_at_last_minute_of_day"),
    pytest.param(1, [("P", 0, 1)], (0, 60), "pool_full", id="full_at_first_minute_of_day"),
    pytest.param(2, [("P", 480, 540)], (480, 540), "confirmed", id="second_place_free"),
    pytest.param(
        2, [("P", 480, 540), ("P", 500, 560)], (530, 535), "pool_full", id="capacity_reached"
    ),
    pytest.param(1, [("Q", 480, 540)], (480, 540), "confirmed", id="other_pool_holds_not_counted"),
    pytest.param(0, [], (480, 540), "pool_full", id="capacity_zero"),
]


@pytest.mark.parametrize("capacity, existing, period, expected", MINUTE_SCENARIOS)
def test_RS_2_5_holds_for_any_minute_never_exceed_capacity(capacity, existing, period, expected):
    """RS.2.5: the holds for any minute never exceed the approved capacity (C.5.3: a free place for
    every minute of the booked period). Periods are half-open [start, end), so back-to-back
    bookings do not overlap, and capacity counts the places held at the same minute rather than
    every booking that touches the period."""
    rules = make_rules({"P": capacity, "Q": 1})
    ledger = CapacityLedger()
    for index, (pool_id, start, end) in enumerate(existing):
        assert_confirmed(
            commit(make_request("existing-%d" % index, pool_id, start, end), rules, ledger),
            "setup booking %d" % index,
        )
    before = canonical(ledger.records())

    new = make_request("new", "P", period[0], period[1])
    result = commit(new, rules, ledger)
    if expected == "confirmed":
        assert_confirmed(result, "new booking %r" % (period,))
        assert len(ledger.records()) == len(existing) + 1
    else:
        assert_refused(result, expected, "new booking %r" % (period,))
        assert canonical(ledger.records()) == before, "a refused booking changed the records"
    assert_capacity_respected(ledger.records(), {"P": capacity, "Q": 1})


def test_RS_2_5_concurrent_overlapping_periods_never_exceed_capacity_at_any_minute():
    """RS.2.5: serialize holds per pool so the holds for any minute never exceed the approved
    capacity, with at least 100 requests at once. 100 requests with different overlapping periods
    are released together; afterwards no minute is overbooked, every confirmation is saved once,
    and every pool_full refusal is backed by a minute of its period that is in fact full."""
    capacity = 3
    rng = random.Random(25)
    for round_no in range(SHORT_ROUNDS):
        context = "round %d" % round_no
        ledger = CapacityLedger()
        rules = make_rules({"P": capacity})
        requests = []
        for i in range(CONCURRENT_REQUESTS):
            start = rng.randrange(420, 720, 5)
            end = min(MINUTES_PER_DAY, start + rng.choice((15, 30, 45, 60, 90, 120)))
            requests.append(make_request("mix-%d-%d" % (round_no, i), "P", start, end))
        results = concurrent_commits(requests, rules, ledger)

        records = ledger.records()
        assert_capacity_respected(records, {"P": capacity}, context)
        assert_unique_ids(records, context)
        confirmed = [io8 for io8, _, _ in results if io8 is not None]
        assert canonical(records) == canonical(confirmed), (
            "%s: saved records differ from the confirmations returned" % context
        )
        counts = holds_per_minute(records, "P")
        for request, (io8, _, io22) in zip(requests, results):
            if io8 is None:
                assert io22["reason"] == "pool_full", (context, io22)
                assert max(counts[request["start"]:request["end"]]) == capacity, (
                    "%s: %s refused as pool_full but its period had a free place every minute"
                    % (context, request["request_id"])
                )


def test_RS_2_5_concurrent_requests_on_two_pools_hold_each_pool_separately():
    """RS.2.5: capacity holds are serialized for each pool. Two pools each have one free place
    left and 100 requests split across them arrive at once; each pool's last place goes to
    exactly one request, and neither pool's holds count against the other."""
    capacities = {"P": 2, "Q": 3}
    for round_no in range(SHORT_ROUNDS):
        context = "round %d" % round_no
        ledger = CapacityLedger()
        rules = make_rules(capacities)
        for pool_id, capacity in capacities.items():
            for k in range(capacity - 1):
                assert_confirmed(
                    commit(make_request("pre-%s-%d" % (pool_id, k), pool_id, 600, 660), rules, ledger)
                )
        requests = [
            make_request("two-%d-%d" % (round_no, i), "P" if i % 2 == 0 else "Q", 600, 660)
            for i in range(CONCURRENT_REQUESTS)
        ]
        results = concurrent_commits(requests, rules, ledger)

        for pool_id in capacities:
            wins = [io8 for io8, _, _ in results if io8 is not None and io8["pool_id"] == pool_id]
            assert len(wins) == 1, "%s: pool %s gave %d confirmations for its last place" % (
                context,
                pool_id,
                len(wins),
            )
        for io8, _, io22 in results:
            if io8 is None:
                assert io22["reason"] == "pool_full", (context, io22)
        records = ledger.records()
        assert len(records) == sum(capacities.values()), context
        assert_unique_ids(records, context)
        assert_capacity_respected(records, capacities, context)


def test_RS_2_5_concurrent_repeated_request_ids_keep_one_reservation_per_request_id():
    """RS.2.5: keep at most one reservation per request ID, with at least 100 requests at once.
    20 request IDs, each sent 5 times, compete for 3 places at once: exactly 3 request IDs are
    saved, each once; every copy of a saved ID gets the saved reservation and every copy of an
    unsaved ID is refused as pool_full."""
    capacity = 3
    distinct_ids, copies = 20, 5
    rng = random.Random(55)
    for round_no in range(SHORT_ROUNDS):
        context = "round %d" % round_no
        ledger = CapacityLedger()
        rules = make_rules({"P": capacity})
        base = [make_request("rep-%d-%d" % (round_no, i), "P", 480, 540) for i in range(distinct_ids)]
        requests = [request for request in base for _ in range(copies)]
        rng.shuffle(requests)
        assert len(requests) == CONCURRENT_REQUESTS
        results = concurrent_commits(requests, rules, ledger)

        records = ledger.records()
        assert len(records) == capacity, "%s: %d records for capacity %d" % (
            context,
            len(records),
            capacity,
        )
        assert_unique_ids(records, context)
        saved = {record["request_id"]: record for record in records}
        for request, (io8, _, io22) in zip(requests, results):
            request_id = request["request_id"]
            if request_id in saved:
                assert io8 == saved[request_id], (
                    "%s: a copy of saved %s did not get the saved reservation: %r"
                    % (context, request_id, io22 if io8 is None else io8)
                )
            else:
                assert io8 is None and io22["reason"] == "pool_full", (context, request_id, io8)


# ---------------------------------------------------------------------------------------------
# RS.1.1.3 and RS.2.2: decisions follow the rule set passed in on the call
# ---------------------------------------------------------------------------------------------


@pytest.mark.parametrize("change", ["capacity_raised", "capacity_lowered_then_raised"])
def test_RS_1_1_3_decision_uses_capacity_from_rule_set_passed_on_the_call(change):
    """RS.1.1.3: accept Approved Parking Rules and Capacity (IO.17); MOP: booking decisions made
    under the latest rule version (100%); verification: publish a new rule version and book; the
    decision follows the new version. Each call is decided under the capacity in the IO.17 passed
    on that call, whether the new version raises or lowers it."""
    ledger = CapacityLedger()
    if change == "capacity_raised":
        v1 = make_rules({"P": 1}, version=1)
        assert_confirmed(commit(make_request("a", "P"), v1, ledger), "v1, first place")
        assert_refused(commit(make_request("b", "P"), v1, ledger), "pool_full", "v1 is full")
        v2 = make_rules({"P": 2}, version=2)
        assert_confirmed(commit(make_request("b", "P"), v2, ledger), "v2 raised capacity to 2")
        assert_refused(commit(make_request("c", "P"), v2, ledger), "pool_full", "v2 is full")
        assert sorted(r["request_id"] for r in ledger.records()) == ["a", "b"]
    else:
        v1 = make_rules({"P": 2}, version=1)
        assert_confirmed(commit(make_request("a", "P"), v1, ledger), "v1, first place")
        v2 = make_rules({"P": 1}, version=2)
        assert_refused(
            commit(make_request("b", "P"), v2, ledger), "pool_full", "v2 lowered capacity to 1"
        )
        v3 = make_rules({"P": 2}, version=3)
        assert_confirmed(commit(make_request("b", "P"), v3, ledger), "v3 raised capacity to 2")
        assert sorted(r["request_id"] for r in ledger.records()) == ["a", "b"]
    assert_capacity_respected(ledger.records(), {"P": 2})


def test_RS_2_2_newly_published_rule_set_applies_to_the_next_attempt():
    """RS.2.2: apply a newly published rule set to every booking attempt received more than 10 s
    after publication. C.5.3 receives IO.17 as the control of each call, so the first attempt
    made with a new version already follows it: a newly published pool becomes bookable, a newly
    published capacity takes effect, and a pool left out of the new set is refused (RS.2.3)."""
    ledger = CapacityLedger()
    v1 = make_rules({"P": 1}, version=1)
    assert_confirmed(commit(make_request("a", "P"), v1, ledger), "v1")
    assert_refused(commit(make_request("b", "Q"), v1, ledger), "missing_data", "Q not in v1")

    v2 = make_rules({"P": 1, "Q": 1}, version=2)
    assert_confirmed(commit(make_request("b", "Q"), v2, ledger), "v2 published Q")
    assert_refused(commit(make_request("c", "P"), v2, ledger), "pool_full", "P still capacity 1")

    v3 = make_rules({"P": 2, "Q": 1}, version=3)
    assert_confirmed(commit(make_request("c", "P"), v3, ledger), "v3 raised P to 2")

    v4 = make_rules({"P": 2}, version=4)
    assert_refused(commit(make_request("d", "Q"), v4, ledger), "missing_data", "Q not in v4")
    assert sorted(r["request_id"] for r in ledger.records()) == ["a", "b", "c"]


# ---------------------------------------------------------------------------------------------
# RS.1.2.1 and RS.1.2.3: outputs
# ---------------------------------------------------------------------------------------------


def test_RS_1_2_1_confirmed_record_is_exactly_the_saved_record():
    """RS.1.2.1: provide Confirmed Reservation Record (IO.8); MOP: confirmations that match a saved
    record (100%); verification: compare every confirmation in a test run with the saved records.
    Each IO.8 carries the request's fields with status confirmed and equals exactly one saved
    record, including the IO.8 returned for a repeated request ID."""
    rules = make_rules({"P": 2, "Q": 1})
    ledger = CapacityLedger()

    first = make_request("conf-a", "P", 480, 540, driver_id="drv-1")
    io8, io18, _ = commit(first, rules, ledger)
    assert io8 is not None
    assert {key: io8[key] for key in REQUEST_FIELDS} == first
    assert io8["status"] == "confirmed"
    assert records_for(ledger, "conf-a") == [io8]
    assert [record for record in io18 if record["request_id"] == "conf-a"] == [io8]

    confirmations = [io8]
    rng = random.Random(121)
    for i in range(30):
        start = rng.randrange(420, 900, 10)
        request = make_request("conf-%d" % i, rng.choice(("P", "Q")), start, start + rng.choice((30, 60)))
        result_io8 = commit(request, rules, ledger)[0]
        if result_io8 is not None:
            assert {key: result_io8[key] for key in REQUEST_FIELDS} == request
            confirmations.append(result_io8)
    assert commit(first, rules, ledger)[0] == io8, "the repeat must return the saved IO.8"

    saved = ledger.records()
    assert len(confirmations) > 1
    for confirmation in confirmations:
        matches = [record for record in saved if record["reservation_id"] == confirmation["reservation_id"]]
        assert matches == [confirmation], "confirmation %r does not match exactly one saved record" % (
            confirmation,
        )


def test_RS_1_2_3_records_contain_every_saved_reservation_and_nothing_refused():
    """RS.1.2.3: provide Reservation Records (IO.18); MOP: saved reservations missing from options
    or reports (0). After every call, the IO.18 returned and ledger.records() hold every saved
    reservation and no record for a refused request."""
    rules = make_rules({"P": 1, "Q": 2})
    ledger = CapacityLedger()
    steps = [
        (make_request("s1", "P", 480, 540), rules),
        (make_request("s2", "P", 500, 520), rules),  # pool_full
        (make_request("s3", "Q", 480, 540), rules),
        (make_request("s4", "GONE", 480, 540), rules),  # missing_data
        (make_request("s1", "P", 480, 540), rules),  # repeat of a saved request ID
        (make_request("s5", "P", 540, 600), rules),
        (make_request("s6", "Q", 480, 540), rules),
        (make_request("s7", "Q", 530, 545), rules),  # pool_full
    ]
    confirmed_ids, refused_ids = set(), set()
    for request, step_rules in steps:
        io8, io18, io22 = commit(request, step_rules, ledger)
        (confirmed_ids if io8 is not None else refused_ids).add(request["request_id"])
        records = ledger.records()
        assert canonical(io18) == canonical(records), (
            "IO.18 after %s differs from ledger.records()" % request["request_id"]
        )
        assert {record["request_id"] for record in records} == confirmed_ids
        assert len(records) == len(confirmed_ids)
        if io8 is not None:
            assert io8 in io18
    assert confirmed_ids == {"s1", "s3", "s5", "s6"}
    assert refused_ids == {"s2", "s4", "s7"}


# ---------------------------------------------------------------------------------------------
# RS.2.1 Limited Personal Data
# ---------------------------------------------------------------------------------------------

EXTRA_PERSONAL_FIELDS = {
    "driver_name": "Alex Placeholder",
    "email": "alex.placeholder@example.edu",
    "licence_plate": "ZZZ0000",
    "phone": "000-000-0000",
}


@pytest.mark.parametrize(
    "extra",
    [{}, EXTRA_PERSONAL_FIELDS],
    ids=["contract_fields_only", "request_carries_extra_personal_fields"],
)
def test_RS_2_1_saved_record_has_only_the_approved_fields(extra):
    """RS.2.1: store only the reservation ID, request ID, identity reference, pool, booked period
    and status for each reservation; verification: schema inspection and an export of a test run
    show no other field. Every record in IO.8, IO.18 and ledger.records() has exactly the fields
    reservation_id, request_id, driver_id, pool_id, start, end and status, even when the incoming
    request carries extra personal data."""
    rules = make_rules({"P": 2})
    ledger = CapacityLedger()
    request = dict(make_request("pd-1", "P", 480, 540), **extra)
    io8, io18, _ = commit(request, rules, ledger)
    assert io8 is not None
    repeat_io8 = commit(request, rules, ledger)[0]
    later_io18 = commit(make_request("pd-2", "P", 600, 660), rules, ledger)[1]

    for record in [io8, repeat_io8] + io18 + later_io18 + ledger.records():
        assert set(record) == RECORD_FIELDS, "record has fields %s" % sorted(record)
    export = json.dumps(ledger.records(), default=repr)
    for value in extra.values():
        assert value not in export, "personal data %r was stored" % value


# ---------------------------------------------------------------------------------------------
# RS.2.3 Safe Handling of Source Failures
# ---------------------------------------------------------------------------------------------


def _broken_rules(case):
    """IO.17 in which the capacity data for pool P are missing, unknown or invalid."""
    if case == "rule_set_missing":
        return None
    if case == "pools_key_missing":
        return {"version": 2}
    rules = make_rules({"OK": 5, "P": 1}, version=2)
    if case == "pool_absent":
        del rules["pools"]["P"]
    elif case == "no_pools_published":
        rules["pools"] = {}
    elif case == "pool_rule_null":
        rules["pools"]["P"] = None
    elif case == "capacity_key_missing":
        del rules["pools"]["P"]["capacity"]
    elif case == "capacity_null":
        rules["pools"]["P"]["capacity"] = None
    elif case == "capacity_text":
        rules["pools"]["P"]["capacity"] = "1"
    elif case == "capacity_fraction":
        rules["pools"]["P"]["capacity"] = 1.5
    elif case == "capacity_negative":
        rules["pools"]["P"]["capacity"] = -1
    else:
        raise ValueError(case)
    return rules


MISSING_CAPACITY_CASES = [
    pytest.param("rule_set_missing", {"missing_data"}, id="rule_set_missing"),
    pytest.param("pools_key_missing", {"missing_data"}, id="pools_key_missing"),
    pytest.param("pool_absent", {"missing_data"}, id="pool_absent_from_rules"),
    pytest.param("no_pools_published", {"missing_data"}, id="no_pools_published"),
    pytest.param("pool_rule_null", {"missing_data"}, id="pool_rule_null"),
    pytest.param("capacity_key_missing", {"missing_data"}, id="capacity_missing"),
    pytest.param("capacity_null", {"missing_data"}, id="capacity_null"),
    pytest.param("capacity_text", {"missing_data"}, id="capacity_not_int_text"),
    pytest.param("capacity_fraction", {"missing_data"}, id="capacity_not_int_fraction"),
    # A negative capacity breaks PoolRule (minimum 0); the specification does not say which
    # reason it gives, only that nothing may be confirmed.
    pytest.param("capacity_negative", {"missing_data", "pool_full"}, id="capacity_negative"),
]


@pytest.mark.parametrize("case, allowed_reasons", MISSING_CAPACITY_CASES)
def test_RS_2_3_missing_or_unknown_capacity_is_refused_without_record_or_hold(case, allowed_reasons):
    """RS.2.3: refuse confirmation whenever the capacity data for any part of the booked period
    are missing, failed or unknown; verification: fault injection on capacity during booking,
    every case refused with no record. The refusal reason is missing_data, the saved records do
    not change, and no place is held: the pool's single place is still free afterwards."""
    ledger = CapacityLedger()
    good_rules = make_rules({"OK": 5, "P": 1}, version=1)
    assert_confirmed(commit(make_request("kept", "OK", 480, 540), good_rules, ledger), "setup")
    before = canonical(ledger.records())

    request = make_request("faulty", "P", 480, 540)
    io8, io18, io22 = commit(request, _broken_rules(case), ledger)
    assert io8 is None, "booking confirmed although the capacity data were %s" % case
    assert io22["reason"] in allowed_reasons, io22
    assert canonical(ledger.records()) == before, "a refused booking changed the records"
    assert canonical(io18) == before
    assert records_for(ledger, "faulty") == []

    assert_confirmed(
        commit(make_request("probe", "P", 480, 540), good_rules, ledger),
        "the refused booking must not hold P's only place",
    )


# ---------------------------------------------------------------------------------------------
# RS.2.4 Booking Response Time
# ---------------------------------------------------------------------------------------------


def test_RS_2_4_booking_call_returns_within_2_seconds_at_95th_percentile():
    """RS.2.4: return a confirmed record or a refusal within 2 seconds for at least 95% of booking
    attempts; verification: timed booking calls, 95th percentile 2 s or less. Measured in-process
    on a ledger already holding a few hundred reservations, over 200 sequential calls mixing
    confirmations, refusals and repeats, plus one burst of 100 calls arriving at once."""
    rng = random.Random(24)
    capacities = {"P1": 40, "P2": 40, "P3": 4}
    rules = make_rules(capacities)
    ledger = CapacityLedger()

    def random_request(request_id):
        start = rng.randrange(360, 1200, 5)
        end = min(MINUTES_PER_DAY, start + rng.choice((30, 60, 120, 240)))
        return make_request(request_id, rng.choice(sorted(capacities)), start, end)

    loaded = [random_request("load-%d" % i) for i in range(300)]
    for request in loaded:
        commit(request, rules, ledger)

    sequential_calls = 200
    allowed_slow = sequential_calls - int(math.ceil(RESPONSE_PERCENTILE * sequential_calls))
    durations, slow = [], 0
    for i in range(sequential_calls):
        if i % 10 == 8:
            request = make_request("timed-gone-%d" % i, "GONE", 480, 540)
        elif i % 10 == 9:
            request = loaded[i]  # the same request again: a repeat, or a refusal again
        else:
            request = random_request("timed-%d" % i)
        began = time.perf_counter()
        result = commit_capacity_hold(dict(request), approved_rules=rules, ledger=ledger)
        elapsed = time.perf_counter() - began
        assert_result_shape(result, request)
        durations.append(elapsed)
        if elapsed > RESPONSE_LIMIT_S:
            slow += 1
            assert slow <= allowed_slow, "more than 5%% of %d calls already took over %.1f s" % (
                sequential_calls,
                RESPONSE_LIMIT_S,
            )

    def timed(request):
        began = time.perf_counter()
        result = commit_capacity_hold(dict(request), approved_rules=rules, ledger=ledger)
        elapsed = time.perf_counter() - began
        assert_result_shape(result, request)
        return elapsed

    burst = [random_request("burst-%d" % i) for i in range(CONCURRENT_REQUESTS)]
    durations.extend(run_at_once([functools.partial(timed, request) for request in burst]))

    durations.sort()
    p95 = durations[int(math.ceil(RESPONSE_PERCENTILE * len(durations))) - 1]
    assert p95 <= RESPONSE_LIMIT_S, "95th percentile booking time %.3f s exceeds %.1f s" % (
        p95,
        RESPONSE_LIMIT_S,
    )


# ---------------------------------------------------------------------------------------------
# RS.2.6 Internal Interface Contract (IO.8, IO.18) and the commitCapacityHold operation (IO.22)
# ---------------------------------------------------------------------------------------------


def test_RS_2_6_outputs_follow_commitCapacityHold_contract():
    """RS.2.6: produce IO.8 and IO.18 only in the forms the internal interface contract defines;
    the commitCapacityHold operation (contract 1.1) adds IO.22. Every call returns
    (IO.8 or None, IO.18, IO.22 or None) with exactly one of IO.8 and IO.22 set, IO.18 a list of
    ConfirmedReservationRecord, and a pool_full refusal carrying reason pool_full and the
    request_id."""
    rules = make_rules({"P": 1})
    ledger = CapacityLedger()

    first = make_request("shape-1", "P", 480, 540)
    io8, io18, io22 = commit(first, rules, ledger)
    assert io8 is not None and io22 is None
    assert isinstance(io18, list) and io8 in io18

    repeat = commit(first, rules, ledger)
    assert repeat[0] is not None and repeat[2] is None

    full = make_request("shape-2", "P", 500, 560)
    io8, io18, io22 = commit(full, rules, ledger)
    assert io8 is None and io22 is not None
    assert io22["reason"] == "pool_full"
    assert io22["request_id"] == "shape-2"
    assert isinstance(io18, list)

    missing = make_request("shape-3", "GONE", 480, 540)
    io8, io18, io22 = commit(missing, rules, ledger)
    assert io8 is None and io22 is not None
    assert io22["reason"] == "missing_data"
    assert isinstance(io18, list)

    records = ledger.records()
    assert isinstance(records, list)
    for record in records:
        assert_record_fields(record)
