"""Spec IR JSON schema and validation."""
from typing import Any

SPEC_IR_SCHEMA = {
    "module_name": str,
    "description": str,
    "inputs": list,
    "outputs": list,
    "clock": (str, type(None)),
    "reset": (str, type(None)),
    "truth_table": (list, type(None)),
    "fsm_states": (list, type(None)),
    "fsm_transitions": (list, type(None)),
    "invariants": (list, type(None)),
    "latency": (int, type(None)),
    "source": str,
}

ACTION_TYPES = [
    "FIX_PARSE",
    "FIX_PORTS",
    "FIX_WIDTH",
    "FIX_TYPE",
    "FIX_FUNCTION",
    "FIX_RESET",
    "FIX_TIMING",
    "ASK_CLARIFICATION",
]


def validate_spec_ir(spec: dict) -> tuple[bool, list[str]]:
    """
    Validate Spec IR structure.
    Returns (valid, list of error messages).
    """
    errors = []
    if not isinstance(spec, dict):
        return False, ["Spec IR must be a dict"]

    required = ["module_name", "description", "inputs", "outputs"]
    for field in required:
        if field not in spec:
            errors.append(f"Missing required field: {field}")

    if "source" not in spec:
        spec["source"] = "text"

    if spec.get("source") not in ("paper", "text"):
        spec["source"] = "text"

    if "clock" not in spec:
        spec["clock"] = None
    if "reset" not in spec:
        spec["reset"] = None
    if "truth_table" not in spec:
        spec["truth_table"] = None
    if "fsm_states" not in spec:
        spec["fsm_states"] = None
    if "fsm_transitions" not in spec:
        spec["fsm_transitions"] = None
    if "invariants" not in spec:
        spec["invariants"] = None
    if "latency" not in spec:
        spec["latency"] = None

    return len(errors) == 0, errors


def spec_ir_to_summary(spec: dict) -> str:
    """Convert Spec IR to human-readable summary for prompts."""
    lines = [
        f"MODULE: {spec.get('module_name', 'unknown')}",
        f"DESCRIPTION: {spec.get('description', '')}",
        f"INPUTS: {spec.get('inputs', [])}",
        f"OUTPUTS: {spec.get('outputs', [])}",
    ]
    if spec.get("clock"):
        lines.append(f"CLOCK: {spec['clock']}")
    if spec.get("reset"):
        lines.append(f"RESET: {spec['reset']}")
    if spec.get("truth_table"):
        lines.append(f"TRUTH TABLE: {spec['truth_table']}")
    if spec.get("fsm_states"):
        lines.append(f"FSM STATES: {spec['fsm_states']}")
    if spec.get("fsm_transitions"):
        lines.append(f"FSM TRANSITIONS: {spec['fsm_transitions']}")
    if spec.get("invariants"):
        lines.append(f"INVARIANTS: {spec['invariants']}")
    return "\n".join(lines)
