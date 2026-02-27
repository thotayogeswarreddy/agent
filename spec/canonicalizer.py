"""Spec Canonicalizer - raw text/images → Spec IR (single LLM call)."""
import json
import re
from typing import Any


def _strip_markdown(raw: str) -> str:
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE)
    return raw.strip()


def canonicalize_from_text(raw_text: str, model) -> tuple[dict, str]:
    """
    Canonicalize freeform text into Spec IR.
    Returns (spec_ir, summary).
    Single LLM call.
    """
    prompt = f"""You are an expert hardware design engineer. Extract a structured hardware specification from this description.

TEXT:
{raw_text}

Output ONLY valid JSON in this exact format (no markdown, no backticks):
{{
  "module_name": "<module name>",
  "description": "<what the circuit does>",
  "inputs": [{{"name": "<port>", "width": <bits>, "description": "<optional>"}}],
  "outputs": [{{"name": "<port>", "width": <bits>, "description": "<optional>"}}],
  "clock": "<clk port or null>",
  "reset": "<reset port or null>",
  "truth_table": [[<in1>, <in2>, ...], <out>] or null,
  "fsm_states": ["S0", "S1", ...] or null,
  "fsm_transitions": [{{"from": "S0", "to": "S1", "cond": "x"}}] or null,
  "invariants": ["<property>"] or null,
  "latency": <cycles or null>,
  "source": "text"
}}

If truth tables or FSM details are in the text, include them. Use null for missing optional fields."""

    response = model.generate_content(prompt)
    raw = _strip_markdown(response.text.strip())
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError:
        spec = _fallback_spec(raw_text, "text")
    return spec, raw_text[:500]


def canonicalize_from_pdf(raw_text: str, images: list, vision_model) -> tuple[dict, str]:
    """
    Canonicalize PDF content (text + images) into Spec IR.
    Returns (spec_ir, summary).
    Single LLM call.
    """
    prompt = (
        "You are an expert hardware design engineer. Extract a structured hardware specification "
        "from this document (research paper, datasheet, etc.). Analyze ALL text and images: "
        "circuit diagrams, truth tables, timing diagrams, equations, FSM diagrams.\n\n"
        "Output ONLY valid JSON in this exact format (no markdown, no backticks):\n"
        '{\n'
        '  "module_name": "<module name>",\n'
        '  "description": "<what the circuit does>",\n'
        '  "inputs": [{"name": "<port>", "width": <bits>}],\n'
        '  "outputs": [{"name": "<port>", "width": <bits>}],\n'
        '  "clock": "<clk or null>",\n'
        '  "reset": "<reset or null>",\n'
        '  "truth_table": [[<inputs...>], <out>] or null,\n'
        '  "fsm_states": ["S0","S1"] or null,\n'
        '  "fsm_transitions": [{"from":"S0","to":"S1","cond":"x"}] or null,\n'
        '  "invariants": ["<property>"] or null,\n'
        '  "latency": <int or null>,\n'
        '  "source": "paper"\n'
        "}\n\n"
        f"EXTRACTED TEXT:\n{raw_text}"
    )
    content_parts = [prompt] + (images if images else [])
    response = vision_model.generate_content(content_parts)
    raw = _strip_markdown(response.text.strip())
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError:
        spec = _fallback_spec(raw_text, "paper")
    return spec, raw_text[:500]


def _fallback_spec(raw_text: str, source: str) -> dict:
    """Minimal Spec IR when JSON parse fails."""
    return {
        "module_name": "design",
        "description": raw_text[:500],
        "inputs": [],
        "outputs": [],
        "clock": None,
        "reset": None,
        "truth_table": None,
        "fsm_states": None,
        "fsm_transitions": None,
        "invariants": None,
        "latency": None,
        "source": source,
    }


def canonicalize(raw_text: str, model, images: list | None = None, source: str = "text") -> tuple[dict, str]:
    """
    Unified canonicalize. Use canonicalize_from_text or canonicalize_from_pdf directly
    for PDF vs text. This is a convenience wrapper.
    """
    if images:
        return canonicalize_from_pdf(raw_text, images, model)
    return canonicalize_from_text(raw_text, model)
