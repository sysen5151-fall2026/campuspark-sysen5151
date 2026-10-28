# CampusPark visual design

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
| Ink | `#1d1d1f`, `#424245`, `#6e6e73`, `#86868b` | type, in four steps |
| Paper / white | `#f5f5f7` / `#ffffff` | app page ground and surfaces |
| Lines | `#d2d2d7`, `#e8e8ed` | borders and dividers |
| Blue | `#0071e3` | every action and link |
| Sodium amber | `#ffb547` | the brand mark, the permit tag, the pass header |
| Green | `#1d8a3a` | places free and the success check |
| Night | `#05070b` | the home page |

Type: the system San Francisco stack. Home headline 104px at 700 with tight tracking; page titles
40px; body 17px.

## Imagery

Photographic images generated for the project (see `web/static/media/README.md`), never stock
footage of real people or plates: a hero, three "how it works" tiles and one thumbnail per lot. Every
image slot has a gradient fallback, so the pages work before the images arrive.

## Map

MapLibre GL with OpenFreeMap's Positron style (no key). Lots the permit allows are white pills showing
the walk in minutes; the open lot turns black; lots outside the permit are small grey dots; the
destination is a blue dot. The walk is a dashed blue line. Positions are approximate and the map says so.

## Motion

Small and purposeful: the hero text rises in once, the hero image settles from a slight zoom, the
details panel slides over the list, the map eases to the chosen lot, and the success check draws
itself before the pass appears. All of it is off under `prefers-reduced-motion`.
