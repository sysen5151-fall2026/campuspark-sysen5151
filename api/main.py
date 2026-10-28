"""CampusPark web routes.

Each route serves one entry point in docs/route-table.md and hands the work to api/service.py,
which runs the first-level functions in functions/ in use-case order. The routes only translate
between the page and the functions: field names, clock labels and plain-language messages.

Both external services are still fixtures. Run it from the repo root with:
    uvicorn api.main:app --reload
"""

from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from api import service
from integrations.map import client as map_client

app = FastAPI(title="CampusPark")


MEDIA = "/static/media/"


@app.middleware("http")
async def revalidate_pages(request, call_next):
    """Pages and their scripts change with every increment; make browsers check before reusing them
    (an unchanged file comes back as a bodiless 304). Images change rarely and are the heaviest files,
    so browsers keep them for a week; a replaced image should get a new file name."""
    response = await call_next(request)
    if request.url.path.startswith(MEDIA):
        response.headers["Cache-Control"] = "public, max-age=604800"
    elif not request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-cache"
    return response


class CompressText:
    """Gzip pages, styles, scripts and JSON. Images are already compressed, so they pass through."""

    def __init__(self, app):
        self.app = app
        self.gzip = GZipMiddleware(app, minimum_size=1024)

    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and not scope["path"].startswith(MEDIA):
            await self.gzip(scope, receive, send)
        else:
            await self.app(scope, receive, send)


app.add_middleware(CompressText)

WEB = Path(__file__).resolve().parents[1] / "web"
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")


@app.exception_handler(StarletteHTTPException)
async def page_not_found(request, exc):
    """A missing page gets a page of its own; the API keeps its JSON errors."""
    if exc.status_code == 404 and not request.url.path.startswith(("/api/", "/static/")):
        return FileResponse(WEB / "404.html", status_code=404, headers={"Cache-Control": "no-cache"})
    return await http_exception_handler(request, exc)

# Shown next to any capacity number, because the number comes from our own
# booking records. Nothing in this version senses an empty space.
CAPACITY_BASIS = "Bookable places come from our booking records, not from sensors."
RECORD_NOTE = "Capacity is held in our records. We do not sense the physical space."

IDENTITY_ERROR = ("We couldn't confirm a permit for that ID, so we can't show options. "
                  "Try student01, staff01 or visitor01.")

# F.5's refusal reasons (IO.13) in the words a driver needs at the curb (RS.2.7).
REFUSALS = {
    "not_eligible": "Your permit no longer covers that lot.",
    "closed": "That lot is closed for part of those hours. Pick another option.",
    "pool_full": "That lot just filled up for those hours. Pick another option.",
    "missing_data": "We couldn't confirm everything a booking needs, so nothing was booked.",
}


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
    request_id: Optional[str] = None   # one per booking attempt, so a retry adds no second booking
    search_id: Optional[str] = None    # the search whose route guidance the confirmation uses


class Closure(BaseModel):
    start: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    end: str = Field(pattern=r"^(([01]\d|2[0-3]):[0-5]\d|24:00)$")


class ControlChange(BaseModel):
    account: str
    pool_id: str
    capacity: Optional[int] = None
    add_closure: Optional[Closure] = None
    clear_closures: bool = False


def minutes(label):
    h, m = label.split(":")
    return int(h) * 60 + int(m)


def trip_error(missing):
    if "hours" in missing:
        return "Your stay has to end by midnight on the same day."
    return "Check the form: " + ", ".join(missing) + " is missing or not valid."


def order_options(options):
    """Nearest first; a lot with no walking estimate goes after every lot that has one."""
    return sorted(options, key=lambda o: (o["walk_minutes"] is None, o["walk_minutes"] or 0))


def confirmation_body(c):
    return {"confirmation": c["reservation_id"], "lot": c["lot"], "address": c["address"],
            "start": service.clock(c["start"]), "end": service.clock(c["end"]),
            "guidance": c["guidance"], "warning": c["warning"], "note": RECORD_NOTE}


@app.get("/")
def home():
    return FileResponse(WEB / "index.html")


@app.get("/find")
def find_page():
    """UC.1.1 to UC.1.6: search results with the list and the map."""
    return FileResponse(WEB / "find.html")


@app.get("/review")
def review_page():
    """UC.1.7: the driver checks the booking before committing it."""
    return FileResponse(WEB / "review.html")


@app.get("/booking/{reservation_id}")
def booking_page(reservation_id: str):
    """UC.1.9 and UC.1.10: the confirmation and pass for one booking."""
    return FileResponse(WEB / "booking.html")


@app.get("/bookings")
def bookings_page():
    """UC.1.10: find a booking again."""
    return FileResponse(WEB / "bookings.html")


@app.get("/admin")
def admin_page():
    return FileResponse(WEB / "admin.html")


@app.get("/api/destinations")
def destinations():
    return {"destinations": map_client.DESTINATIONS}


@app.get("/api/map")
def map_positions():
    """UC.1.6: where the lots and destinations sit on the driver's map (approximate, display only)."""
    return map_client.map_view()


@app.post("/api/options")
def options(req: OptionsRequest):
    """UC.1.1 through UC.1.6."""
    found = service.search(req.model_dump())
    if found.get("error_kind") == "identity":
        return {"error": IDENTITY_ERROR}
    if found.get("error_kind") == "trip":
        return {"error": trip_error(found["missing"])}
    trip, offer = found["trip"], found["options"]
    return {
        "permit": found["eligibility"]["permit"],
        "start": service.clock(trip["start"]),
        "end": service.clock(trip["end"]),
        "capacity_basis": CAPACITY_BASIS,
        "search_id": found["search_id"],
        "reason": offer["reason"],
        "options": [
            {
                "lot_id": o["pool_id"],
                "name": o["name"],
                "address": found["addresses"].get(o["pool_id"]),
                "walk_minutes": o["walk_minutes"],  # None means no estimate
                "remaining": o["remaining"],
                "capacity": o["capacity"],
                "facts": o["facts"],
            }
            for o in order_options(offer["options"])
        ],
    }


@app.post("/api/reserve")
def reserve(req: ReserveRequest):
    """UC.1.7 to UC.1.9, including the second eligibility and capacity check in F.5."""
    trip = req.model_dump(include={"driver_id", "destination", "arrival", "hours"})
    booked = service.book(trip, req.lot_id, request_id=req.request_id, search_id=req.search_id)
    if booked.get("error_kind") == "identity":
        return {"error": "We couldn't confirm a permit for that ID, so nothing was booked."}
    if booked.get("error_kind") == "trip":
        return {"error": trip_error(booked["missing"])}
    if "refusal" in booked:
        return {"error": REFUSALS.get(booked["refusal"]["reason"], REFUSALS["missing_data"]),
                "reason": booked["refusal"]["reason"]}
    return confirmation_body(booked["confirmation"])


@app.get("/api/reservations/{reservation_id}")
def find_reservation(reservation_id: str, driver_id: str):
    """UC.1.10: the driver reviews a confirmation again."""
    found = service.find_confirmation(reservation_id.strip().upper(), driver_id.strip())
    if found is None:
        return {"error": "No booking with that confirmation number for that driver ID."}
    return confirmation_body(found)


@app.get("/api/admin/pools")
def admin_pools():
    """UC.2: the approved controls now in force (IO.17)."""
    rules = service.approved_rules()
    return {"version": rules["version"],
            "pools": [{"pool_id": pool_id, "name": p["name"], "capacity": p["capacity"],
                       "permits": p["permits"],
                       "closures": [{"start": service.clock(c["start"]), "end": service.clock(c["end"])}
                                    for c in p["closures"]]}
                      for pool_id, p in rules["pools"].items()]}


@app.post("/api/admin/controls")
def admin_controls(req: ControlChange):
    """UC.2: apply a parking control change (F.1), then acknowledge and report it (F.7)."""
    pool = service.approved_rules()["pools"].get(req.pool_id) or {}
    closures = None
    if req.clear_closures:
        closures = []
    if req.add_closure is not None:
        closures = (closures if closures is not None else list(pool.get("closures") or [])) + [
            {"start": minutes(req.add_closure.start), "end": minutes(req.add_closure.end)}]
    change = {"account": req.account.strip(), "pool_id": req.pool_id, "capacity": req.capacity,
              "permits": None, "closures": closures}
    ack, report = service.change_controls(change)
    return {"accepted": ack["accepted"], "reason": ack["reason"], "version": ack["version"],
            "pool_id": ack["pool_id"], "confirmed_count": report["confirmed_count"],
            "affected": [{"reservation_id": r["reservation_id"], "driver_id": r["driver_id"],
                          "start": service.clock(r["start"]), "end": service.clock(r["end"])}
                         for r in report["affected"]]}
