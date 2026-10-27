# Deviation log: C.5.3 Capacity Ledger

Chapter 9 component implementation from specification. The component prompt is
`prompts/2026-10-26-c5-3-capacity-ledger.md`. The implementation was generated in one pass by a
session that saw only that prompt, the stub and the contract, and could not read the tests. It is
committed unchanged in 49c9c8c. The requirement-derived tests in
`tests/test_c5_3_capacity_ledger.py` were written before it by a different session.

**First result:** all 39 test cases passed on the uncorrected generation (5.9 s), including 100
rounds of 100 concurrent requests for the last place with no overbooking. Passing tests did not end
the review. The code was then read line by line against the specification and the generating
session's own list of 22 assumptions. Ten points were examined. Six are deviations, listed first;
the other four are recorded because a reader might expect them to be.

Classification follows the Lab Manual: specification defect, assistant error, or unrequested
addition.

| # | The specification said | The code did | Why the gap appeared | Class | Reconciled by |
| --- | --- | --- | --- | --- | --- |
| D1 | RS.2.5: "serialize capacity holds for each pool" | One lock over the whole ledger, so holds in different pools also wait for each other | Per-pool serialization cannot keep "at most one reservation per request ID" when the same request ID arrives for two pools at once. The synthesis in RS.2.5 named the three properties but missed how two of them interact. | Specification defect | **Promoted.** RS.2.5 now reads "for each pool and for each request ID". Code kept: one lock meets both, and the 2 s check (RS.2.4) passes under 100 concurrent calls. |
| D2 | RS.1.4.3: return the saved reservation for a repeated request ID. RS.2.3: refuse when capacity data are missing. Silent on which wins. | Checks for a repeat first, so a repeat gets its saved reservation even if the pool has since vanished from IO.17 or filled up | The two requirements were written separately and both apply to a repeat after a rule change. The test session flagged the same conflict and left it untested. | Specification defect | **Promoted.** RS.1.4.3 now says the saved reservation is returned "whatever the capacity data or free places when the request is repeated". A repeat makes no new commitment, so RS.2.3's refusal does not apply, and a driver retrying after a timeout must get the booking already made. |
| D3 | RS.1.4.3: return the saved reservation for a request ID already saved | Returns it even when the repeat names a different driver, pool or period | The requirement keys on the request ID alone. The Chapter 5 implementation session raised the same point: anyone reusing another driver's request ID would see that driver's booking. | Specification defect | **Open, for the team.** Not promoted and not changed in code. Until it is decided, request IDs have to be random values generated per booking, never something a driver can type or guess. |
| D4 | Nothing about a rule set that lowers capacity below the places already held | Keeps every saved reservation and its hold, and refuses new holds for the minutes that are then full | The specification describes adding holds only. The choice matches SR.9 and 1.4.1.7, where a capacity cut flags affected bookings for staff instead of cancelling them. | Specification defect (gap) | **Promoted** as new requirement RS.1.4.5 Keep Saved Holds When Capacity Falls, traced from 1.4.1.7, satisfied by C.5 and C.5.3. |
| D5 | Prompt: `missing_data` when capacity is "absent or not an integer". Contract (RS.2.6): capacity is an integer with minimum 0. | Treated a negative capacity as valid, so every request for that pool got `pool_full` | The prompt's list of error conditions was narrower than the contract it pointed to, and the session followed the prompt. | Specification defect (in the prompt) | **Corrected in code.** A negative capacity is now invalid data and gives `missing_data`, as RS.2.3 asks. The prompt template note for next time: copy bounds from the contract into the error conditions. |
| D6 | IO.8 `reservation_id` is a string; no format | `"res-"` followed by a random UUID | No requirement fixes the format, so each component picked its own. The F.5 in-memory store and the SQLite store use `RES-00001`. | Specification defect (underspecified) | **Accepted, not promoted.** Nothing depends on the format, and random IDs do not reveal how many bookings exist. The sequential form goes away when F.5 hands commitment to C.5.3. |
| N1 | IO.21 is already screened by F.5.1 (RS.1.4.1); screening is out of scope | Does not re-validate IO.21. A malformed request can raise, and a zero-length period would be confirmed with no hold. | Matches the specification. | No deviation | Recorded as an integration condition: F.5.1 must run before C.5.3 whenever F.5 is rewired. |
| N2 | Capacity must be an integer | Booleans and floats such as 3.0 give `missing_data` | Python counts `True` as an int; JSON integers do not include booleans. The session followed the contract type. | No deviation | none |
| N3 | Out of scope: logging, caching, retries, persistence | None of these were added. The per-minute hold counters and the private `_commit` method are how the hold itself is kept, which RS.1.4.3 asks for. | | No unrequested addition | none |
| N4 | RS.2.4: 2 s at the 95th percentile | IO.18 is copied in full on every call, so cost grows with the number of saved reservations | Correct as written; the session noted it as an improvement it was not allowed to make. | No deviation | Watched, not changed. At pilot scale the RS.2.4 test passes with a wide margin. |

## Summary

Six deviations, all specification defects, none an assistant error, no unrequested additions. Three
were promoted into the model (D1 and D2 as amended wording of RS.2.5 and RS.1.4.3, D4 as the new
requirement RS.1.4.5) through the Chapter 8 and 9 import. One was corrected in code (D5). One was
accepted (D6). One waits for a team decision (D3).

What this says about the specification: the one-pass result was functionally right, but every
deviation sat where two requirements meet (D1, D2), where a requirement keys on less than it should
(D3), or where the specification simply stops (D4, D6). The prompt itself caused D5.

**After reconciliation:** 39 passed on the corrected component, and it runs in continuous integration
(step "Run the C.5.3 component tests (Chapter 9)").
