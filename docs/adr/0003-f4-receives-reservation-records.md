# ADR-0003: F.4 receives IO.18 Reservation Records

Status: Accepted (2026-10-26), model update pending import

Context: Requirement 1.4.1.4 says F.4 shows only options that fit the remaining capacity. Remaining
capacity is the approved capacity (IO.17) minus the places already held, and the places held live in
the saved reservations that F.5 produces. On the first-level IDEF0 submitted for Chapters 6 and 7,
IO.18 goes from F.5 to F.7 only, so F.4 had no way to know what was held. The gap showed up when the
Chapter 4 signature for F.4 was written from its ICOMs: the requirement could not be met with the
inputs the model gave it.

Decision: F.4 receives IO.18 as a second input. The contract and the function signature already
include it. The Innoslate model gets the matching relationship (F.4 receives IO.18) in the Chapter 8
and 9 import.

Consequences: The first-level structure is no longer strictly feed-forward. The N² diagram gains one
cell below the diagonal (F.5 to F.4), which is a real feedback loop: options depend on bookings
already made. The Chapter 8 and 9 report records this as a change to the Chapter 7 architecture.

Model entities affected: F.4, F.5, IO.18, requirement 1.4.1.4.
