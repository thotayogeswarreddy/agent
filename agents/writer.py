"""Code Writer Agent - generates RTL + auxiliary testbench from Spec IR."""
import json
import re

from spec.schema import spec_ir_to_summary


def generate_rtl(spec_ir: dict, model) -> dict:
    """
    Ask LLM to generate RTL + auxiliary testbench from Spec IR.
    Returns dict with module_name, rtl_code, testbench_code, explanation.
    """
    summary = spec_ir_to_summary(spec_ir)
    prompt = f"""You are an expert RTL design engineer using SystemVerilog/Verilog.

Given this structured hardware specification, generate:
1. A synthesizable RTL module (DUT) that implements the spec exactly
2. A self-contained Icarus Verilog-compatible testbench that:
   - Instantiates the DUT
   - Applies test vectors (use truth_table if provided, else exhaustive/sampling)
   - Uses $display to print results
   - Ends with $finish
   - Uses only Icarus-compatible constructs (no $fatal, no assertions)

SPECIFICATION:
{summary}

Respond ONLY in this exact JSON format:
{{
  "module_name": "<top module name>",
  "rtl_code": "<full Verilog/SV code for DUT>",
  "testbench_code": "<full Verilog/SV testbench code>",
  "explanation": "<brief explanation of the design>"
}}

Output ONLY the JSON. No markdown, no backticks."""

    response = model.generate_content(prompt)
    raw = response.text.strip()
    raw = _strip_markdown(raw)
    return json.loads(raw)


def _strip_markdown(raw: str) -> str:
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE)
    return raw.strip()
