"""Optional: Run pipeline on benchmark (paper specs)."""
from pathlib import Path


def run_benchmark(specs_dir: Path, output_dir: Path, text_model, max_per_spec: int = 3) -> dict:
    """
    Run pipeline on each Spec IR in specs_dir.
    specs_dir: folder of JSON Spec IR files
    Returns aggregate results.
    """
    from pipeline import run_pipeline
    import json

    results = []
    for spec_file in Path(specs_dir).glob("*.json"):
        spec = json.loads(spec_file.read_text())
        state = run_pipeline(spec, text_model, work_dir=output_dir / spec_file.stem, max_retries=max_per_spec)
        results.append({"spec": spec_file.name, "status": state["status"], "iterations": state["iteration"]})
    return {"total": len(results), "passed": sum(1 for r in results if r["status"] == "PASS"), "results": results}
