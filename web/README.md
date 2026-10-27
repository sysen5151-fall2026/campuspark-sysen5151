# Driver interface

The Campus Driver side of UC.1. One page, `index.html`: the trip form goes in,
a list of lots the driver's permit covers comes back, the driver picks one and
sees the confirmation with the booked period.

The page is served by `api/main.py` at `/`, so run the app and open it there
rather than opening the file directly. Opened as a file, the fetch calls have
nothing to talk to.

What it shows on purpose:

- walk times are labelled as estimates, and a lot with no estimate says so
  instead of showing a number (SR.3)
- capacity is shown as places not booked yet, with a line saying it comes from
  our booking records and not from sensors
- a blank or unknown ID, or a bad form value, gets a plain message instead of a
  frozen page

What it doesn't do yet: anything after the booking (cancellation, history),
dates, or a keyboard and screen-reader review for SR.12. The form uses native
controls and announces results through a live region, which is a start, not
the review.

ORD requirements that land on this screen: 5.1.1.1 (session initiation),
5.1.1.3 (customer input), 5.1.2.1 (welcome screen), 5.1.2.3 (requests for
customer input), 5.1.2.5 (itinerary, here the parking options).
