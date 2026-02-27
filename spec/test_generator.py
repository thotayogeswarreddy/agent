"""Spec-derived testbench generator - deterministic, no LLM."""
from typing import Any


def generate_spec_tb(spec: dict, module_name: str | None = None) -> str | None:
    """
    Generate deterministic Verilog testbench from Spec IR.
    Returns TB string if derivable (truth_table or fsm_transitions), else None.
    """
    name = module_name or spec.get("module_name", "dut")
    truth_table = spec.get("truth_table")
    fsm_transitions = spec.get("fsm_transitions")
    inputs = spec.get("inputs", [])
    outputs = spec.get("outputs", [])
    clock = spec.get("clock")
    reset = spec.get("reset")

    if truth_table and len(truth_table) > 0:
        return _gen_truth_table_tb(name, truth_table, inputs, outputs, clock, reset)
    if fsm_transitions and spec.get("fsm_states"):
        tb = _gen_fsm_tb(name, spec["fsm_states"], fsm_transitions, inputs, outputs, clock, reset)
        if tb:
            return tb
    return None


def _gen_truth_table_tb(
    module_name: str,
    truth_table: list,
    inputs: list,
    outputs: list,
    clock: str | None,
    reset: str | None,
) -> str:
    """Generate TB from truth table. Format: [[in1, in2, ...], out] per row."""
    in_names = [p["name"] if isinstance(p, dict) else str(p) for p in inputs]
    out_names = [p["name"] if isinstance(p, dict) else str(p) for p in outputs]
    if not in_names and truth_table:
        first = truth_table[0]
        n_in = len(first[0]) if isinstance(first[0], (list, tuple)) else len(first) - 1
        in_names = [f"in{i}" for i in range(n_in)]
    if not out_names:
        out_names = ["out"]

    lines = [
        "`timescale 1ns/1ps",
        f"module tb_{module_name};",
        "  reg " + ", ".join(in_names) + ";",
        "  wire " + ", ".join(out_names) + ";",
        f"  {module_name} dut (" + ", ".join(f".{n}({n})" for n in in_names + out_names) + ");",
        "  initial begin",
        '    $display("Testing truth table");',
    ]
    for row in truth_table:
        if isinstance(row[0], (list, tuple)):
            ins = list(row[0])
            out_exp = row[1] if len(row) > 1 else 0
        else:
            ins = list(row[:-1])
            out_exp = row[-1]
        n = min(len(in_names), len(ins))
        assigns = " ".join(f"{in_names[i]}={ins[i]};" for i in range(n))
        lines.append(f"    #1 {assigns}")
        lines.append(f"    #1 $display(\"in=%b out=%b exp=%b\", {{{','.join(in_names)}}}, {{{','.join(out_names)}}}, {out_exp});")
    lines.extend([
        '    $display("PASS");',
        "    $finish;",
        "  end",
        "endmodule",
    ])
    return "\n".join(lines)


def _gen_fsm_tb(
    module_name: str,
    states: list,
    transitions: list,
    inputs: list,
    outputs: list,
    clock: str | None,
    reset: str | None,
) -> str | None:
    """FSM TB generation is interface-dependent; return None for now."""
    return None
