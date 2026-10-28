"""Developer tests for the walking skeleton.

These are NOT the Chapter 3 acceptance tests. Those live in
test_spec_acceptance.py, stay red, and need owner-reviewed cases or real users
before any of them can pass. The tests here only check that the skeleton code
does what its own docstrings say, so a later change can't quietly break UC.1.

Where a test is about a behaviour some SR cares about, the SR is named so the
link is easy to follow. Passing here is not evidence that the SR is met.
"""

import pytest
from fastapi.testclient import TestClient

from api import service
from api.main import app, order_options
from integrations.map import client as map_client
from integrations.permit import client as permit_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def empty_store():
    # Every test starts from the fixture rules and an empty in-memory reservation database.
    service.reset(":memory:")
    yield
    service.reset(":memory:")


def trip(**overrides):
    body = {"driver_id": "student01", "destination": "Duffield Hall",
            "arrival": "09:00", "hours": 2}
    body.update(overrides)
    return body


def lot_ids(response):
    return [o["lot_id"] for o in response.json()["options"]]


# UC.1 happy path --------------------------------------------------------

def test_home_page_loads():
    r = client.get("/")
    assert r.status_code == 200
    assert "CampusPark" in r.text


def test_student_gets_only_student_lots_nearest_first():
    r = client.post("/api/options", json=trip())
    assert r.status_code == 200
    assert r.json()["permit"] == "student"
    assert lot_ids(r) == ["forest-home", "A-lot"]  # 11 min, then 14 min


def test_different_permits_get_different_lots():
    student = set(lot_ids(client.post("/api/options", json=trip())))
    visitor = set(lot_ids(client.post("/api/options", json=trip(driver_id="visitor01"))))
    assert student and visitor
    assert student.isdisjoint(visitor)


def test_reservation_returns_confirmation_with_booked_period():
    r = client.post("/api/reserve", json=trip(lot_id="forest-home"))
    body = r.json()
    assert "error" not in body
    assert body["lot"] == "Forest Home Drive"
    assert (body["start"], body["end"]) == ("09:00", "11:00")
    assert body["confirmation"]
    assert "do not sense" in body["note"]


def test_booking_lowers_remaining_places():
    before = client.post("/api/options", json=trip()).json()["options"][0]
    client.post("/api/reserve", json=trip(lot_id=before["lot_id"]))
    after = client.post("/api/options", json=trip()).json()["options"][0]
    assert after["remaining"] == before["remaining"] - 1


# Identity and eligibility (SR.2, SR.15) ---------------------------------

@pytest.mark.parametrize("driver_id", ["", "   ", "nobody"])
def test_unconfirmed_identity_gets_no_options(driver_id):
    r = client.post("/api/options", json=trip(driver_id=driver_id))
    assert "error" in r.json()
    assert "options" not in r.json()


@pytest.mark.parametrize("driver_id", ["", "nobody"])
def test_unconfirmed_identity_cannot_book(driver_id):
    r = client.post("/api/reserve", json=trip(driver_id=driver_id, lot_id="forest-home"))
    assert "error" in r.json()
    assert service.records() == []


def test_blank_id_no_longer_borrows_student_rights():
    assert permit_client.validate("") is None
    assert permit_client.validate(None) is None


def test_recheck_blocks_a_lot_the_permit_does_not_cover():
    r = client.post("/api/reserve", json=trip(lot_id="visitor-garage"))
    assert r.json()["error"] == "Your permit no longer covers that lot."
    assert service.records() == []


def test_unknown_lot_is_refused():
    r = client.post("/api/reserve", json=trip(lot_id="no-such-lot"))
    assert "error" in r.json()


# Request validation -------------------------------------------------------

@pytest.mark.parametrize("field", ["driver_id", "destination", "arrival", "hours"])
def test_missing_field_is_rejected_instead_of_filled_in(field):
    body = trip()
    del body[field]
    assert client.post("/api/options", json=body).status_code == 422


@pytest.mark.parametrize("arrival", ["9am", "25:00", "09:60", "9:00", ""])
def test_bad_arrival_time_is_rejected(arrival):
    assert client.post("/api/options", json=trip(arrival=arrival)).status_code == 422


@pytest.mark.parametrize("hours", [0, -1])
def test_stay_must_end_after_it_starts(hours):
    assert client.post("/api/options", json=trip(hours=hours)).status_code == 422


# Missing facts (SR.3) -----------------------------------------------------

def test_unknown_destination_shows_walk_time_as_unavailable():
    r = client.post("/api/options", json=trip(destination="Somewhere New"))
    options = r.json()["options"]
    assert options
    assert all(o["walk_minutes"] is None for o in options)


def test_lots_without_an_estimate_sort_after_lots_with_one():
    options = [
        {"lot_id": "a", "walk_minutes": None},
        {"lot_id": "b", "walk_minutes": 20},
    ]
    assert [o["lot_id"] for o in order_options(options)] == ["b", "a"]


def test_route_text_says_when_walk_time_is_missing():
    lot = {"name": "A Lot", "walk_minutes": None}
    assert "don't have a walk time" in map_client.route_to(lot, "Somewhere")


# Capacity over time (SR.4) ------------------------------------------------
# Small made-up pools so a full pool is easy to reach. Bookings go through the
# real route, so F.5 and the SQLite store make every decision.

SMALL_POOLS = {
    "one": {"name": "One place", "capacity": 1, "permits": ["student"], "closures": []},
    "two": {"name": "Two places", "capacity": 2, "permits": ["student"], "closures": []},
}


def book(lot_id, arrival, hours):
    body = client.post("/api/reserve", json=trip(lot_id=lot_id, arrival=arrival, hours=hours)).json()
    return "error" not in body


@pytest.fixture
def small_pools():
    service.reset(":memory:", pools=SMALL_POOLS)


def test_overlapping_booking_is_refused_when_pool_is_full(small_pools):
    assert book("one", "09:00", 2)
    assert not book("one", "10:00", 2)    # 10:00-12:00 overlaps


def test_back_to_back_bookings_do_not_overlap(small_pools):
    assert book("one", "09:00", 1)
    assert book("one", "10:00", 1)        # starts as the first ends


def test_capacity_counts_places_held_at_the_same_time_not_every_touching_booking(small_pools):
    assert book("two", "09:00", 1)        # 09-10
    assert book("two", "10:00", 1)        # 10-11
    assert book("two", "09:00", 2)        # 09-11: never more than 2 at once
    assert not book("two", "09:30", 1)    # 09:30-10:30: two already held then


def test_bookings_in_other_lots_do_not_count(small_pools):
    assert book("one", "09:00", 2)
    assert book("two", "09:00", 2)
    assert book("two", "09:00", 2)


def test_full_lot_drops_out_of_the_options():
    capacity = next(lot["capacity"] for lot in map_client.LOTS if lot["id"] == "forest-home")
    for _ in range(capacity):
        assert book("forest-home", "09:00", 2)
    r = client.post("/api/options", json=trip())
    assert "forest-home" not in lot_ids(r)
    refused = client.post("/api/reserve", json=trip(lot_id="forest-home")).json()
    assert "filled up" in refused["error"]


def test_records_survive_a_restart(tmp_path):
    service.reset(str(tmp_path / "r.db"))
    assert book("forest-home", "09:00", 2)
    service.reset(str(tmp_path / "r.db"))
    assert len(service.records()) == 1


def test_stay_past_midnight_is_refused_with_a_reason():
    r = client.post("/api/options", json=trip(arrival="23:00", hours=2)).json()
    assert r["error"] == "Your stay has to end by midnight on the same day."


def test_confirmation_can_be_found_again_only_by_its_driver():
    booked = client.post("/api/reserve", json=trip(lot_id="forest-home")).json()
    again = client.get(f"/api/reservations/{booked['confirmation']}", params={"driver_id": "student01"}).json()
    assert again["lot"] == "Forest Home Drive" and again["confirmation"] == booked["confirmation"]
    other = client.get(f"/api/reservations/{booked['confirmation']}", params={"driver_id": "staff01"}).json()
    assert "error" in other


def test_repeated_request_id_books_once():
    body = trip(lot_id="forest-home", request_id="attempt-1")
    first = client.post("/api/reserve", json=body).json()
    second = client.post("/api/reserve", json=body).json()
    assert first["confirmation"] == second["confirmation"]
    assert len(service.records()) == 1


def test_search_route_guidance_reaches_the_confirmation():
    found = client.post("/api/options", json=trip()).json()
    booked = client.post("/api/reserve", json=trip(lot_id="forest-home", search_id=found["search_id"])).json()
    assert "walk about 11 min" in booked["guidance"] and booked["warning"] is None
    assert booked["address"].startswith("Forest Home Drive")


def test_booking_without_its_search_keeps_the_booking_and_warns():
    booked = client.post("/api/reserve", json=trip(lot_id="forest-home")).json()
    assert booked["guidance"] is None and "confirmed and kept" in booked["warning"]


# Administrator controls (UC.2, SR.8, SR.9, SR.14) -------------------------

def change(**fields):
    body = {"account": "admin01", "pool_id": "forest-home"}
    body.update(fields)
    return client.post("/api/admin/controls", json=body).json()


def test_closure_hides_the_lot_and_lists_affected_bookings():
    booked = client.post("/api/reserve", json=trip(lot_id="forest-home")).json()
    result = change(add_closure={"start": "10:00", "end": "11:00"})
    assert result["accepted"] and result["confirmed_count"] == 1
    assert [a["reservation_id"] for a in result["affected"]] == [booked["confirmation"]]
    assert "forest-home" not in lot_ids(client.post("/api/options", json=trip()))
    assert "closed" in client.post("/api/reserve", json=trip(lot_id="forest-home")).json()["error"]


def test_capacity_change_applies_to_the_next_search():
    assert change(capacity=3)["accepted"]
    option = next(o for o in client.post("/api/options", json=trip()).json()["options"] if o["lot_id"] == "forest-home")
    assert option["capacity"] == 3


def test_unapproved_account_cannot_change_controls():
    result = change(account="student01", capacity=0)
    assert not result["accepted"] and "approved staff" in result["reason"]
    pools = {p["pool_id"]: p for p in client.get("/api/admin/pools").json()["pools"]}
    assert pools["forest-home"]["capacity"] == 15


def test_map_positions_cover_every_lot_and_destination():
    data = client.get("/api/map").json()
    assert {l["pool_id"] for l in data["lots"]} == {lot["id"] for lot in map_client.LOTS}
    assert {d["name"] for d in data["destinations"]} == set(map_client.DESTINATIONS)


def test_clock_labels():
    assert service.clock(540) == "09:00"
    assert service.clock(1440) == "24:00"  # a stay may end at midnight, never after it (F.2)
