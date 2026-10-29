# Web interface

Two pages, both served by `api/main.py`. Run the app and open them through it (opened as files, the
fetch calls have nothing to talk to). Shared styles are in `static/style.css`, page scripts in `static/common.js`, `static/find.js`, `static/booking.js` and `static/admin.js`. The visual direction, tokens and rules are in `DESIGN.md`.

**The Campus Driver (UC.1)** moves through separate pages, each doing one job: `index.html` (the trip
search embedded in the home page), `find.html` (results list, a MapLibre map and lot details that open
in place, with each lot's "Why this lot was offered" facts from F.4, SR.3), `review.html` (the booking
summarized; nothing is held until the driver confirms), `booking.html` (a success check, then a pass
with confirmation number, QR code, directions and an add-to-calendar file, or a warning that keeps the
booking when route guidance is unavailable, SR.16) and `bookings.html` (open a booking again, UC.1.10).
The driver ID is kept in the tab's session storage and never put in a URL.

**`admin.html` at `/admin`: the Parking Administrator (UC.2).** A light working page. Shows the approved controls now in
force, and applies a capacity change or a closure. An accepted change shows the new rule version and
every confirmed booking it overlaps, which stay booked (SR.9); a change from an account that is not
approved is rejected (SR.14).

On purpose: walk times are labelled as estimates and a missing one says so; capacity is described as
places in our booking records, never as sensed spaces; every refusal names its reason in plain words.

The pages need network access for the map (MapLibre from unpkg, OpenFreeMap tiles) and the QR code library (cdnjs).

Not done yet: dates (every booking is today), cancellation, a real staff sign-in, and a keyboard and
screen-reader review for SR.12. The pages use native controls, labels and live regions, which is a
start, not the review.
