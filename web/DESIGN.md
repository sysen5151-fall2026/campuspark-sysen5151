# CampusPark visual design

**Look: Liquid Glass.** Every page sits on a night scene (the generated photographs, blurred, with two slow
amber and blue light fields and a fine grain). Surfaces use Apple's two glass materials: *regular* glass
for anything read (a light tint over a backdrop that is blurred and dimmed, so text keeps its contrast
while colour still shows through) and *thin* glass for small controls. Glass never sits on glass: tiles
inside a panel are plain fills. A gradient rim lights each edge, brightest at the top left. Primary
actions are white glowing pills; secondary ones are thin glass. On the results page the map is the page
and the list, search and lot card float over it, as in Apple Maps; the day map switches every surface to
light glass with dark type.

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
| Ink | `#f5f5f7` at 100 and 88%, then `#ebebf5` at 70 and 52% | type, in four steps (day map: `#1d1d1f` and `#3c3c43`) |
| Regular glass | tint `rgba(18,20,27,.30)`, backdrop `blur(24px) saturate(190%) brightness(.6)` | panels, sheets, cards, the pass |
| Thin glass | tint `rgba(18,20,27,.14)`, backdrop `blur(10px) saturate(180%) brightness(.72)` | chips, map controls, markers |
| Rim | 1px gradient ring, white 62% top left to 3% mid to 32% bottom right | every glass edge |
| White pill | `#ffffff` to `#e9eaee` with a soft white glow | primary actions |
| Blue | `#2997ff` | links and the destination |
| Sodium amber | `#ffb547` | the brand mark, the permit tag, the pass header |
| Green | `#34c759` | places free and the success check |
| Night | `#05070b` | the home page |

Type: the system San Francisco stack. Home headline 104px at 700 with tight tracking; page titles
40px; body 17px.

## Imagery

Photographic images generated for the project (see `web/static/media/README.md`), never stock
footage of real people or plates: a hero and three "how it works" tiles. Lot pictures are never
generated: each lot shows a real, freely licensed Wikimedia Commons photo of a comparable campus lot,
labelled "Similar lot" with its author and licence, and an aerial of the actual spot from USGS (public
domain). Every image slot has a gradient fallback, so the pages work before the images arrive.

## Map

MapLibre GL with OpenFreeMap tiles (no key). Night style by default with a day switch, tilted to 3D.
The buildings are the real ones: OpenStreetMap footprints and heights from the tiles, raised with a
fill-extrusion layer. Lot and destination pins sit on real places from OpenStreetMap (Hoy Road Garage
and the destinations by name; the other fixture lots on the nearest real parking area). Lots the permit
allows raise an amber beam whose height is the share of places free and pulse a soft glow; the walk is
an arched trail with moving dashes and a travelling light; the destination pings. Opening a lot flies
the camera in and then orbits slowly until the driver touches the map. A rotation dial sits bottom
right: turn left, a compass that shows the heading and turns back to north, turn right, and a slow spin
(a tap turns 45 degrees, holding keeps turning; Q, E and N on the keyboard). The camera keeps the
floating panels as padding, so fly-ins and rotation centre on the visible map. Lot photos are real aerials from
USGS The National Map (public domain), cropped around each lot.

## Weight

Each picture is sent at the size it is drawn and in the lightest format the browser reads (AVIF, then
WebP, then JPEG): the home page's first screen is one 240 KB hero, the tiles load as they near the
screen, blurred backdrops use 360 px copies, and lot photos come from Commons at 330 px in the list,
960 px in the card and 1280 px on the review page. The aerial is fetched only when a card opens. Text
responses are gzipped; images are cached for a week. The home page fetches the map library while idle,
and the results page opens its connections to the tile and photo servers as it starts. On the map,
data is sent to the map only when it changes; the glow's pulse and the travelling light run on feature
state, so an idle map does no re-tiling.

## Motion

Small and purposeful: the hero text rises in once, the hero image settles from a slight zoom, the
details panel slides over the list, the map eases to the chosen lot, and the success check draws
itself before the pass appears. All of it is off under `prefers-reduced-motion`.
