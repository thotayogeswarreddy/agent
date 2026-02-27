"""Verilator - fast syntax/semantic lint (open source, free)."""
import subprocess
from pathlib import Path


def run_cmd(cmd: list, cwd: Path | None = None, timeout: int = 30) -> dict:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return {
        "returncode": result.returncode,
        "stdout": result.stdout.strip() if result.stdout else "",
        "stderr": result.stderr.strip() if result.stderr else "",
    }


def run_verilator(rtl_path: Path, work_dir: Path, top_module: str | None = None) -> dict:
    """
    Run Verilator lint on RTL.
    Returns {returncode, stdout, stderr}.
    """
    top = top_module or rtl_path.stem
    # Verilator: --lint-only for static check, no codegen
    result = run_cmd(
        [
            "verilator",
            "--lint-only",
            "-Wall",
            "-Wno-fatal",
            "--top-module",
            top,
            str(rtl_path.name),
        ],
        cwd=work_dir,
    )
    return result
