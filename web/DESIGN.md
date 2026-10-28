# CampusPark visual design

**Subject.** A campus driver, about to leave for Cornell, wants to know which lots their permit allows
and to hold a place before driving. The page is set as a Swiss International Style poster: an
asymmetric grid, a flush-left grotesk, numbers set large because the numbers are the decision (minutes
of walking, places free), and one signal color used only where something is chosen or held.

## Tokens

| Name | Hex | Role |
| --- | --- | --- |
| Signal red | `#E1251B` | lots the permit allows, the walk being looked at, the held place |
| Black | `#000000` | type, rules, the destination, primary actions |
| White | `#FFFFFF` | ground |
| Field grey | `#EDEDED` | the map field and empty states |
| Mid grey | `#8A8A8A` | lots the permit does not allow, secondary text |

Type: **Archivo** (Google Fonts, variable width and weight). Wordmark 800 weight at up to 168px,
tight tracking, lowercase. Big numerals 800 at 72px. Body 400 at 17px / 1.45. Labels 600 at 15px,
sentence case. One family; contrast comes from size and weight.

## Grid

Twelve columns, 24px gutters, 40px page margin. Left seven columns: the wordmark and the map. Right
five: the numbered steps, because the flow is a real sequence (1 your trip, 2 lots, 3 your place).

```
| campus           | 1  Your trip                    |
| park             |    Driver ID ______________      |
|                  |    Destination ____________      |
|------------------|    Arriving ___   Hours __      |
| schematic map    |    [ Find parking ]              |
| dots and 45° lines|-------------------------------- |
| not to scale     | 2  Lots                          |
|                  | 11   Forest Home Drive   14/15   |
|                  | 14   A Lot               40/40   |
```

## Map

No map tiles. A schematic in the manner of a transit diagram: the destination is a black square,
lots are circles (red and numbered by walking order when the permit allows them, grey rings when it
does not), and the walk is drawn as a line that runs at 45° and then straight. Nodes start from their
approximate real positions and are pushed apart where they crowd, then snapped to a 40px construction
grid, as transit diagrams do. It keeps who is north or east of whom but is not to scale, and the page
says so.

## Rules

- Sharp rectangles, no rounded corners, no shadows. Thick rules (3px) only where they separate steps.
- Red marks a choice the driver can make or has made. Nothing decorative is red.
- The numerals are the content: walk minutes and places free are the largest text in each row.
- One motion: the walk line draws itself when a lot is pointed at or held. Off under
  `prefers-reduced-motion`.
- Sentence case, plain words. Errors say what happened and what to do next.
