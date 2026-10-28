# CampusPark visual design

**Subject.** A campus driver, about to leave for Cornell, wants to know which lots their permit allows
and to hold a place before driving. The world they already read every day is parking signage: the
blue P sign, the painted stall lines, the curb, the permit hang-tag on the mirror. The interface borrows
that vernacular instead of a generic app look.

## Tokens

| Name | Hex | Role |
| --- | --- | --- |
| Sign blue | `#1D4E9E` | the P sign: header band, lot markers, option signs, primary action |
| Sign white | `#FFFFFF` | sign faces and borders |
| Asphalt | `#2C2F34` | the map and anything that stands for the road surface; held stalls |
| Curb yellow | `#F4C21B` | the walking route and the place you hold; never decoration |
| Concrete | `#DCDDD8` | page ground |
| Tag colors | student `#3E8E5A`, staff `#1D4E9E`, visitor `#E3672B` | the permit hang-tag after the permit is checked |

Type: **Overpass** (Google Fonts), the open revival of the US highway sign face, at 400, 600 and 800.
One family; hierarchy comes from weight and size. Body 16px / 1.5, headings 28/22/18, sign names 20/800.

## Layout

```
+--[ P  CampusPark ]---------------------------- Find my booking  Staff console --+
|  +------------------- map, sticky --------------+  +---- hang-tag -----------+  |
|  |  asphalt tiles, P markers, destination pin   |  |   ( )                   |  |
|  |  curb-yellow dashed walk on hover or hold    |  |  Your trip  [form]      |  |
|  |                                              |  +-------------------------+  |
|  |                                              |  [P | Forest Home Drive   ]  |
|  |                                              |  [  | 11 min · stall strip]  |
|  +----------------------------------------------+  [P | A Lot ...           ]  |
+---------------------------------------------------------------------------------+
```

Phones stack: map (45vh), hang-tag, signs.

## Rules

- Every structural device carries data: the stall strip is the pool's real capacity, with held stalls
  filled; the tag color is the permit the permit system returned; the yellow line is the walk.
- Signs are flat, with the inset white border real signs have. No drop shadows, no rounded card kit.
- One orchestrated motion: after a search the map fits the lots and the markers settle in order; after
  a booking the walk draws itself. Both are off under `prefers-reduced-motion`.
- Sentence case, plain words, no all-caps labels. Errors say what happened and what to do.
- Map positions are approximate fixture positions and the page says so.
