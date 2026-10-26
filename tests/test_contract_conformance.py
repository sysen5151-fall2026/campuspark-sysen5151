"""The function modules keep the signatures generated from contracts/api-v1.yaml.

Chapter 7: the contract, not the code, is the authority on what crosses a boundary between
first-level functions. If this test fails, change the contract and regenerate the stubs
(python tools/gen_stubs.py), or bring the module back in line. Do not edit the generated files.
"""
import inspect

import pytest

from contracts.generated import stubs
from functions import (
    f1_apply_parking_controls as f1,
    f2_validate_trip_eligibility as f2,
    f3_gather_lot_location_and_route_data as f3,
    f4_present_eligible_parking_options as f4,
    f5_recheck_and_record_reservation as f5,
    f6_provide_confirmation_and_route_guidance as f6,
    f7_report_reservations_and_affected_bookings as f7,
)

IMPLEMENTATIONS = {
    "apply_parking_controls": f1,
    "validate_trip_eligibility": f2,
    "request_location_and_route": f3,
    "gather_lot_location_and_route_data": f3,
    "present_eligible_parking_options": f4,
    "recheck_and_record_reservation": f5,
    "provide_confirmation_and_route_guidance": f6,
    "report_reservations_and_affected_bookings": f7,
}


def shape(fn):
    return [(p.name, p.kind) for p in inspect.signature(fn).parameters.values()]


def test_every_contract_operation_has_an_implementation():
    generated = {n for n, f in inspect.getmembers(stubs, inspect.isfunction) if f.__module__ == stubs.__name__}
    assert generated == set(IMPLEMENTATIONS)


@pytest.mark.parametrize("name", sorted(IMPLEMENTATIONS))
def test_module_signature_matches_the_contract(name):
    assert shape(getattr(IMPLEMENTATIONS[name], name)) == shape(getattr(stubs, name))


# The internal flows of the first-level IDEF0 of F.0, with IO.18 also going to F.4 (ADR-0003).
MODEL_INTERNAL_FLOWS = {
    "IO.8": ("F.5", {"F.6"}),
    "IO.14": ("F.2", {"F.3"}),
    "IO.15": ("F.3", {"F.4"}),
    "IO.16": ("F.3", {"F.6"}),
    "IO.17": ("F.1", {"F.2", "F.4", "F.5", "F.6", "F.7"}),
    "IO.18": ("F.5", {"F.4", "F.7"}),
    "IO.19": ("F.1", {"F.7"}),
}


def test_every_internal_flow_in_the_model_has_a_schema():
    import pathlib

    import yaml

    contract = yaml.safe_load((pathlib.Path(__file__).resolve().parents[1] / "contracts" / "api-v1.yaml").read_text())
    flows = contract["x-internal-flows"]
    schemas = contract["components"]["schemas"]
    assert set(flows) == set(MODEL_INTERNAL_FLOWS)
    for io, (source, receivers) in MODEL_INTERNAL_FLOWS.items():
        assert flows[io]["from"] == source and set(flows[io]["to"]) == receivers, io
        assert schemas[flows[io]["schema"]]["x-io"] == io
