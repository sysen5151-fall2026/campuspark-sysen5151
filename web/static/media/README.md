# Images

Generated for CampusPark from one prompt (in the Chapter 8 wiring notes and the project chat). Expected
files; every one has a gradient fallback, so a missing file never breaks a page.

| File | Size | Used on |
| --- | --- | --- |
| `hero-autumn.avif`, `.webp`, `.jpg` | 1672 x 940 | home page background (supplied by Hangting on 2026-10-28; 195, 246 and 484 KB; browsers take the first they support). The night hero it replaced stays in git history. |
| `permit.jpg`, `count.jpg`, `held.jpg` | 1200 x 1500 | fallback for browsers without AVIF or WebP |
| `permit-800.avif`/`.webp`, `count-800.*`, `held-800.*` | 800 x 1000 | home page "how it works" tiles (a tile is about 380 px wide, so 800 covers a retina screen) |
| `permit-bg.jpg`, `count-bg.jpg`, `held-bg.jpg` | 360 x 450 | the blurred backdrops; the blur hides any detail beyond this size |

Every web copy was encoded from the largest file available: AVIF with `sips` (quality 68 for the tiles, 74
for the hero, which starts smaller) and WebP with `cwebp -m 6 -sharp_yuv` (84 and 88), compared at 1:1 with
the JPEG before use. `sips` needs even dimensions for AVIF (an odd height decoded as a flat grey picture),
so the autumn hero was cropped by one row to 940. The server lets browsers keep these
files for a week, so a replaced image needs a new file name.

The images above are AI-generated concept images (`generation-prompts.json` records the prompts; its four
`lot-*` entries are kept for the record, but those files were removed on 2026-10-28). Files here are
compressed web copies: hero 2560 px wide, tiles 1200 px.

## Home page scenes

The home page plays one of six scenes (`static/scenes.js`): a weather effect over a photograph. The autumn
scene uses `hero-autumn`; the others use real, freely licensed photographs of Ithaca and Cornell from
Wikimedia Commons, loaded from Commons at 1280 or 1920 px and credited at the bottom right of the page.

| Scene | Photo | Author | Licence |
| --- | --- | --- | --- |
| Cherry blossom | [Cornell Botanic Gardens](https://commons.wikimedia.org/wiki/File:The_Cornell_Botanic_Gardens.jpg) | Bimala Rai Colavito | CC BY-SA 4.0 |
| Cherry blossom | [Beebe Lake and Triphammer Falls](https://commons.wikimedia.org/wiki/File:Cornell_University_-_Beebe_Lake_and_Triphammer_Falls.jpg) | P. Hughes | CC BY 4.0 |
| Snow | [Ithaca Falls in winter](https://commons.wikimedia.org/wiki/File:Ithaca_Falls_in_winter_3_(44330311385).jpg) | VillageHero | CC BY-SA 2.0 |
| Snow | [Buttermilk Falls in winter](https://commons.wikimedia.org/wiki/File:Buttermilk_falls_in_winter_(Ithaca)_(44518698994).jpg) | VillageHero | CC BY-SA 2.0 |
| Rain | [Ithaca Falls](https://commons.wikimedia.org/wiki/File:Ithaca_Falls_01.jpg) | LBM1948 | CC BY-SA 4.0 |
| Rain | [Cascadilla Gorge Trail](https://commons.wikimedia.org/wiki/File:Ithaca_-_Cascadilla_Gorge_Trail.jpg) | P. Hughes | CC BY 4.0 |
| Sunny | [Cayuga Lake from the Johnson Museum](https://commons.wikimedia.org/wiki/File:Ithaca,_NY_01.jpg) | LBM1948 | CC BY-SA 4.0 |
| Sunny | [Lower Taughannock Falls](https://commons.wikimedia.org/wiki/File:Lower_Taughannock_Falls_April_2024.jpg) | Awinch1001 | CC0 |
| Dusk | [Sunset on Cayuga Lake, Stewart Park](https://commons.wikimedia.org/wiki/File:Sunset_on_the_lake_-_panoramio.jpg) | Arseny Khakhalin | CC BY 3.0 |
| Dusk | [Sunrise at Beebe Lake](https://commons.wikimedia.org/wiki/File:Sunrise_at_Beebe_Lake_(4026352842).jpg) | Yisong Yue | CC BY-SA 2.0 |

No freely licensed photo of cherry trees in bloom in Ithaca was found, so the blossom scene's petals fall
over spring views of the Botanic Gardens and Beebe Lake.

## Lot photos

Lot pictures are real photographs, not generated. No freely licensed photo of the fixture lots exists, so
each lot shows a photo of a comparable campus lot or garage from Wikimedia Commons, loaded from Commons at
960 or 1920 px and credited on the page (`LOT_PHOTOS` in `static/common.js`). The lot details also show the
actual spot from above (USGS The National Map, public domain).

| Lot | Photo | Author | Licence |
| --- | --- | --- | --- |
| A Lot | [Summit View lot, University of Wyoming](https://commons.wikimedia.org/wiki/File:Summit_View_Parking_Lot_-_University_of_Wyoming_Campus_(52511610724).jpg) | Tony Webster | CC BY 2.0 |
| Hoy Road Garage | [Thompson Street structure, University of Michigan](https://commons.wikimedia.org/wiki/File:Thompson_Parking_Structure_at_Night,_University_of_Michigan_Campus,_Ann_Arbor,_Michigan_-_panoramio.jpg) | Dwight Burdette | CC BY 3.0 |
| Forest Home Drive | [Lake Meridian Park lot, Kent, WA](https://commons.wikimedia.org/wiki/File:Parking_lot_at_Lake_Meridian_Park_(2025)_-_0001.jpg) | Roc0ast3r | CC0 |
| Visitor Parking Garage | [Oak Street deck, Valdosta State University](https://commons.wikimedia.org/wiki/File:VSU_Oak_St_Parking_Deck_5.jpg) | Michael Rivera | CC BY-SA 3.0 |

Photos of the real Cornell lots taken by the team would replace these one for one: add the files here and
point `LOT_PHOTOS` at them.
