# Web interface

Two pages, both served by `api/main.py`. Run the app and open them through it (opened as files, the
fetch calls have nothing to talk to). Shared styles are in `static/style.css`.

**`index.html` at `/`: the Campus Driver (UC.1).** The trip form goes in; the lots the driver's permit
accepts, with places free for the whole stay, come back as cards. Each card shows the address, the
walking estimate, a capacity bar and a "Why this option" list with the rule and trip facts F.4 used
(SR.3). Reserving gives a confirmation with its number, period, address and route guidance, or a
warning that keeps the booking when guidance is unavailable (SR.16). "Find my booking" shows a
confirmation again to the driver who made it (UC.1.10).

**`admin.html` at `/admin`: the Parking Administrator (UC.2).** Shows the approved controls now in
force, and applies a capacity change or a closure. An accepted change shows the new rule version and
every confirmed booking it overlaps, which stay booked (SR.9); a change from an account that is not
approved is rejected (SR.14).

On purpose: walk times are labelled as estimates and a missing one says so; capacity is described as
places in our booking records, never as sensed spaces; every refusal names its reason in plain words.

Not done yet: dates (every booking is today), cancellation, a real staff sign-in, and a keyboard and
screen-reader review for SR.12. The pages use native controls, labels and live regions, which is a
start, not the review.
