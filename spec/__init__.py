"""Spec IR - structured hardware specification for Two-Oracle agent."""
from .schema import SPEC_IR_SCHEMA, validate_spec_ir, spec_ir_to_summary, ACTION_TYPES
from .canonicalizer import canonicalize_from_text, canonicalize_from_pdf
from .test_generator import generate_spec_tb

__all__ = [
    "SPEC_IR_SCHEMA",
    "validate_spec_ir",
    "spec_ir_to_summary",
    "ACTION_TYPES",
    "canonicalize_from_text",
    "canonicalize_from_pdf",
    "generate_spec_tb",
]
