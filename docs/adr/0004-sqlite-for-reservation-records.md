# ADR-0004: SQLite for the reservation records

Status: Accepted (2026-10-26)

Context: Saved reservations were a list in process memory, so a restart lost every booking.
Chapter 8 replaces that stub with a data access component behind the interface F.5 already uses.
The pilot runs on one machine, has no budget for a hosted database (2.5.1 No Paid Licenses), and
must keep driver data on that machine.

Decision: SQLite through Python's standard `sqlite3` module, one table defined in
`data/schema.sql` with only the RS.2.1 fields. `data/reservation_db.py` implements the same
`all`, `saved_for` and `save` methods as the in-memory store, so F.5 runs on either.

Consequences: No new dependency and no server to run. A UNIQUE constraint on `request_id` backs up
the one-commitment-per-request rule even if a caller skips the check. SQLite serializes writers,
but F.5 still checks capacity before it saves, so the capacity rule is not yet atomic; that is the
job of C.5.3 Capacity Ledger.

Model entities affected: C.5, IO.8, IO.18, RS.2.1.
