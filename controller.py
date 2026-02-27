"""Controller - failure classification and action routing (no LLM)."""
from spec.schema import ACTION_TYPES


def classify_failure(
    verilator_result: dict | None,
    icarus_compile: dict,
    icarus_sim: dict | None,
) -> str:
    """
    Classify failure from tool outputs.
    Returns action type: FIX_PARSE | FIX_PORTS | FIX_WIDTH | FIX_FUNCTION | FIX_RESET | FIX_TIMING | ASK_CLARIFICATION
    """
    # Verilator catches syntax/semantic early
    if verilator_result and verilator_result.get("returncode", 0) != 0:
        stderr = (verilator_result.get("stderr") or "").lower()
        if "port" in stderr or "connection" in stderr or "module" in stderr:
            return "FIX_PORTS"
        if "width" in stderr or "bit" in stderr or "size" in stderr:
            return "FIX_WIDTH"
        if "syntax" in stderr or "parse" in stderr or "unexpected" in stderr:
            return "FIX_PARSE"
        if "type" in stderr or "incompatible" in stderr:
            return "FIX_TYPE"
        return "FIX_PARSE"

    # Icarus compile failure
    if icarus_compile.get("returncode", 0) != 0:
        stderr = (icarus_compile.get("stderr") or "").lower()
        if "port" in stderr or "connection" in stderr:
            return "FIX_PORTS"
        if "width" in stderr or "bit" in stderr or "sized" in stderr:
            return "FIX_WIDTH"
        if "syntax" in stderr or "parse" in stderr or "unexpected" in stderr:
            return "FIX_PARSE"
        if "type" in stderr or "incompatible" in stderr:
            return "FIX_TYPE"
        return "FIX_PARSE"

    # Icarus sim failure (runtime)
    if icarus_sim and icarus_sim.get("returncode", 0) != 0:
        return "FIX_FUNCTION"

    # Sim passed but wrong output - would need spec comparison
    return "FIX_FUNCTION"


def get_repair_focus(action_type: str) -> str:
    """Return short focus hint for repair prompt."""
    focus = {
        "FIX_PARSE": "Fix syntax/parse errors. Check module structure, brackets, semicolons.",
        "FIX_PORTS": "Fix port/connection mismatches. Ensure DUT and TB port lists match.",
        "FIX_WIDTH": "Fix bit width mismatches. Check signal widths and assignments.",
        "FIX_TYPE": "Fix type mismatches. Check reg vs wire, signed vs unsigned.",
        "FIX_FUNCTION": "Fix functional/logic errors. Verify behavior matches specification.",
        "FIX_RESET": "Fix reset behavior. Check reset polarity and initial state.",
        "FIX_TIMING": "Fix timing. Check clock edges, delays, sequencing.",
        "ASK_CLARIFICATION": "Spec may be ambiguous. Proceed with best interpretation.",
    }
    return focus.get(action_type, "Fix the reported errors.")
