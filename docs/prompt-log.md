# Prompt and provenance log

Required by the course: any work done with generative AI gets recorded here,
with enough detail that a reader can tell what was asked for and what came
back. The course also rules out generating the whole project from one broad
prompt, so the entries below are scoped to a single file or a single question
each.

Format: date, who, tool, what was asked, what was produced, what the human
checked or changed.

---

### 2026-09-24 · Hangting Zhu · Claude (Opus 5)

**Asked for:** a README written from our approved OpsCon and system context,
covering the problem, the UC.1 flow, the four external participants, and the
in and out of scope lists from the BMA report.

**Produced:** `README.md`.

**Inputs given to the tool:** our submitted Business or Mission Analysis
report, the Milestone Check 1 criteria document.

**Checked:** external participants and the seven step flow match section 4 and
section 5 of the report. Scope list matches section 1.1 and 9.2. No feature
appears that is not in the report.

---

### 2026-09-24 · Hangting Zhu · Claude (Opus 5)

**Asked for:** a package layout that mirrors the system context diagram rather
than a generic framework starter, with stub modules whose docstrings cite the
requirement or use case action each one serves.

**Produced:** `api/eligibility.py`, `api/ranking.py`, `api/reservations.py`,
`integrations/permit/client.py`, `integrations/map/client.py`,
`web/README.md`. All function bodies raise NotImplementedError.

**Checked:** one top level folder per element of the system context. Each
module cites ORD numbers and UC.1 actions. No implementation was requested or
accepted at this stage, since the ranking rules and error handling depend on
the stakeholder requirements due October 4.

---

### 2026-09-24 · Hangting Zhu · Claude (Opus 5)

**Asked for:** a specification file derived from the ORD requirements and the
UC.1 flow, covering the primary path only, with the gaps left visible.

**Produced:** `docs/SPEC.md`.

**Checked:** every step in the path table cites a UC.1 action and, where one
exists, an ORD requirement number. The two measures match the ones in the BMA
report. Off nominal cases are listed as not specified rather than filled in.

---

### 2026-09-24 · Hangting Zhu · Claude (Opus 5)

**Asked for:** a walking skeleton covering UC.1 only, with the permit system
and the map service returning fixture data, and the second eligibility and
capacity check kept as a real step rather than skipped.

**Produced:** implementations in `api/eligibility.py`, `api/ranking.py`,
`api/reservations.py`, both integration clients, `api/main.py` with
`/api/options` and `/api/reserve`, and `web/index.html`.

**Checked by running it:** a student permit and a visitor permit get different
lots back, remaining capacity drops from 15 to 14 after a reservation, a
student trying to reserve the visitor garage is refused by the recheck at step
8, and an unknown driver ID returns a message instead of an error page. The
browser flow completes from the form through to a confirmation number.

**Left deliberately undone:** ranking weights, error handling for a downed
external service, persistence. Those depend on the stakeholder requirements
due October 4, and filling them in now would put behaviour in the code that no
requirement asks for.

---

### Template for future entries

```
### YYYY-MM-DD · name · tool

**Asked for:**

**Produced:**

**Inputs given to the tool:**

**Checked:**
```


### 2026-09-30 Chapter 3 specification and acceptance work

**Requested by:** the Team 25 project user. No individual name is assigned to this entry.

**Tool:** Codex.

**Asked for:** complete the remaining Chapter 3.5 specification, data and AI response contracts, named failing tests, commit, and automatic checks in the existing CampusPark repository.

**Inputs:** the saved CampusPark Chapter 3 report draft; Innoslate project 13360 with 13 needs, 18 stakeholder requirements, and 20 source links; the current Canvas assignment and rubric screenshots; Lab Manual Chapter 3; the existing specification and walking skeleton.

**Produced:** an updated `docs/SPEC.md`; `tests/acceptance_cases.json`; 20 named tests in `tests/test_spec_acceptance.py`; one trace check in `tests/test_spec_coverage.py`; `requirements-dev.txt`; `.github/workflows/chapter3-acceptance.yml`; updated README instructions.

**Assistant work:** copied the current draft need statements, requirement statements, MOEs, and validation criteria without changing their targets. Added repository criterion IDs and test names. Described current fixture fields and planned contract behavior separately. Flagged the earlier 20%/90% targets and the newer Chapter 3 proposals for review. This was drafting and technical review, not a claim that the team wrote these criteria without assistant help.

**Technical checks run:** the local pytest run collected 21 tests. The trace check passed and all 20 acceptance placeholders failed with their named assertion messages. The process returned exit code 1. No syntax, collection, or dependency error caused those 20 failures. A separate review checked that all source statements, MOEs, and validation criteria matched the saved Chapter 3 data.

**Human review:** the user authorized this repository work and confirmed the repository URL. Team adoption of the criteria, owner approval, and real user or field validation remain pending. No completed human review or stakeholder approval is claimed.

**Build limits:** application code was not changed for this increment. The existing fixture services, time-window limits, and in-memory records remain. The named red suite follows the manual's Chapter 3 example. The AI contract is specified for later implementation; no live model service was called.

---

### 2026-10-03 · Hangting Zhu · Claude (Opus 5.5)

**Asked for:** read every file in the repository after the Chapter 3 branch, fix
places where the walking skeleton contradicts `docs/SPEC.md`, and add checks so
later changes can't break UC.1. The request was explicit that the project must
not be broken and that nothing should be done that could cost marks.

**Inputs given to the tool:** the whole repository on top of commit `3bcfc58`
(the Chapter 3 branch), the Milestone Check 1 criteria, and the Stakeholder
Needs and Requirements Definition rubric.

**Decided against, and why:**

- Turning any acceptance test green. Each AC needs owner-reviewed cases, real
  users or a field pilot. A unit test passing would have been presented as
  evidence that doesn't exist.
- Building new SR features such as cancellation, admin screens, AI help or
  route-failure handling. Milestone Check 1 asks for a controlled walking
  skeleton, and the SPEC places implementation in later chapters.
- Changing the CI trigger or softening the red suite. The SPEC says the suite
  runs on every push and pull request and must not be hidden.
- Editing anything in the SPEC's Needs and Acceptance Criteria section. The
  trace check matches those strings exactly, and the criteria are still waiting
  for team review.
- Pushing to `main`. Junjie's pull request #1 is still open; merging it is the
  team's call.

**Produced:**

- `integrations/permit/client.py`: a blank ID now returns no profile. It used to
  borrow the student profile, which gave rights nobody confirmed (SR.2, SR.15).
- `integrations/map/client.py`: an unlisted destination gets no walk time
  instead of a made-up 15 minutes; route text says when it has no estimate (SR.3).
- `api/reservations.py`: bookings are same-day half-open intervals, and
  remaining capacity is configured places minus the most held at one moment.
  The old version compared window labels as strings, so `09:00+2h` and
  `10:00+2h` never saw each other and a lot could be overbooked (SR.4).
- `api/ranking.py`: follows the interval change; lots with no estimate sort last.
- `api/main.py`: all request fields required, `arrival` must be `HH:MM`, `hours`
  at least 1. No upper limit, because none is approved. Confirmation now
  includes the booked period. The home page path no longer depends on the
  directory the server is started from.
- `web/index.html`: a 422 or server error now shows a message instead of
  freezing the page; estimates, missing walk times and the capacity basis are
  labelled; the upper hour limit was dropped to match the API.
- `api/__init__.py` and the `integrations` package markers.
- `tests/test_skeleton.py`: 33 developer tests, kept out of
  `test_spec_acceptance.py` so the trace check still sees exactly 20 tests there.
- `.github/workflows/chapter3-acceptance.yml`: installs the app, runs the
  developer tests before the red suite, and writes a short run summary saying
  which failures are expected. The red suite still fails the job.
- `docs/SPEC.md`: only the sections that describe current code (scope note,
  existing components, current data shape, current failure behaviour, and a
  paragraph on the developer tests).
- `docs/TRACE.md`: new. One need traced end to end, every need against code and
  tests, and every file against what asks for it.
- `README.md` and `web/README.md`: brought up to date; the Actions link points
  at the course organisation.

**Checked:**

- `pytest tests/test_skeleton.py`: 33 passed.
- `pytest tests/test_spec_coverage.py`: 1 passed.
- `pytest tests/test_spec_acceptance.py`: 20 failed, each with its own named
  message. Same result as before this change.
- `git diff` against `3bcfc58` shows no changed line in the SPEC's needs and
  criteria section.
- Every test name and file path cited in `docs/TRACE.md` exists.
- The page was run in a browser: student and visitor lookups, a blank ID, a
  zero-hour stay, and a booking all behave as described above.

**Still open for the team:** whether to adopt the SR.1 30 percent target or keep
the BMA report's 20 percent, and the SR.1 "retained from Chapter 1" label, since
Chapter 1 says 20 percent. Neither was changed here.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 4 module decomposition

**Asked for:** one module per first-level function, with a signature written only from that
function's ICOMs (inputs as parameters, controls as keyword-only configuration, outputs as return
values, mechanisms as injected dependencies) and no bodies.

**Built from:** the first-level IDEF0 of F.0 in the Innoslate model (F.1 to F.7, IO.1 to IO.19),
as exported on 2026-10-20.

**Produced:** `functions/` with seven modules, each docstring naming its function ID and listing
its ICOMs, and `docs/traceability.md`. Every body raises `NotImplementedError`.

**Findings while translating ICOMs:**

- F.3 sends IO.4 to the map service and gets IO.5 back, so its module has two functions, one that
  writes the request and one that turns the answer into IO.15 and IO.16.
- F.4 is required to show only options with remaining capacity, but no flow on the first-level
  IDEF0 brings it the places already held. The signature takes IO.18 Reservation Records as a
  second input. This is a model gap, not a code choice: the model is corrected in the Chapter 8 and
  9 import (F.4 receives IO.18), which adds one feedback loop from F.5 to F.4.
- F.1 and F.5 need somewhere to keep state (approved rules, saved reservations). The first-level
  IDEF0 has no mechanisms yet, so both take an injected store. The stores become the Chapter 8
  subsystems.

**Checked:** every module imports; each ICOM in a docstring matches Table 4 of the Chapter 6 and 7
report; no function body was written.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 5 tests, written first

**Asked for:** one test per functional requirement 1.4.1.1 to 1.4.1.11, derived from the requirement
text and its verification criterion, in a session of its own that could read only the requirement
text and the `functions/` signatures and docstrings, not `api/`, `integrations/` or `web/`.

**Built from:** requirements 1.4.1.1 to 1.4.1.11 in the Innoslate system requirements document,
with their verification methods and pass conditions.

**Produced:** `tests/test_functional_requirements.py` (11 tests, named for the requirement IDs) and a
new CI step that runs them. All 11 fail with `NotImplementedError`, as they should before any body
exists. The test session also wrote a throwaway reference implementation outside the repository to
confirm the tests can be satisfied, then broke it on purpose in ten places to confirm each break is
caught. That reference was not kept and was not given to the implementation session.

**Finding, repaired in the specification before any code was written:** requirement 1.4.1.6 asks for
the lot address in the confirmation, but none of F.6's inputs carried an address. IO.16 Route
Guidance Data now carries each pool's address from IO.5, kept even when every route is unavailable,
which is also what SR.16 needs. The F.3 and F.6 docstrings and `contracts/api-v1.yaml` were updated,
and the test session then tightened the 1.4.1.3 and 1.4.1.6 tests to check the actual address.

**Other limits the test session reported:** "logged" in 1.4.1.1 can only be checked through the
reason in IO.19; "same decision" in 1.4.1.8 is a real cross-check only for F.4, F.5 and F.7, because
F.2 and F.6 make no rule decision; 1.4.1.9 is verified by Demonstration and the automated test does
not replace the user demonstration; the 60 second limits are checked only for the in-process part.

**Checked:** `pytest tests/test_functional_requirements.py`: 11 failed, each on `NotImplementedError`.
`pytest tests/test_skeleton.py tests/test_spec_coverage.py`: 34 passed.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 5 implementation

**Asked for:** bodies for the seven modules in `functions/` until
`tests/test_functional_requirements.py` passes, in a fresh session that could read the requirements,
the module docstrings, `contracts/api-v1.yaml` and the tests, and was not allowed to change any test.

**Built from:** requirements 1.4.1.1 to 1.4.1.11, the ICOM docstrings from the Chapter 4 increment
and the shapes in the internal interface contract.

**Produced:** bodies for F.1 to F.7 and their two stores (`RulesStore`, `ReservationStore`). No file
outside `functions/` was changed. Remaining capacity is computed in F.4 and F.5 the same way, as the
peak number of places held at once over the booked period, so the options F.4 shows and the
decisions F.5 makes cannot disagree.

**Decisions the requirements left open, made in code and listed here for the team:**

- F.1 replaces the closure list of a pool when a change gives a new one, and counts an accepted
  change that alters nothing as a new rule version. Rejected attempts are kept in a private log on
  the store; nothing reads it yet.
- F.5 maps unknown, invalid and mismatched eligibility answers to `not_eligible`, and missing or
  failed answers to `missing_data`, as SR.15 asks.
- A repeated `request_id` returns the saved record even when the driver or pool differs, because
  that is what the contract and RS.1.4.3 say. The implementation session pointed out that this
  would show one driver's booking to another driver who reused the same ID. Open question for the
  team: narrow the contract to "the same driver and request ID".

**Model gaps found:** IO.5 Parking Locations and Route Information has no route text, but 1.4.1.3 and
1.4.1.6 need route guidance to show the driver. F.3 builds the text from the walk estimate for now.
IO.12 Reservation Reports lists only affected bookings, so there is no report of all bookings that
1.4.1.11 could be checked against directly; the test drives it through a closure on every pool.

**Checked:** `pytest tests/test_functional_requirements.py`: 11 passed.
`tests/test_skeleton.py` 33 passed, `tests/test_spec_coverage.py` 1 passed,
`tests/test_spec_acceptance.py` 20 failed (the Chapter 3 placeholders, unchanged). `git diff tests/`
is empty. The 11 functional tests were also run under Python 3.12 with a small runner, all passing.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 6 entry-point audit

**Asked for:** a list of every route, endpoint and user-triggered entry point and what calls each
one, without a use-case mapping. This was a read of the repository, not a generation.

**Built from:** `api/main.py`, `web/index.html`, `integrations/`, `functions/`, `tools/`.

**Produced:** `docs/route-table.md`. The assistant listed four routes (`GET /`,
`GET /api/destinations`, `POST /api/options`, `POST /api/reserve`) and the two buttons that call
them, and noted that nothing calls `functions/` yet. The use-case column, the orphan decision and
the planned status for UC.2 were filled in by Hangting Zhu against the model and are open for the
team's review in the pull request.

**Result:** no orphan entry points. UC.2 has no entry point and is recorded as planned. The routes
still use the Chapter 2 helpers instead of `functions/`; recorded as a duplication to remove in the
Chapter 8 increment.

**Assistant assumptions:** none; no code was changed.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 7 internal interface contract

**Asked for:** an internal interface contract written from the flow list of the first-level IDEF0,
not from the code, then typed stubs generated from it and a test that the modules keep those
signatures.

**Built from:** the internal flows of the first-level IDEF0 of F.0 (IO.8, IO.14 to IO.19) in the
export of 2026-10-20, the function ICOMs, and the shapes noted in the Chapter 4 docstrings.

**Produced:** `contracts/api-v1.yaml` (OpenAPI 3.0.3, one operation per first-level function, each
internal flow listed under `x-internal-flows` with its source, receivers and role),
`tools/gen_stubs.py`, the generated `contracts/generated/flows.py` and `stubs.py`,
`tests/test_contract_conformance.py`, and ADR-0001 to ADR-0003. A CI step now runs the conformance
test and `pyyaml` is in `requirements-dev.txt`. The contract was written before the Chapter 5
implementation session and was one of the files that session could read.

**Decisions recorded as ADRs:** ADR-0001 writes down the toolchain chosen in Chapter 1.
ADR-0002 keeps the two stores out of the contract as injected mechanisms. ADR-0003 adds IO.18 as an
input to F.4, a model correction that the Chapter 8 and 9 import carries into Innoslate.

**Checked:** `python tools/gen_stubs.py` regenerates the committed stubs with no difference.
`pytest tests/test_contract_conformance.py`: 10 passed, including a check that every `x-internal-flows` entry matches a
flow on the first-level IDEF0, with IO.18 also going to F.4 per ADR-0003.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 8 data access and deployment view

**Asked for:** the component and deployment view, a database schema from the Chapter 3 data
contract, and a data access component behind the interface F.5's ICOMs define, keeping every suite
green. The model adapter was to be built only if the model authorizes it.

**Built from:** the first-level subsystems C.1 to C.7, the context and first-level conduits, the
booking record in the `docs/SPEC.md` data contract, and RS.2.1 Limited Personal Data from the
Reservation Subsystem Specification.

**Produced:** `docs/deployment.md`; `data/schema.sql` and `data/reservation_db.py` (SQLite, standard
library only); `tests/test_data_access.py` (5 tests) and a CI step for it; ADR-0004 (SQLite) and
ADR-0005 (no model adapter yet). The in-memory store's private `_saved_for` and `_save` became the
public `saved_for` and `save`, so a second store can implement the interface without reaching into
private names; F.5's capacity count now reads `store.all()` instead of the in-memory list.

**Not done, on purpose:** the model adapter. The Innoslate model has no AI function or model
interface (candidate F.9), so per the Lab Manual the gap is in the model and is fixed there first
(ADR-0005). The routes in `api/main.py` are not yet switched to `functions/` and the database,
because that changes the reset fixture in `tests/test_skeleton.py`; recorded as the next step in
`docs/deployment.md`. The permit and map sources stay fixtures until their owners approve access.

**Checked:** `pytest tests/test_data_access.py`: 5 passed, including F.5 giving identical results on
both stores for a scripted sequence and the table holding exactly the RS.2.1 fields.
`test_functional_requirements.py` 11 passed, `test_skeleton.py` 33 passed,
`test_contract_conformance.py` 10 passed after the refactor.

---

### 2026-10-26 · Hangting Zhu · Claude (Opus 5.5) · Chapter 9 tests for C.5.3, written first

**Asked for:** requirement-derived tests for C.5.3 Capacity Ledger (F.5.3 Commit Capacity Hold), in a
session that could read only the component specification, the contract and the signature-only stub,
and no implementation of anything in F.5.

**Built from:** `docs/reservation-subsystem-spec.md` (RS.1.4.3, RS.2.5, RS.1.1.3, RS.2.2, RS.1.2.1,
RS.1.2.3, RS.2.1, RS.2.3, RS.2.4) and `contracts/api-v1.yaml` version 1.1, which adds the
second-level flows IO.20 to IO.22 and the `commitCapacityHold` operation.

**Produced:** `functions/f5_3_commit_capacity_hold.py` (signature and ICOM docstring only),
`docs/reservation-subsystem-spec.md` (copy of the model document), contract version 1.1 with
regenerated stubs, and `tests/test_c5_3_capacity_ledger.py` (16 test functions, 39 cases). The
concurrency tests release 100 threads at once through a barrier, 100 rounds for the last free
place, matching the SR.4 validation of 100 rounds of 100 requests. The specification first said 50
requests; it was corrected to 100 in the model and here before the tests were finished, because 50
was weaker than the stakeholder requirement it traces from.

**How the tests were checked:** the test session wrote a throwaway reference implementation outside
the repository. All 39 cases pass on it, and on three other valid designs (one global lock,
counting by scanning records, refusing a changed repeat). Fifteen deliberate breaks were each caught,
among them no lock, check and save as two steps, a second record for a repeated request ID, counting
touching bookings instead of places held at once, cached rules, and an extra stored field. The
reference was not kept and is not available to the implementation session.

**Ambiguities the test session reported, left untested on purpose:** what a repeated request ID with
different details should do (only "one record, unchanged" is tested); a repeat arriving when capacity
data are missing (RS.2.3 and RS.1.4.3 pull in opposite directions); the refusal reason for a negative
capacity; boolean or float-valued capacities; the order of IO.18.

**Checked:** against the stub, 39 failed, each on `NotImplementedError`. Every other suite unchanged.
