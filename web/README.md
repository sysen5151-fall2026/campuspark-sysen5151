# Web interface

Two pages, both served by `api/main.py`. Run the app and open them through it (opened as files, the
fetch calls have nothing to talk to). Shared styles are in `static/style.css`, page scripts in `static/main.js`, `static/scene.js` and `static/admin.js`. The visual direction, tokens and rules are in `DESIGN.md`.

**`index.html` at `/`: the Campus Driver (UC.1).** A product-launch page over a live 3D world built
in `static/scene.js` (Three.js; no image or model files). Scrolling moves the camera through a lit lot
at dusk to the driver's empty stall, then up to the whole campus. Booking happens on that campus view
from a glass panel (`static/main.js`): lots the permit allows raise amber beams sized by places free,
pointing at a lot draws an arched trail to the destination, and holding a place shows the ticket with
confirmation number, address and route guidance, or a warning that keeps the booking when guidance is
unavailable (SR.16). Each option keeps its "Why this lot" facts from F.4 (SR.3). "Find my booking"
shows a confirmation again to the driver who made it (UC.1.10).

**`admin.html` at `/admin`: the Parking Administrator (UC.2).** A light working page. Shows the approved controls now in
force, and applies a capacity change or a closure. An accepted change shows the new rule version and
every confirmed booking it overlaps, which stay booked (SR.9); a change from an account that is not
approved is rejected (SR.14).

On purpose: walk times are labelled as estimates and a missing one says so; capacity is described as
places in our booking records, never as sensed spaces; every refusal names its reason in plain words.

The page needs network access for Three.js and GSAP (jsDelivr and cdnjs).

Not done yet: dates (every booking is today), cancellation, a real staff sign-in, and a keyboard and
screen-reader review for SR.12. The pages use native controls, labels and live regions, which is a
start, not the review.
