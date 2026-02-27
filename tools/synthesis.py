"""Yosys synthesis - area, cell count (open source, free)."""
import subprocess
from pathlib import Path


def run_cmd(cmd: list, cwd: Path | None = None, timeout: int = 60) -> dict:
    """Run shell command, return structured result."""
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


def run_synthesis(rtl_path: Path, work_dir: Path, top_module: str | None = None) -> dict:
    """
    Run Yosys: read_verilog, synth, stat.
    top_module: name of top module (default: filename stem).
    """
    rtl_name = rtl_path.name
    top = top_module or rtl_path.stem
    script = f"""
    read_verilog -sv {rtl_name}
    synth -top {top}
    stat -tech cmos
    """
    script_path = work_dir / "yosys_script.ys"
    script_path.write_text(script.strip())

    result = run_cmd(
        ["yosys", "-q", "-s", str(script_path)],
        cwd=work_dir,
    )
    return result
