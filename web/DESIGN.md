# CampusPark visual design

**Look: Liquid Glass.** Every page sits on a night scene (the generated photographs, blurred, with two slow
amber and blue light fields and a fine grain), and every surface is frosted glass: a translucent fill, a
28px backdrop blur, a lit top edge and a soft drop shadow. Primary actions are white glowing pills;
secondary ones are glass. On the results page the map is the page and the list, search and lot card float
over it, as in Apple Maps.

**Subject.** A campus driver, about to leave for Cornell, wants to know which lots their permit allows
and to hold a place before driving. The product follows the shape of the booking apps drivers already
know (search, results on a map, details, review, confirmation) and the look of Apple's own pages: a
cinematic home page, then quiet light pages where the work happens.

## Pages and flow

| Page | Job | Pattern it borrows |
| --- | --- | --- |
| `/` home | one sentence and the trip search, embedded in the hero | Airbnb and Google Flights search bar over a full-bleed image |
| `/find` | results list on the left, map on the right, lot details sliding over the list | SpotHero and Airbnb split view |
| `/review` | the booking summarized before anything is held | checkout review step |
| `/booking/{id}` | a success moment, then a pass with QR code, directions and calendar | Apple Wallet pass |
| `/bookings` | open a booking again; bookings made on this device are listed | order lookup |
| `/admin` | staff controls | settings page |

Each page does one thing. Nothing is held until the driver presses "Confirm and hold this place" on
the review page, and the confirmation is a page of its own.

## Tokens

| Name | Value | Role |
| --- | --- | --- |
| Ink | `#f5f5f7` at 100, 82, 62 and 44% | type, in four steps |
| Glass | fill `rgba(28,31,40,.42)`, edge `rgba(255,255,255,.16)`, blur 28px | every surface |
| White pill | `#ffffff` to `#e9eaee` with a soft white glow | primary actions |
| Blue | `#2997ff` | links and the destination |
| Sodium amber | `#ffb547` | the brand mark, the permit tag, the pass header |
| Green | `#34c759` | places free and the success check |
| Night | `#05070b` | the home page |

Type: the system San Francisco stack. Home headline 104px at 700 with tight tracking; page titles
40px; body 17px.

## Imagery

Photographic images generated for the project (see `web/static/media/README.md`), never stock
footage of real people or plates: a hero and three "how it works" tiles. Lot pictures are real
aerial photos from USGS (public domain), not generated. Every
image slot has a gradient fallback, so the pages work before the images arrive.

## Map

MapLibre GL with OpenFreeMap tiles (no key). Night style by default with a day switch, tilted to 3D.
The buildings are the real ones: OpenStreetMap footprints and heights from the tiles, raised with a
fill-extrusion layer. Lot and destination pins sit on real places from OpenStreetMap (Hoy Road Garage
and the destinations by name; the other fixture lots on the nearest real parking area). Lots the permit
allows raise an amber beam whose height is the share of places free and pulse a soft glow; the walk is
an arched trail with moving dashes and a travelling light; the destination pings. Opening a lot flies
the camera in and then orbits slowly until the driver touches the map. Lot photos are real aerials from
USGS The National Map (public domain), cropped around each lot.

## Motion

Small and purposeful: the hero text rises in once, the hero image settles from a slight zoom, the
details panel slides over the list, the map eases to the chosen lot, and the success check draws
itself before the pass appears. All of it is off under `prefers-reduced-motion`.
