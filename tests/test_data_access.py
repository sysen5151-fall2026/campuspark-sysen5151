"""The SQLite data access component behind F.5 (Chapter 8).

F.5 must make the same decisions on the database store as on the in-memory store, and the table
must hold only the fields RS.2.1 allows.
"""
import sqlite3

import pytest

from data.reservation_db import FIELDS, SqliteReservationStore
from functions.f5_recheck_and_record_reservation import ReservationStore, recheck_and_record_reservation

RULES = {"version": 1, "pools": {"P1": {"name": "North Lot", "capacity": 1, "permits": ["student"],
                                        "closures": []}}}
ELIGIBLE = {"driver_id": "student01", "status": "eligible", "permit": "student"}


def request(request_id, start=540, end=660, pool_id="P1"):
    return {"request_id": request_id, "driver_id": "student01", "pool_id": pool_id, "start": start, "end": end}


def book(store, req):
    return recheck_and_record_reservation(req, eligibility=ELIGIBLE, approved_rules=RULES, reservation_store=store)


def test_table_holds_only_the_fields_rs_2_1_allows(tmp_path):
    SqliteReservationStore(tmp_path / "r.db").close()
    columns = [row[1] for row in sqlite3.connect(str(tmp_path / "r.db")).execute("PRAGMA table_info(reservations)")]
    assert tuple(columns) == FIELDS == ("reservation_id", "request_id", "driver_id", "pool_id", "start", "end", "status")


def test_f5_decides_the_same_on_both_stores():
    script = [request("a"), request("a"), request("b"), request("c", start=660, end=720),
              request("d", pool_id="P9"), request("e", start=600, end=630)]
    results = []
    for store in (ReservationStore(), SqliteReservationStore()):
        results.append([book(store, r) for r in script] + [store.all()])
    assert results[0] == results[1]
    confirmed, refusal, records = results[1][2]
    assert confirmed is None and refusal["reason"] == "pool_full"


def test_repeated_request_id_adds_no_second_row():
    store = SqliteReservationStore()
    first, _, _ = book(store, request("a"))
    again, refusal, records = book(store, request("a"))
    assert again == first and refusal is None and len(records) == 1


def test_records_survive_reopening_the_database(tmp_path):
    path = tmp_path / "r.db"
    store = SqliteReservationStore(path)
    saved, _, _ = book(store, request("a"))
    store.close()
    reopened = SqliteReservationStore(path)
    assert reopened.all() == [saved]
    _, refusal, _ = book(reopened, request("b"))
    assert refusal["reason"] == "pool_full"


def test_database_rejects_a_second_record_for_the_same_request_id():
    store = SqliteReservationStore()
    store.save(request("a"))
    with pytest.raises(sqlite3.IntegrityError):
        store.save(request("a"))
