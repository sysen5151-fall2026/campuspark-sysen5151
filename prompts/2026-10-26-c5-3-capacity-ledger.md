# Filled Component Prompt Template: C.5.3 Capacity Ledger

Chapter 9 component implementation from specification. Generated in one pass by a fresh session
that received only this prompt and the files it names; no follow-up corrections were given.

**Context.** CampusPark is a campus parking reservation web application: a Campus Driver enters a
trip, sees the parking pools their permit allows, and reserves a place, with capacity held in
CampusPark's own records rather than sensed. This component sits inside C.5 Reservation Subsystem,
which performs F.5 Recheck and Record Reservation, and it is the only component that writes a
reservation. It receives requests that F.5.1 has already screened and F.5.2 has already rechecked
for eligibility and closures.

**Component.** C.5.3 Capacity Ledger

**Function performed.** F.5.3 Commit Capacity Hold

**Requirements.** Quoted from the Reservation Subsystem Specification (`docs/reservation-subsystem-spec.md`):
- RS.1.4.3 Commit Capacity Hold: "The Reservation Subsystem shall check capacity and save the reservation with its capacity hold in one step, and shall return the saved reservation for a request ID it has already saved."
- RS.2.5 Capacity Safety Under Concurrent Use: "The Reservation Subsystem shall serialize capacity holds for each pool so that the holds for any minute never exceed the approved capacity, and shall keep at most one reservation per request ID, with at least 100 requests arriving at once."
- RS.1.1.3 Accept Approved Parking Rules and Capacity: "The Reservation Subsystem shall accept Approved Parking Rules and Capacity from the Parking Control Subsystem."
- RS.2.2 Timely Parking Controls: "The Reservation Subsystem shall apply a newly published rule set to every booking attempt it receives more than 10 seconds after publication."
- RS.1.2.1 Provide Confirmed Reservation Record: "The Reservation Subsystem shall provide Confirmed Reservation Record to the Confirmation Subsystem."
- RS.1.2.3 Provide Reservation Records: "The Reservation Subsystem shall provide Reservation Records to the Option Selection Subsystem and the Reporting Subsystem."
- RS.2.1 Limited Personal Data: "The Reservation Subsystem shall store only the reservation ID, request ID, identity reference, pool, booked period and status for each reservation."
- RS.2.3 Safe Handling of Source Failures: "The Reservation Subsystem shall refuse confirmation whenever the eligibility or capacity data for any part of the booked period are missing, failed or unknown."
- RS.2.4 Booking Response Time: "The Reservation Subsystem shall return a confirmed record or a refusal within 2 seconds for at least 95% of booking attempts."
- RS.2.6 Internal Interface Contract: "The Reservation Subsystem shall accept and produce IO.7, IO.3, IO.17, IO.8, IO.13 and IO.18 only in the forms defined by the internal interface contract, version 1."

RS.1.4.3 is the design output requirement for C.5.3. Its measure of performance is "Overbookings in
100 rounds of 100 concurrent requests (0)" and its verification is "Concurrency test on the last free
place, plus a repeated request ID." RS.2.6 applies here to IO.17, IO.8 and IO.18; IO.21 and IO.22 are
defined in version 1.1 of the same contract.

**Interfaces.** The signature is fixed by the contract (`contracts/api-v1.yaml`, operation
`commitCapacityHold`) and must not change:

```python
class CapacityLedger:
    def __init__(self): ...
    def records(self) -> list: ...      # every saved reservation (IO.18)

def commit_capacity_hold(eligible_booking_request: dict, *, approved_rules: dict,
                         ledger: CapacityLedger) -> tuple:
    # returns (IO.8 or None, IO.18, IO.22 or None); exactly one of IO.8 and IO.22 is not None
```

- Input IO.21 Eligible Booking Request: `{"request_id": str, "driver_id": str, "pool_id": str,
  "start": int, "end": int}`. Times are minutes since midnight on one day; the booked period is the
  half-open interval [start, end), so a booking ending at 600 and one starting at 600 do not overlap.
- Control IO.17 Approved Parking Rules and Capacity: `{"version": int, "pools": {pool_id: {"name":
  str, "capacity": int, "permits": [str], "closures": [{"start": int, "end": int}]}}}`. The rule set
  passed on each call is the one in force for that call.
- Output IO.8 Confirmed Reservation Record: `{"reservation_id": str, "request_id": str, "driver_id":
  str, "pool_id": str, "start": int, "end": int, "status": "confirmed"}`.
- Output IO.18 Reservation Records: a list of IO.8, every reservation the ledger has saved.
- Output IO.22 Booking Refusal Reason: `{"request_id": str or None, "reason": "missing_data" |
  "not_eligible" | "closed" | "pool_full"}`. From this component only `pool_full` (no free place for
  some minute of the period) and `missing_data` (capacity for the pool is absent or not an integer)
  can occur.
- Mechanism: the `ledger` argument, an instance of `CapacityLedger`, injected by the caller.
- Error conditions: a pool missing from IO.17 or without an integer capacity gives `missing_data`
  with no record and no hold; a request_id already saved returns the saved IO.8 and adds no second
  hold; anything else that fits gives a new IO.8.

**Constraints.** Python, valid on both 3.9 and 3.12; standard library only. Write only
`functions/f5_3_commit_capacity_hold.py` and keep its module docstring. Calls arrive concurrently
from many threads, so the ledger must be safe under concurrent use. Storage is in memory in this
increment; persistence belongs to the data access component and is not this component's job. No
network access; everything runs locally. A call must return well within 2 seconds.

**Success criteria.** Requirement-derived tests written beforehand by a separate session from the
same requirements (`tests/test_c5_3_capacity_ledger.py`) pass, including zero overbookings in 100
rounds of 100 concurrent requests for the last place, and `tests/test_contract_conformance.py` still
passes.

**Output format.** The complete new contents of `functions/f5_3_commit_capacity_hold.py`, written to
that file, then a plain list of every assumption you made that this prompt does not state.

**Out of scope.** Eligibility, permit and closure checks (F.5.2 does those); refusal wording for the
driver (F.5.4); screening of malformed requests (F.5.1); logging, caching, retries, persistence,
cancellation; any stored field beyond those RS.2.1 lists; changes to any other file; new
dependencies.

The current stub, for reference:

```python
"""F.5.3 Commit Capacity Hold, performed by C.5.3 Capacity Ledger.

ICOM on the second-level IDEF0 of F.5 Recheck and Record Reservation (Chapter 9):
    input     IO.21 Eligible Booking Request              from F.5.2 Recheck Booking Eligibility
    control   IO.17 Approved Parking Rules and Capacity   from F.1 (C.1 Parking Control Subsystem)
    outputs   IO.8  Confirmed Reservation Record          to F.6 (C.6 Confirmation Subsystem)
              IO.18 Reservation Records                   to F.4 (C.4) and F.7 (C.7)
              IO.22 Booking Refusal Reason                to F.5.4 Issue Booking Refusal
Mechanism: C.5.3 Capacity Ledger, injected as `ledger`.

Shapes (contracts/api-v1.yaml, version 1.1):
    IO.21  {"request_id": str, "driver_id": str, "pool_id": str, "start": int, "end": int}
           Already screened by F.5.1 and rechecked for eligibility and closures by F.5.2.
           Minutes since midnight; the period is [start, end).
    IO.17  {"version": int, "pools": {pool_id: {"name": str, "capacity": int, "permits": list[str],
            "closures": list[{"start": int, "end": int}]}}}
    IO.8   {"reservation_id": str, "request_id": str, "driver_id": str, "pool_id": str,
            "start": int, "end": int, "status": "confirmed"}
    IO.18  list[IO.8]
    IO.22  {"request_id": str | None, "reason": "missing_data" | "not_eligible" | "closed" | "pool_full"}
"""


class CapacityLedger:
    """C.5.3 Capacity Ledger: the saved reservations and their capacity holds."""

    def __init__(self):
        raise NotImplementedError

    def records(self) -> list:
        """Every saved reservation (IO.18)."""
        raise NotImplementedError


def commit_capacity_hold(eligible_booking_request: dict, *, approved_rules: dict,
                         ledger: CapacityLedger) -> tuple:
    """in: IO.21. control: IO.17. mechanism: ledger (C.5.3).
    out: (IO.8 or None, IO.18, IO.22 or None). Exactly one of IO.8 and IO.22 is not None.
    """
    raise NotImplementedError
```
