"""Formal verification - SymbiYosys (optional, open source)."""
import shutil
import subprocess
from pathlib import Path


def _sby_available() -> bool:
    return shutil.which("sby") is not None


def run_formal_check(
    rtl_path: Path,
    work_dir: Path,
    top_module: str | None = None,
    properties: list[str] | None = None,
) -> dict:
    """
    Run SymbiYosys formal check (if available).
    Returns {available, passed, counterexample, stderr}.
    """
    if not _sby_available():
        return {"available": False, "passed": None, "stderr": "SymbiYosys (sby) not installed"}

    top = top_module or rtl_path.stem
    sby_file = work_dir / "formal.sby"
    sby_content = f"""
[options]
mode bmc
depth 20

[engines]
smtbmc

[script]
read_verilog -sv {rtl_path.name}
prep -top {top}

[files]
{rtl_path.name}
"""
    sby_file.write_text(sby_content.strip())

    result = subprocess.run(
        ["sby", "-f", "formal.sby"],
        cwd=work_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "available": True,
        "passed": result.returncode == 0,
        "stderr": result.stderr or "",
        "stdout": result.stdout or "",
    }
