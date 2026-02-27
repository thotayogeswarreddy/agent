"""Icarus Verilog simulation - iverilog + vvp (open source, free)."""
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
        "cmd": " ".join(cmd),
        "returncode": result.returncode,
        "stdout": result.stdout.strip() if result.stdout else "",
        "stderr": result.stderr.strip() if result.stderr else "",
    }


def write_and_compile(
    rtl_code: str, tb_code: str, module_name: str, work_dir: Path
) -> tuple[dict, Path]:
    """Write Verilog files and compile with Icarus."""
    dut_file = work_dir / f"{module_name}.sv"
    tb_file = work_dir / f"tb_{module_name}.sv"
    sim_out = work_dir / "sim.out"

    dut_file.write_text(rtl_code)
    tb_file.write_text(tb_code)

    compile_result = run_cmd(
        ["iverilog", "-g2012", "-o", str(sim_out), dut_file.name, tb_file.name],
        cwd=work_dir,
    )
    return compile_result, sim_out


def run_simulation(sim_out: Path, work_dir: Path) -> dict:
    """Run compiled simulation binary (vvp)."""
    return run_cmd(["vvp", sim_out.name], cwd=work_dir)
