"""Input layer - PDF or text to Spec IR (structured hardware specification)."""
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

from spec.canonicalizer import canonicalize_from_pdf, canonicalize_from_text
from spec.schema import validate_spec_ir, spec_ir_to_summary


def extract_from_pdf(pdf_path: str | Path, vision_model) -> tuple[dict, str]:
    """Extract from PDF, canonicalize to Spec IR. Returns (spec_ir, summary)."""
    pdf_path = Path(pdf_path)
    doc = fitz.open(pdf_path)
    all_text = ""
    all_images = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        all_text += f"\n--- Page {page_num + 1} ---\n"
        all_text += page.get_text()
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                base_img = doc.extract_image(xref)
                pil_img = Image.open(io.BytesIO(base_img["image"]))
                if pil_img.mode not in ("RGB", "L"):
                    pil_img = pil_img.convert("RGB")
                all_images.append(pil_img)
            except Exception:
                pass

    spec_ir, summary = canonicalize_from_pdf(all_text, all_images, vision_model)
    valid, _ = validate_spec_ir(spec_ir)
    if not valid:
        spec_ir["description"] = all_text[:1000]
    return spec_ir, spec_ir_to_summary(spec_ir)


def extract_from_pdf_bytes(pdf_bytes: bytes, vision_model) -> tuple[dict, str]:
    """Extract from PDF bytes (e.g. Colab upload). Returns (spec_ir, summary)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    all_text = ""
    all_images = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        all_text += f"\n--- Page {page_num + 1} ---\n"
        all_text += page.get_text()
        for img in page.get_images(full=True):
            try:
                base_img = doc.extract_image(img[0])
                pil_img = Image.open(io.BytesIO(base_img["image"]))
                if pil_img.mode not in ("RGB", "L"):
                    pil_img = pil_img.convert("RGB")
                all_images.append(pil_img)
            except Exception:
                pass

    spec_ir, summary = canonicalize_from_pdf(all_text, all_images, vision_model)
    valid, _ = validate_spec_ir(spec_ir)
    if not valid:
        spec_ir["description"] = all_text[:1000]
    return spec_ir, spec_ir_to_summary(spec_ir)


def extract_from_text(raw_text: str, text_model) -> tuple[dict, str]:
    """Canonicalize freeform text to Spec IR. Returns (spec_ir, summary)."""
    spec_ir, _ = canonicalize_from_text(raw_text, text_model)
    validate_spec_ir(spec_ir)
    return spec_ir, spec_ir_to_summary(spec_ir)
