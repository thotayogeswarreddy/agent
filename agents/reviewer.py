"""Reviewer Agent - targeted repair based on action type (no LLM for is_expected when spec-derived)."""
import json
import re

from spec.schema import spec_ir_to_summary
from controller import get_repair_focus


def repair_rtl(
    spec_ir: dict,
    rtl_code: str,
    tb_code: str,
    compile_result: dict,
    run_result: dict | None,
    action_type: str,
    attempt: int,
    max_retries: int,
    model,
) -> dict:
    """
    Ask LLM to fix RTL/TB based on failure. Uses action-specific focus.
    Returns dict with module_name, rtl_code, testbench_code, changes_made.
    """
    summary = spec_ir_to_summary(spec_ir)
    focus = get_repair_focus(action_type)

    compile_summary = (
        f"Return code: {compile_result['returncode']}\n"
        f"STDERR:\n{compile_result['stderr']}\n"
        f"STDOUT:\n{compile_result['stdout']}"
    )
    sim_summary = (
        f"Return code: {run_result['returncode']}\n"
        f"STDOUT:\n{run_result['stdout']}\n"
        f"STDERR:\n{run_result['stderr']}"
    ) if run_result else "Simulation did not run (compile failed)."

    prompt = f"""You are an expert RTL debug engineer.

SPECIFICATION:
{summary}

This is attempt {attempt} of {max_retries}. The verification failed.
FOCUS: {focus}
Fix ONLY what is broken. Do NOT rewrite from scratch unless necessary.
Use Icarus-compatible constructs (-g2012).

CURRENT RTL (DUT):
{rtl_code}

CURRENT TESTBENCH:
{tb_code}

COMPILE RESULT:
{compile_summary}

SIMULATION RESULT:
{sim_summary}

Respond ONLY in this JSON format:
{{
  "module_name": "<top module name>",
  "rtl_code": "<fixed Verilog/SV code for DUT>",
  "testbench_code": "<fixed Verilog/SV testbench code>",
  "changes_made": "<bullet list of what you changed>"
}}

Output ONLY the JSON. No markdown."""

    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE)
    return json.loads(raw)
