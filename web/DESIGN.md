# CampusPark visual design

**Subject.** A campus driver, about to leave for Cornell, wants to know which lots their permit allows
and to hold a place before driving. The page is built like a product launch page: one live 3D world
behind everything, a short scroll story told by the camera, then booking on the same world seen from
above. Quiet type, a lot of dark space, one warm accent.

## Tokens

| Name | Value | Role |
| --- | --- | --- |
| Night | `#06080c` | scene and page ground |
| Ink | `#f5f5f7` | type on the dark page |
| Soft / dim | `#a1a1a6` / `#6e6e73` | secondary type |
| Sodium amber | `#ffb547` | the place you can take or have taken: the empty stall, beams over allowed lots, the walk, the ticket |
| System blue | `#0a84ff` (`#0071e3` on light) | actions and links only |
| Glass | `rgba(18,20,26,.58)` with 28px blur | the booking panel over the map |
| Paper / text | `#f5f5f7` / `#1d1d1f` | the staff console, which is a light working page |

Type: the system San Francisco stack (`-apple-system`, SF Pro Display/Text). Hero 112px at 700 with
tight tracking and a white-to-steel gradient; section heads 64px; body 17px; numerals tabular.

## The world (`web/static/scene.js`, Three.js 0.160 from jsDelivr)

Everything is generated in code: no image, model or video files.

- A lot at dusk: rounded-box cars in muted paint, head and tail lights, sodium lamps with real point
  lights, trees, wet asphalt, a blue-hour sky dome, lit-window buildings on the skyline, bloom.
- The empty stall glows amber with a floating P: that is the driver's place.
- From above, the same world becomes the campus map: every fixture lot is placed from `/api/map`
  (approximate positions), allowed lots raise an amber beam whose height is the share of places free,
  destinations are pale beams, and the walk is an arched light trail with moving dashes.

## Motion

One choreography, driven by scroll (GSAP 3.12 ScrollTrigger): hero, then three beats (permit, places
counted, held) with one camera move each, then the rise to the campus for booking. After that, motion
only answers the driver: pointing at a lot draws its trail and frames it; holding draws it solid.
Everything is static under `prefers-reduced-motion`.

## Rules

- Amber means "a place for you". Blue means "you can press this". Nothing else is colored.
- Words sit on dark space, never on top of busy geometry; the camera frames the scene to leave room.
- No decorative cards: the only panel is the glass booking panel and the only filled block is the
  ticket for a held place.
- Lot positions are approximate and the footer says so.
