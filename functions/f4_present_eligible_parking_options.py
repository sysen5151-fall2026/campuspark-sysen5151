"""F.4 Present Eligible Parking Options.

ICOM on the first-level IDEF0:
    input     IO.15 Candidate Parking Data                 from F.3
    controls  IO.3  Identity and Permit Eligibility        from X.F.3
              IO.17 Approved Parking Rules and Capacity    from F.1
    output    IO.6  Eligible Parking Options               to X.F.1
Finding while writing this signature: "remaining capacity" needs the places already held, and no
flow on the first-level IDEF0 brings them to F.4. The signature takes IO.18 Reservation Records as
a second input, and the model is being corrected to match (F.4 receives IO.18). See
docs/prompt-log.md, Chapter 4 entry.

Shapes:
    IO.18  list[IO.8]   saved reservations, see F.5
    IO.6   {"status": "OPTIONS_AVAILABLE" | "NO_OPTIONS", "reason": str | None,
            "options": list[{"pool_id": str, "name": str, "walk_minutes": int | None,
            "remaining": int, "capacity": int, "facts": list[str]}]}
           "facts" are the rule and trip facts used to select the option (SR.3)
"""


def present_eligible_parking_options(candidate_parking_data: dict, reservation_records: list, *,
                                     eligibility: dict, approved_rules: dict) -> dict:
    """in: IO.15, IO.18. controls: IO.3, IO.17. out: IO.6."""
    raise NotImplementedError
