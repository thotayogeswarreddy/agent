#!/usr/bin/env python3
"""
Run RTL Agent v3 locally.
Set GOOGLE_API_KEY or GEMINI_API_KEY in environment.

Usage:
  export GOOGLE_API_KEY=your_key
  python run_local.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import google.generativeai as genai

from config import API_KEY, TEXT_MODEL, VISION_MODEL, WORK_DIR, MAX_RETRIES
from input_layer import extract_from_pdf, extract_from_pdf_bytes, extract_from_text
from pipeline import run_pipeline


def main():
    api_key = API_KEY or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Error: Set GOOGLE_API_KEY or GEMINI_API_KEY in environment.")
        sys.exit(1)

    genai.configure(api_key=api_key)
    text_model = genai.GenerativeModel(TEXT_MODEL)
    vision_model = genai.GenerativeModel(VISION_MODEL)

    work_dir = Path(__file__).parent / "work"
    work_dir.mkdir(exist_ok=True)

    print("=" * 60)
    print("RTL AGENT PIPELINE v3 - Local")
    print("=" * 60)
    print("[1] Type / paste hardware description (END to finish)")
    print("[2] PDF file path")
    choice = input("\nChoice (1 or 2): ").strip()

    if choice == "2":
        pdf_path = input("PDF path: ").strip()
        spec_ir, summary = extract_from_pdf(pdf_path, vision_model)
    else:
        print("\nPaste description, type END on new line when done:\n")
        lines = []
        while True:
            line = input()
            if line.strip().upper() == "END":
                break
            lines.append(line)
        raw = "\n".join(lines)
        spec_ir, summary = extract_from_text(raw, text_model)

    if not spec_ir.get("module_name"):
        print("No valid spec. Exiting.")
        sys.exit(1)

    print(f"\n📝 Spec: {spec_ir.get('module_name', '?')}")
    print("-" * 40)
    print(summary[:500] + ("..." if len(summary) > 500 else ""))
    print("-" * 40)

    state = run_pipeline(
        spec_ir,
        text_model,
        work_dir=work_dir,
        max_retries=MAX_RETRIES,
        run_post_pass=True,
    )
    return state


if __name__ == "__main__":
    main()
