# Web interface

Two pages, both served by `api/main.py`. Run the app and open them through it (opened as files, the
fetch calls have nothing to talk to). Shared styles are in `static/style.css`, page scripts in `static/driver.js` and `static/admin.js`. The visual direction, tokens and rules are in `DESIGN.md`.

**`index.html` at `/`: the Campus Driver (UC.1).** Set as a Swiss-style poster: the wordmark and a
schematic campus map on the left, three numbered steps on the right (your trip, lots, your place). The
map is drawn in SVG like a transit diagram: the destination is a black square, lots the permit allows
are red numbered circles, and the walk from a lot is a 45-degree line with its minutes. It is not to
scale and says so. Each lot row leads with the walking minutes and the places free, then one tick per
place in the pool and a "Why this lot was offered" list with the rule and trip facts F.4 used (SR.3).
Holding a place turns step 3 into a red block with the confirmation, address and route guidance, or a
warning that keeps the booking when guidance is unavailable (SR.16). Step 3 also finds a confirmation
again for the driver who made it (UC.1.10).

**`admin.html` at `/admin`: the Parking Administrator (UC.2).** The same poster system. Shows the approved controls now in
force, and applies a capacity change or a closure. An accepted change shows the new rule version and
every confirmed booking it overlaps, which stay booked (SR.9); a change from an account that is not
approved is rejected (SR.14).

On purpose: walk times are labelled as estimates and a missing one says so; capacity is described as
places in our booking records, never as sensed spaces; every refusal names its reason in plain words.

Not done yet: dates (every booking is today), cancellation, a real staff sign-in, and a keyboard and
screen-reader review for SR.12. The pages use native controls, labels and live regions, which is a
start, not the review.
