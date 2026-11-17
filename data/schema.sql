-- CampusPark saved reservations, the records C.5 Reservation Subsystem owns.
-- From the booking record in the docs/SPEC.md data contract, limited to the fields RS.2.1 allows:
-- reservation ID, request ID, identity reference, pool, booked period and status.
-- Times are minutes since midnight on one day; the period is the half-open interval [start, end).
-- A booking the driver cancels before it starts keeps its row with status 'cancelled' (SR.6), so its
-- places stop counting and its number is never reused. The SPEC's planned record also has dates and
-- condition text; neither has a function in the model yet, so they are not stored.

CREATE TABLE IF NOT EXISTS reservations (
    reservation_id TEXT PRIMARY KEY,
    request_id     TEXT NOT NULL UNIQUE,          -- one commitment per request ID (SR.4)
    driver_id      TEXT NOT NULL,                 -- identity reference from X.C.3, nothing more
    pool_id        TEXT NOT NULL,
    start          INTEGER NOT NULL CHECK (start >= 0 AND start < 1440),
    "end"          INTEGER NOT NULL CHECK ("end" > start AND "end" <= 1440),
    status         TEXT NOT NULL CHECK (status IN ('confirmed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS reservations_by_pool ON reservations (pool_id, start, "end");
