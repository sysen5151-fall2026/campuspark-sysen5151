"""Tests for SR.6 Future Booking Cancellation.

SR.6: CampusPark shall release the capacity held by a future reservation when the driver cancels
that reservation. The first test runs the SPEC acceptance criterion against the product code: 20
cases with varied future start times and partial overlaps, recording the places held before the
booking, after it and after the cancellation. A booking that has already started is checked on its
own, because SR.6 covers future bookings only.

The Chapter 3 placeholder test_N4_SR6_future_booking_cancellation in tests/test_spec_acceptance.py
stays red with the rest of that suite, which waits for stakeholder evidence.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from api import service
from api.main import app
from data.reservation_db import SqliteReservationStore
from functions.cancel_future_reservation import cancel_future_reservation
from functions.f5_recheck_and_record_reservation import recheck_and_record_reservation

POOL = "P-NORTH"
DAY = 24 * 60


def rules(capacity):
    return {"version": 1, "pools": {POOL: {"name": "North Lot", "capacity": capacity,
                                           "permits": ["student"], "closures": []}}}


def book(store, request_id, driver_id, start, end, capacity=10):
    request = {"request_id": request_id, "driver_id": driver_id, "pool_id": POOL,
               "start": start, "end": end}
    eligibility = {"driver_id": driver_id, "status": "eligible", "permit": "student"}
    return recheck_and_record_reservation(request, eligibility=eligibility,
                                          approved_rules=rules(capacity), reservation_store=store)


def cancel(store, reservation_id, driver_id, now):
    return cancel_future_reservation({"reservation_id": reservation_id, "driver_id": driver_id},
                                     now=now, reservation_store=store)


def held(store):
    """Places held in the pool at every minute of the day, from confirmed records only."""
    minutes = [0] * DAY
    for r in store.all():
        if r["pool_id"] == POOL and r["status"] == "confirmed":
            for m in range(r["start"], r["end"]):
                minutes[m] += 1
    return minutes


@pytest.mark.parametrize("case", range(20))
def test_SR_6_cancelling_a_future_booking_releases_its_places_for_the_whole_period(case):
    """SR.6 Future Booking Cancellation [cancel_future_reservation, C.5 Reservation Subsystem]

    Passes when, in each of 20 cases with a different future start and length and two other
    bookings that partly overlap it, the cancelled booking's places come back for exactly its
    period, a new request for that period gets the released place in a pool that was full, and a
    second cancellation releases nothing more.
    """
    store = SqliteReservationStore(":memory:")
    start = 8 * 60 + case * 30
    end = start + 60 + (case % 4) * 30
    now = start - 15 - case

    # One booking that ends inside the period and one that starts inside it.
    assert book(store, "early", "student02", start - 45, start + 30)[0] is not None
    assert book(store, "late", "student03", end - 30, end + 60)[0] is not None
    before = held(store)

    record, refusal, _ = book(store, "mine", "student01", start, end)
    assert refusal is None
    after_booking = held(store)
    assert all(after_booking[m] == before[m] + (1 if start <= m < end else 0) for m in range(DAY))

    # With capacity at the peak, the pool is full for this period while the booking stands.
    full = max(after_booking[start:end])
    _, refusal, _ = book(store, "waiting-1", "student04", start, end, capacity=full)
    assert refusal["reason"] == "pool_full"

    cancelled, refusal, records = cancel(store, record["reservation_id"], "student01", now)
    assert refusal is None and cancelled["status"] == "cancelled"
    assert held(store) == before
    assert len(records) == 3 and all(r["status"] == "confirmed" for r in records
                                     if r["reservation_id"] != record["reservation_id"])

    again, refusal, _ = cancel(store, record["reservation_id"], "student01", now + 1)
    assert refusal is None and again == cancelled
    assert held(store) == before

    taken, refusal, _ = book(store, "waiting-2", "student04", start, end, capacity=full)
    assert refusal is None and taken["status"] == "confirmed"


@pytest.mark.parametrize("minutes_after_start", [0, 1, 45])
def test_SR_6_a_booking_that_has_started_is_not_cancelled(minutes_after_start):
    store = SqliteReservationStore(":memory:")
    record, _, _ = book(store, "mine", "student01", 600, 720)
    before = held(store)

    cancelled, refusal, _ = cancel(store, record["reservation_id"], "student01",
                                   600 + minutes_after_start)
    assert cancelled is None and refusal["reason"] == "already_started"
    assert store.all()[0]["status"] == "confirmed" and held(store) == before


def test_SR_6_only_the_driver_who_booked_can_cancel_and_bad_requests_change_nothing():
    store = SqliteReservationStore(":memory:")
    record, _, _ = book(store, "mine", "student01", 600, 720)
    before = store.all()

    for request, reason in [
        ({"reservation_id": record["reservation_id"], "driver_id": "student02"}, "not_found"),
        ({"reservation_id": "RES-99999", "driver_id": "student01"}, "not_found"),
        ({"reservation_id": "", "driver_id": "student01"}, "missing_data"),
        ({"reservation_id": record["reservation_id"]}, "missing_data"),
        (None, "missing_data"),
    ]:
        cancelled, refusal, _ = cancel_future_reservation(request, now=480, reservation_store=store)
        assert cancelled is None and refusal["reason"] == reason
        assert isinstance(refusal["message"], str) and refusal["message"]
    assert store.all() == before


def test_SR_6_cancel_route_releases_the_place_shown_to_the_next_driver(monkeypatch):
    service.reset(":memory:")
    monkeypatch.setattr(service, "minutes_now", lambda: 8 * 60)
    client = TestClient(app)
    trip = {"driver_id": "student01", "destination": "Duffield Hall", "arrival": "09:00", "hours": 2}

    def remaining():
        options = client.post("/api/options", json=trip).json()["options"]
        return {o["lot_id"]: o["remaining"] for o in options}["forest-home"]

    free = remaining()
    booked = client.post("/api/reserve", json={**trip, "lot_id": "forest-home"}).json()
    number = booked["confirmation"]
    assert booked["status"] == "confirmed" and remaining() == free - 1

    refused = client.post(f"/api/reservations/{number}/cancel", json={"driver_id": "student02"}).json()
    assert refused["reason"] == "not_found" and remaining() == free - 1

    done = client.post(f"/api/reservations/{number}/cancel", json={"driver_id": "student01"}).json()
    assert done["status"] == "cancelled" and done["confirmation"] == number
    assert remaining() == free
    shown = client.get(f"/api/reservations/{number}", params={"driver_id": "student01"}).json()
    assert shown["status"] == "cancelled"

    again = client.post(f"/api/reservations/{number}/cancel", json={"driver_id": "student01"}).json()
    assert again["status"] == "cancelled" and remaining() == free

    monkeypatch.setattr(service, "minutes_now", lambda: 9 * 60 + 5)
    later = client.post("/api/reserve", json={**trip, "lot_id": "forest-home"}).json()
    started = client.post(f"/api/reservations/{later['confirmation']}/cancel",
                          json={"driver_id": "student01"}).json()
    assert started["reason"] == "already_started"
    service.reset(":memory:")


def test_SR_6_a_database_made_before_cancellation_is_upgraded_and_keeps_its_rows(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript("""
        CREATE TABLE reservations (
            reservation_id TEXT PRIMARY KEY, request_id TEXT NOT NULL UNIQUE, driver_id TEXT NOT NULL,
            pool_id TEXT NOT NULL, start INTEGER NOT NULL, "end" INTEGER NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('confirmed')));
        INSERT INTO reservations VALUES ('RES-00001', 'a', 'student01', 'P-NORTH', 600, 720, 'confirmed');
        INSERT INTO reservations VALUES ('RES-00002', 'b', 'student02', 'P-NORTH', 540, 600, 'confirmed');
    """)
    old.close()

    store = SqliteReservationStore(path)
    assert [r["reservation_id"] for r in store.all()] == ["RES-00001", "RES-00002"]
    cancelled, refusal, _ = cancel(store, "RES-00001", "student01", 480)
    assert refusal is None and cancelled["status"] == "cancelled"
    assert book(store, "c", "student03", 600, 660)[0]["reservation_id"] == "RES-00003"
    store.close()
