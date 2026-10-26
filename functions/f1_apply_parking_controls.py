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
"""


class RulesStore:
    """Holds the current approved rules and the approved staff accounts (SR.14)."""

    def __init__(self, pools: dict, approved_accounts: set):
        raise NotImplementedError

    def current(self) -> dict:
        """The approved rule set now in force (IO.17)."""
        raise NotImplementedError


def apply_parking_controls(*, parking_rules_and_capacity: dict, rules_store: RulesStore) -> tuple:
    """control: IO.10. mechanism: rules_store. out: (IO.17, IO.19)."""
    raise NotImplementedError
