"""Walking skeleton for UC.1.

One path, end to end: the driver asks for parking, we check the permit, get
lots from the map service, filter and rank them, the driver picks one, we
re-check and record the reservation, then send back a confirmation.

Both external services are stubs. Run it from the repo root with:
    uvicorn api.main:app --reload
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from api import eligibility, ranking, reservations
from integrations.map import client as map_client
from integrations.permit import client as permit_client

app = FastAPI(title="CampusPark")

INDEX = Path(__file__).resolve().parents[1] / "web" / "index.html"

# Shown next to any capacity number, because the number comes from our own
# booking records. Nothing in this version senses an empty space.
CAPACITY_BASIS = "Bookable places come from our booking records, not from sensors."


class OptionsRequest(BaseModel):
    # No defaults on purpose. A missing field used to be filled in for the
    # driver (student01, 09:00, two hours), which made up trip facts and
    # permit rights nobody had asked for.
    driver_id: str
    destination: str
    arrival: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")  # 24h HH:MM
    hours: int = Field(ge=1)  # end has to come after start; no upper limit is approved yet


class ReserveRequest(OptionsRequest):
    lot_id: str


def window_of(req):
    """Minutes since midnight for the start and end of the requested stay."""
    h, m = req.arrival.split(":")
    start = int(h) * 60 + int(m)
    return start, start + req.hours * 60


@app.get("/")
def home():
    return FileResponse(INDEX)


@app.get("/api/destinations")
def destinations():
    return {"destinations": map_client.DESTINATIONS}


@app.post("/api/options")
def options(req: OptionsRequest):
    """UC.1.2 through UC.1.6."""
    profile = permit_client.validate(req.driver_id)
    if profile is None:
        return {"error": "We couldn't confirm a permit for that ID, so we can't show options. "
                         "Try student01, staff01 or visitor01."}

    start, end = window_of(req)
    candidates = map_client.lots_near(req.destination)
    allowed = eligibility.eligible_lots(profile, candidates)
    ranked = ranking.rank(allowed, req.destination, start, end)

    return {
        "permit": profile["permit"],
        "start": reservations.clock(start),
        "end": reservations.clock(end),
        "capacity_basis": CAPACITY_BASIS,
        "options": [
            {
                "lot_id": lot["id"],
                "name": lot["name"],
                "walk_minutes": lot["walk_minutes"],  # None means no estimate
                "remaining": lot["remaining"],
                "capacity": lot["capacity"],
            }
            for lot in ranked
        ],
    }


@app.post("/api/reserve")
def reserve(req: ReserveRequest):
    """UC.1.8 and UC.1.9, including the second eligibility and capacity check."""
    profile = permit_client.validate(req.driver_id)
    if profile is None:
        return {"error": "We couldn't confirm a permit for that ID, so nothing was booked."}

    lots = {l["id"]: l for l in map_client.lots_near(req.destination)}
    lot = lots.get(req.lot_id)
    if lot is None:
        return {"error": "That lot isn't in the list any more."}

    # Re-check rather than trusting what we showed a minute ago.
    if not eligibility.is_still_eligible(profile, lot):
        return {"error": "Your permit no longer covers that lot."}

    start, end = window_of(req)
    record = reservations.reserve(profile, lot, req.destination, start, end)
    if record is None:
        return {"error": "That lot just filled up for those hours. Pick another option."}

    return {
        "confirmation": record["id"],
        "lot": lot["name"],
        "start": record["start"],
        "end": record["end"],
        "guidance": map_client.route_to(lot, req.destination),
        "note": "Capacity is held in our records. We do not sense the physical space.",
    }
