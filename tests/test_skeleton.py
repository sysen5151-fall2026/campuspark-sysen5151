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

from api import reservations
from api.main import app
from integrations.map import client as map_client
from integrations.permit import client as permit_client

client = TestClient(app)


@pytest.fixture(autouse=True)
def empty_store():
    reservations._RESERVATIONS.clear()
    yield
    reservations._RESERVATIONS.clear()


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
    assert reservations.all_reservations() == []


def test_blank_id_no_longer_borrows_student_rights():
    assert permit_client.validate("") is None
    assert permit_client.validate(None) is None


def test_recheck_blocks_a_lot_the_permit_does_not_cover():
    r = client.post("/api/reserve", json=trip(lot_id="visitor-garage"))
    assert r.json()["error"] == "Your permit no longer covers that lot."
    assert reservations.all_reservations() == []


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
    lots = [
        {"id": "a", "name": "A", "capacity": 5, "walk_minutes": None},
        {"id": "b", "name": "B", "capacity": 5, "walk_minutes": 20},
    ]
    from api import ranking
    assert [l["id"] for l in ranking.rank(lots, "x", 540, 600)] == ["b", "a"]


def test_route_text_says_when_walk_time_is_missing():
    lot = {"name": "A Lot", "walk_minutes": None}
    assert "don't have a walk time" in map_client.route_to(lot, "Somewhere")


# Capacity over time (SR.4) ------------------------------------------------
# Small made-up lots so a full pool is easy to reach.

ONE = {"id": "one", "name": "One place", "capacity": 1}
TWO = {"id": "two", "name": "Two places", "capacity": 2}
DRIVER = {"driver_id": "student01"}


def book(lot, start, end):
    return reservations.reserve(DRIVER, lot, "Duffield Hall", start, end)


def test_overlapping_booking_is_refused_when_pool_is_full():
    assert book(ONE, 540, 660)            # 09:00-11:00
    assert book(ONE, 600, 720) is None    # 10:00-12:00 overlaps


def test_back_to_back_bookings_do_not_overlap():
    assert book(ONE, 540, 600)            # 09:00-10:00
    assert book(ONE, 600, 660)            # 10:00-11:00 starts as the first ends


def test_capacity_counts_places_held_at_the_same_time_not_every_touching_booking():
    assert book(TWO, 540, 600)            # 09-10
    assert book(TWO, 600, 660)            # 10-11
    assert book(TWO, 540, 660)            # 09-11: never more than 2 at once
    assert book(TWO, 570, 630) is None    # 09:30-10:30: two already held then


def test_bookings_in_other_lots_do_not_count():
    assert book(ONE, 540, 660)
    assert reservations.remaining_capacity(TWO, 540, 660) == 2


def test_full_lot_drops_out_of_the_options():
    lot = map_client.lots_near("Duffield Hall")[2]   # forest-home, 15 places
    assert lot["id"] == "forest-home"
    for _ in range(lot["capacity"]):
        assert book(lot, 540, 660)
    r = client.post("/api/options", json=trip())
    assert "forest-home" not in lot_ids(r)
    refused = client.post("/api/reserve", json=trip(lot_id="forest-home")).json()
    assert "filled up" in refused["error"]


def test_clock_labels():
    assert reservations.clock(540) == "09:00"
    assert reservations.clock(1500) == "01:00 next day"
