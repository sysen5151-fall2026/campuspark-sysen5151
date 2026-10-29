# Prompt and provenance log

The course asks for every use of generative AI to be recorded, with enough detail to tell what was
asked and what came back, and rules out generating the project from one broad prompt. Each entry is
one scoped request: what was asked, what it was built from, what came back, and what a person checked
or decided. Entries were shortened on 2026-10-29; the longer originals are in this file's git history.

---

### 2026-09-24 · Hangting Zhu · Claude (Opus 5) · README, layout, SPEC and walking skeleton

Four separate requests, each built from the submitted BMA report and the Milestone Check 1 criteria: a
README, a package layout that mirrors the system context (stub modules citing ORD numbers and UC.1
actions), a primary-path `docs/SPEC.md` with the gaps left visible, and a UC.1 walking skeleton with
fixture permit and map services. Participants, flow and scope were checked against sections 1.1, 4, 5
and 9.2 of the report. The skeleton was run by hand: student and visitor permits get different lots,
capacity drops from 15 to 14 after a booking, the step 8 recheck refuses a student booking the visitor
garage, and an unknown ID gets a message instead of an error page. Ranking weights, outage handling and
persistence were left undone, because the stakeholder requirements that decide them were due October 4.

---

### 2026-09-30 · Team 25 project user · Codex · Chapter 3 specification and acceptance tests

No individual name is assigned to this entry. Asked to finish the Chapter 3.5 specification, the data
and AI response contracts, named failing tests and CI, from the saved Chapter 3 draft, Innoslate
project 13360 (13 needs, 18 stakeholder requirements), the rubric and Lab Manual Chapter 3. Produced the
updated `docs/SPEC.md`, `tests/acceptance_cases.json`, 20 named tests in `tests/test_spec_acceptance.py`,
the trace check in `tests/test_spec_coverage.py` and `.github/workflows/chapter3-acceptance.yml`. Need
and requirement statements, MOEs and validation criteria were copied from the draft without changing
any target. The trace check passed and all 20 placeholders failed with their named messages, as
intended. Team adoption of the criteria and real user validation are still pending; no stakeholder
approval is claimed.

---

### 2026-10-03 · Hangting Zhu · Claude (Opus 5.5) · Skeleton fixes against the SPEC

Asked to read the whole repository on top of `3bcfc58`, fix places where the skeleton contradicted
`docs/SPEC.md`, and add checks so later changes can't break UC.1. Fixed: a blank ID no longer borrows
the student profile (SR.2, SR.15); an unlisted destination no longer gets an invented 15 minute walk
(SR.3); bookings became half-open intervals, because comparing window labels as strings let
`09:00+2h` and `10:00+2h` miss each other and overbook a lot (SR.4); request fields are validated and
the page shows errors instead of freezing. Added `tests/test_skeleton.py` (33 tests), `docs/TRACE.md`,
and a CI step that runs developer tests before the red suite.

Turned down on purpose: making any acceptance test green without real evidence, building SR features
early, softening the red suite, editing the SPEC's needs and criteria section (`git diff` shows no
changed line there), and pushing to `main` while PR #1 was open. Left for the team: SR.1's 30 percent
target against the 20 percent in the BMA report.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 4 module decomposition

One module per first-level function in `functions/`, each signature written only from that function's
ICOMs in the first-level IDEF0 of F.0 (export of 2026-10-20), no bodies. Two model gaps surfaced. F.4
must show remaining capacity but receives no reservation records, so it takes IO.18 as a second input,
a correction the Chapter 8 and 9 import carries into Innoslate. F.1 and F.5 need somewhere to keep
state, so both take an injected store; the stores became the Chapter 8 subsystems. Every module imports
and every docstring matches Table 4 of the Chapter 6 and 7 report.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 5 tests first, then the implementation

Two sessions. The test session could read only requirements 1.4.1.1 to 1.4.1.11 and the `functions/`
signatures. It wrote `tests/test_functional_requirements.py` (11 tests, all failing on
`NotImplementedError`) and proved them against a throwaway reference implementation broken in ten
places; the reference was discarded. It also found that 1.4.1.6 asks for the lot address while no F.6
input carried one, so IO.16 got the address in the specification before any code was written.

A fresh session then wrote F.1 to F.7 and was not allowed to change a test: 11 passed and
`git diff tests/` was empty. It flagged that a repeated `request_id` from a different driver returns
the first driver's record. That question is still open (D3 below).

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 6 entry-point audit

A read of the repository, not a generation. The assistant listed the four routes and the two buttons
that call them in `docs/route-table.md`; Hangting filled in the use-case column against the model. No
orphan entry points, UC.2 recorded as planned, no code changed.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 7 internal interface contract

`contracts/api-v1.yaml` was written from the internal flows of the first-level IDEF0 (IO.8, IO.14 to
IO.19), not from the code, together with `tools/gen_stubs.py`, the generated stubs,
`tests/test_contract_conformance.py` and ADR-0001 to ADR-0003. Regenerating the stubs gives no
difference and the conformance test passed (10).

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 8 data access and deployment view

Produced `docs/deployment.md`, `data/schema.sql`, `data/reservation_db.py` (SQLite behind F.5's store
interface), `tests/test_data_access.py`, ADR-0004 and ADR-0005. The 5 data tests pass, including F.5
giving identical results on both stores and a table that holds exactly the RS.2.1 fields. The model
adapter was not built, because the model has no AI function yet and the Lab Manual says to fix that in
the model first (ADR-0005).

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 9 C.5.3 Capacity Ledger

The test session read only `docs/reservation-subsystem-spec.md`, contract 1.1 and a signature-only
stub, and wrote `tests/test_c5_3_capacity_ledger.py`: 16 functions, 39 cases, including 100 rounds of
100 concurrent requests for the last free place to match SR.4 (the specification said 50 and was raised
first). A throwaway reference passed them and fifteen deliberate breaks were each caught.

A separate session that never saw the tests generated `functions/f5_3_commit_capacity_hold.py` once from
`prompts/2026-10-26-c5-3-capacity-ledger.md`. It was committed unchanged in 49c9c8c and passed all 39
cases. The line-by-line review in `docs/deviation-log.md` found six specification defects: D1, D2 and D4
were promoted into RS.2.5, RS.1.4.3 and the new RS.1.4.5, D5 was fixed in four lines of code, D6 was
accepted, and D3 is open for the team. `tests/test_c5_3_promoted_requirements.py` covers the promoted
text.

---

### 2026-10-28 · Hangting Zhu · Claude (Opus 5.5) · Chapter 8 wiring

The routes moved off the Chapter 2 helpers onto `functions/` and SQLite through `api/service.py` (UC.1
search and booking, UC.2 changes), with new entry points for UC.1.10 and a staff console for UC.2. The
duplicate helpers in `api/` were removed. `tests/test_skeleton.py` now resets the service and books
through `/api/reserve`, so F.5 and the database make every decision; the behaviours it checks are the
same, plus nine new tests. Known limits: one booking lock until C.5.3 takes over, staff changes kept in
memory, and the staff check is the fixture account `admin01`. UC.1 and UC.2 were also run by hand.

---

### 2026-10-28 · Hangting Zhu · Claude (Opus 5.5) · Driver website design

Over one day Hangting asked repeatedly for a site that looks distinctive and loads fast. Four
directions were tried (parking signage, a Swiss poster, a procedural Three.js scene, and the multi-page
flow that was kept). No function, interface or requirement changed; the design rules are in
`web/DESIGN.md`. What stayed:

- Separate pages: home with the search built in, `/find` with a MapLibre 3D map (OpenFreeMap tiles,
  real OpenStreetMap building heights, day and night, a rotation dial), `/review` with a slide to hold
  the place that still works from the keyboard, the `/booking/{id}` pass with QR code and calendar
  file, `/bookings`, the staff console and a 404 page. The driver ID stays in session storage and never
  goes into a URL.
- Images: Hangting's own autumn photo, and freely licensed Wikimedia Commons photos of Ithaca, credited
  on the page. Lot cards show a Commons photo of a similar lot beside a USGS aerial of the actual spot.
  The three "how it works" pictures were generated by Hangting with GPT image generation; the notes are
  in `web/static/media/generation-prompts.json`. Generated lot photos were tried and removed, and Google
  imagery was not used because its terms forbid reuse.
- Speed: measured first (the home page sent about 1.8 MB), then AVIF and WebP copies, gzip for text,
  cache headers and a map loop that sends data only when it changes. The first screen is now about
  245 KB.
- Bugs found in testing and fixed: the day/night switch dropped the 3D layers; night buildings were
  drawn under the roads; a database file deleted under the running server broke booking (test data is
  now cleared only with the server stopped); the slide control's `.slide` class collapsed the lot photo
  and was renamed `.swipe`; the pass number wrapped on phones.

Every suite still passes (120 tests) and the 20 Chapter 3 placeholders still fail. The booking flow was
run by hand at desktop and phone width after each change.
