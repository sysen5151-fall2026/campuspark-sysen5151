"""F.1 Apply Parking Controls.

ICOM on the first-level IDEF0:
    control   IO.10 Parking Rules and Capacity          from X.F.2 Administer Parking Controls
    outputs   IO.17 Approved Parking Rules and Capacity to F.2, F.4, F.5, F.6, F.7 (as their control)
              IO.19 Control Change Result               to F.7
    no inputs: the work is driven by the administrator's change, which arrives as a control.
Mechanism: none on the first-level IDEF0 yet (assigned in Chapter 8). The current approved rule
set and the list of approved staff accounts live in an injected rules store.

Shapes (the interface contract in Chapter 7 replaces these notes):
    IO.10  {"account": str, "pool_id": str, "capacity": int | None, "permits": list[str] | None,
            "closures": list[{"start": int, "end": int}] | None}   None means "leave unchanged"
    IO.17  {"version": int, "pools": {pool_id: {"name": str, "capacity": int, "permits": list[str],
            "closures": list[{"start": int, "end": int}]}}}
    IO.19  {"accepted": bool, "reason": str | None, "version": int, "pool_id": str,
            "windows": list[{"start": int, "end": int}]}   windows = periods the change touched

The body was added in Chapter 5; the signatures and shapes above are unchanged.
"""

import copy

_DAY_END = 24 * 60


class RulesStore:
    """Holds the current approved rules and the approved staff accounts (SR.14)."""

    def __init__(self, pools: dict, approved_accounts: set):
        self._pools = copy.deepcopy(pools)
        self._approved_accounts = set(approved_accounts)
        self._version = 1
        # Rejected change attempts, kept in memory (1.4.1.1: "rejected and logged").
        self._log = []

    def current(self) -> dict:
        """The approved rule set now in force (IO.17)."""
        # A copy, so no caller can alter the rules every other function relies on (1.4.1.8).
        return {"version": self._version, "pools": copy.deepcopy(self._pools)}


def apply_parking_controls(*, parking_rules_and_capacity: dict, rules_store: RulesStore) -> tuple:
    """control: IO.10. mechanism: rules_store. out: (IO.17, IO.19)."""
    change = parking_rules_and_capacity if isinstance(parking_rules_and_capacity, dict) else {}
    pool_id = change.get("pool_id") if isinstance(change.get("pool_id"), str) else ""

    problem = _problem_with(change, rules_store)
    if problem is not None:
        rules_store._log.append({"account": change.get("account"), "pool_id": pool_id,
                                 "reason": problem, "version": rules_store._version})
        result = {"accepted": False, "reason": problem, "version": rules_store._version,
                  "pool_id": pool_id, "windows": []}
        return rules_store.current(), result

    pool = rules_store._pools[pool_id]
    capacity, permits, closures = change.get("capacity"), change.get("permits"), change.get("closures")
    # A new capacity or permit list applies to the pool all day, so it touches the whole day.
    whole_day = False
    if capacity is not None:
        whole_day = whole_day or capacity != pool.get("capacity")
        pool["capacity"] = capacity
    if permits is not None:
        whole_day = whole_day or set(permits) != set(pool.get("permits") or [])
        pool["permits"] = list(permits)
    windows = [{"start": 0, "end": _DAY_END}] if whole_day else []
    # A closure list replaces the old one; the closures it adds are the periods it touches.
    if closures is not None:
        new_closures = [{"start": w["start"], "end": w["end"]} for w in closures]
        old_closures = pool.get("closures") or []
        windows.extend(dict(w) for w in new_closures if w not in old_closures)
        pool["closures"] = new_closures
    rules_store._version += 1

    result = {"accepted": True, "reason": None, "version": rules_store._version,
              "pool_id": pool_id, "windows": windows}
    return rules_store.current(), result


def _problem_with(change, rules_store):
    """Why the change cannot be applied, or None when it can."""
    account = change.get("account")
    if not isinstance(account, str) or account not in rules_store._approved_accounts:
        return "account is not on the approved staff list; change rejected"
    pool_id = change.get("pool_id")
    if not isinstance(pool_id, str) or pool_id not in rules_store._pools:
        return "pool is not in the approved rules; change rejected"
    capacity = change.get("capacity")
    if capacity is not None and not (_is_int(capacity) and capacity >= 0):
        return "capacity must be a whole number of places, 0 or more; change rejected"
    permits = change.get("permits")
    if permits is not None and not (isinstance(permits, (list, tuple))
                                    and all(isinstance(p, str) and p.strip() for p in permits)):
        return "permits must be a list of permit names; change rejected"
    closures = change.get("closures")
    if closures is not None and not (isinstance(closures, (list, tuple))
                                     and all(_is_window(w) for w in closures)):
        return "each closure must be a period [start, end) within one day; change rejected"
    return None


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_window(window):
    return (isinstance(window, dict) and _is_int(window.get("start")) and _is_int(window.get("end"))
            and 0 <= window["start"] < window["end"] <= _DAY_END)
