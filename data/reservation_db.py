"""Data access component for C.5 Reservation Subsystem: saved reservations in SQLite.

Implements the store interface F.5 takes as its injected mechanism, the same three methods as
functions.f5_recheck_and_record_reservation.ReservationStore (all, saved_for, save), so F.5 runs
unchanged on either. The table is data/schema.sql and holds only the fields RS.2.1 allows.

Capacity is still checked by F.5 before it calls save(), so a check and a save are two steps here.
Doing both in one step is the job of C.5.3 Capacity Ledger (RS.1.4.3), built in Chapter 9.
"""

import pathlib
import sqlite3

SCHEMA = pathlib.Path(__file__).with_name("schema.sql")
FIELDS = ("reservation_id", "request_id", "driver_id", "pool_id", "start", "end", "status")
_SELECT = 'SELECT reservation_id, request_id, driver_id, pool_id, start, "end", status FROM reservations'


class SqliteReservationStore:
    """Saved reservations in a SQLite database file, or in memory when path is ":memory:"."""

    def __init__(self, path=":memory:"):
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.executescript(SCHEMA.read_text())

    def all(self) -> list:
        """Every saved reservation, oldest first (IO.18)."""
        return [dict(zip(FIELDS, row)) for row in self._db.execute(_SELECT + " ORDER BY rowid")]

    def saved_for(self, request_id):
        """The saved reservation for this request_id, or None."""
        row = self._db.execute(_SELECT + " WHERE request_id = ?", (request_id,)).fetchone()
        return dict(zip(FIELDS, row)) if row else None

    def save(self, request):
        """Save a confirmed reservation for the request and return it (IO.8)."""
        with self._db:
            number = self._db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] + 1
            record = {"reservation_id": "RES-%05d" % number, "request_id": request["request_id"],
                      "driver_id": request["driver_id"], "pool_id": request["pool_id"],
                      "start": request["start"], "end": request["end"], "status": "confirmed"}
            self._db.execute('INSERT INTO reservations (reservation_id, request_id, driver_id, pool_id, '
                             'start, "end", status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                             tuple(record[f] for f in FIELDS))
        return record

    def close(self):
        self._db.close()
