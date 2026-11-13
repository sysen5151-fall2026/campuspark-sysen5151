"""Persistent bookings for C.5.3. One write transaction protects the final place."""

import pathlib
import sqlite3
import threading

from functions.f5_recheck_and_record_reservation import _peak_held

SCHEMA = pathlib.Path(__file__).with_name("schema.sql")
FIELDS = ("reservation_id", "request_id", "driver_id", "pool_id", "start", "end", "status")
_SELECT = 'SELECT reservation_id, request_id, driver_id, pool_id, start, "end", status FROM reservations'


class SqliteReservationStore:
    """Saved reservations in a SQLite database file, or in memory when path is ":memory:"."""

    def __init__(self, path=":memory:"):
        self._lock = threading.RLock()
        self._db = sqlite3.connect(str(path), check_same_thread=False)
        self._db.executescript(SCHEMA.read_text())

    def all(self) -> list:
        """Every saved reservation, oldest first (IO.18)."""
        with self._lock:
            return [dict(zip(FIELDS, row)) for row in self._db.execute(_SELECT + " ORDER BY rowid")]

    def saved_for(self, request_id):
        """The saved reservation for this request_id, or None."""
        with self._lock:
            row = self._db.execute(_SELECT + " WHERE request_id = ?", (request_id,)).fetchone()
        return dict(zip(FIELDS, row)) if row else None

    def save(self, request):
        """Save a confirmed reservation for the request and return it (IO.8)."""
        with self._lock, self._db:
            self._db.execute("BEGIN IMMEDIATE")
            return self._insert(request)

    def _commit(self, request, capacity):
        """Run the C.5.3 check and hold under the same database write lock."""
        with self._lock, self._db:
            self._db.execute("BEGIN IMMEDIATE")
            records = self.all()
            saved = self.saved_for(request["request_id"])
            if saved is not None:
                return saved, None, records
            if capacity is None:
                return None, "missing_data", records
            if _peak_held(records, request["pool_id"], request["start"], request["end"]) >= capacity:
                return None, "pool_full", records
            saved = self._insert(request)
            return saved, None, records + [saved]

    def _insert(self, request):
        number = self._db.execute("SELECT COUNT(*) FROM reservations").fetchone()[0] + 1
        record = {"reservation_id": "RES-%05d" % number, "request_id": request["request_id"],
                  "driver_id": request["driver_id"], "pool_id": request["pool_id"],
                  "start": request["start"], "end": request["end"], "status": "confirmed"}
        self._db.execute('INSERT INTO reservations (reservation_id, request_id, driver_id, pool_id, '
                         'start, "end", status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                         tuple(record[f] for f in FIELDS))
        return record

    def close(self):
        with self._lock:
            self._db.close()
