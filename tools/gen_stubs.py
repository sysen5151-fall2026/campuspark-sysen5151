"""Generate typed shapes and function stubs from contracts/api-v1.yaml.

    python tools/gen_stubs.py

Writes contracts/generated/flows.py (one TypedDict per schema) and contracts/generated/stubs.py
(one signature-only function per operation). The contract is the authority: change the contract and
regenerate, never edit the generated files by hand. tests/test_contract_conformance.py checks that
the modules under functions/ keep the generated signatures.
"""
import pathlib
import re

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "api-v1.yaml"
OUT = ROOT / "contracts" / "generated"
HEADER = '"""GENERATED from contracts/api-v1.yaml by tools/gen_stubs.py. Do not edit by hand."""\n'

PY = {"string": "str", "integer": "int", "boolean": "bool", "number": "float"}


def snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def ref_name(ref):
    return ref.rsplit("/", 1)[-1]


def py_type(spec):
    if "$ref" in spec:
        t = ref_name(spec["$ref"])
    elif spec.get("type") == "array":
        t = f"List[{py_type(spec['items'])}]"
    elif spec.get("type") == "object" and "additionalProperties" in spec:
        t = f"Dict[str, {py_type(spec['additionalProperties'])}]"
    elif spec.get("type") == "object":
        t = "dict"
    else:
        t = PY[spec["type"]]
    return f"Optional[{t}]" if spec.get("nullable") else t


def build_flows(schemas):
    lines = [HEADER, "from typing import Dict, List, Optional, TypedDict\n"]
    order = list(schemas)
    # emit dependencies first so the module imports cleanly
    done, emitted = set(), []

    def deps(spec):
        out = []
        if isinstance(spec, dict):
            if "$ref" in spec:
                out.append(ref_name(spec["$ref"]))
            for v in spec.values():
                out += deps(v)
        elif isinstance(spec, list):
            for v in spec:
                out += deps(v)
        return out

    def emit(name):
        if name in done:
            return
        done.add(name)
        for d in deps(schemas[name]):
            if d != name:
                emit(d)
        emitted.append(name)

    for n in order:
        emit(n)
    for name in emitted:
        s = schemas[name]
        io = s.get("x-io")
        tag = f"  # {io}" + (" (crosses the CampusPark boundary)" if s.get("x-external") else "") if io else ""
        if s.get("type") == "array":
            lines.append(f"{name} = {py_type(s)}{tag}\n")
            continue
        lines.append(f"\nclass {name}(TypedDict, total=False):{tag}")
        props = s.get("properties", {})
        if not props:
            lines.append("    pass")
        for p, ps in props.items():
            lines.append(f"    {p}: {py_type(ps)}")
        lines.append("")
    return "\n".join(lines) + "\n"


def build_stubs(paths):
    lines = [HEADER, "from typing import Any, List, Optional, Tuple\n", "from contracts.generated.flows import *  # noqa: F401,F403\n"]
    for path, ops in paths.items():
        op = ops["post"]
        body = op["requestBody"]["content"]["application/json"]["schema"]["properties"]
        pos = [(p, s) for p, s in body.items() if s.get("x-role") == "input"]
        kw = [(p, s) for p, s in body.items() if s.get("x-role") == "control"]
        mech = op.get("x-mechanism")
        resp = op["responses"]["200"]["content"]["application/json"]["schema"]
        if "$ref" in resp:
            ret = ref_name(resp["$ref"])
        else:
            parts = [py_type(s) for s in resp["properties"].values()]
            ret = f"Tuple[{', '.join(parts)}]"
        params = [f"{p}: {py_type(s)}" for p, s in pos]
        kwparams = [f"{p}: {py_type(s)}" for p, s in kw] + ([f"{mech}: Any"] if mech else [])
        sig = ", ".join(params + (["*"] + kwparams if kwparams else []))
        roles = "; ".join(f"{p} = {s.get('x-io')} ({s.get('x-role')})" for p, s in body.items())
        lines.append(f"\ndef {snake(op['operationId'])}({sig}) -> {ret}:")
        lines.append(f'    """{op["operationId"]} {path}. {op["summary"]}')
        lines.append(f"    {roles}." + (f" mechanism: {mech}." if mech else ""))
        lines.append(f'    Implemented in {op["x-module"]}."""')
        lines.append("    raise NotImplementedError\n")
    return "\n".join(lines) + "\n"


def main():
    spec = yaml.safe_load(CONTRACT.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "__init__.py").write_text(HEADER)
    (OUT / "flows.py").write_text(build_flows(spec["components"]["schemas"]))
    (OUT / "stubs.py").write_text(build_stubs(spec["paths"]))
    print("wrote", OUT / "flows.py", "and", OUT / "stubs.py")


if __name__ == "__main__":
    main()
