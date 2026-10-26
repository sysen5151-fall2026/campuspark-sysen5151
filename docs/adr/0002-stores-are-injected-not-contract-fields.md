# ADR-0002: Stores are injected mechanisms, not contract fields

Status: Accepted (2026-10-26)

Context: F.1 Apply Parking Controls and F.5 Recheck and Record Reservation both need state that
outlives one call: the approved rule set with the approved staff accounts, and the saved
reservations. The Chapter 4 signatures took each store as a keyword-only argument. When the
interface contract was written from the first-level IDEF0's flow list, no flow carries a store,
because a store is not information passing between two functions. It is the thing that performs the
function.

Decision: Stores stay out of the request and response schemas in `contracts/api-v1.yaml`. The
contract names them with `x-mechanism` on the two operations that need them, and the generated stubs
take them as keyword-only dependencies typed `Any`. In Chapter 8 they become the mechanisms of the
first-level subsystems (C.1 for the rules, C.5 for reservations), and the in-memory stores are
replaced by the data access component behind the same interface.

Consequences: Every internal flow in the contract is pure data, so the schemas can be checked
without knowing how anything is stored. The conformance test compares parameter names and kinds,
so a store parameter cannot be renamed or turned into a positional input without the contract
changing first.

Model entities affected: F.1, F.5; the Chapter 8 subsystem assets C.1 and C.5.
