# Images

Generated for CampusPark from one prompt (in the Chapter 8 wiring notes and the project chat). Expected
files; every one has a gradient fallback, so a missing file never breaks a page.

| File | Size | Used on |
| --- | --- | --- |
| `hero.jpg` | 3840 x 2160 | home page background |
| `loop.mp4` (optional) | 1920 x 1080, 6 to 8 s | home page, replaces the still when present |
| `permit.jpg`, `count.jpg`, `held.jpg` | 1600 x 2000 | home page "how it works" tiles |
The images above are AI-generated concept images (`generation-prompts.json` records the prompts; its four
`lot-*` entries are kept for the record, but those files were removed on 2026-10-28). Files here are
compressed web copies: hero 2560 px wide, tiles 1200 px.

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
