"""
RTL Agent Pipeline v3
Two-Oracle: Spec-derived TB (primary) + Icarus | Action-constrained repair
"""
import json
import shutil
from pathlib import Path

from config import MAX_RETRIES, WORK_DIR
from spec.schema import spec_ir_to_summary
from spec.test_generator import generate_spec_tb
from agents.writer import generate_rtl
from agents.reviewer import repair_rtl
from controller import classify_failure
from tools.simulator import write_and_compile, run_simulation
from tools.verilator import run_verilator
from tools.synthesis import run_synthesis
from tools.visualizer import run_visualize
from tools.metrics import parse_yosys_stat


def _banner(msg: str, char: str = "=") -> None:
    print(f"\n{char * 60}")
    print(f"  {msg}")
    print(f"{char * 60}")


def _verilator_available() -> bool:
    return shutil.which("verilator") is not None


def run_pipeline(
    spec_ir: dict,
    text_model,
    work_dir: Path | None = None,
    max_retries: int = MAX_RETRIES,
    run_post_pass: bool = True,
    use_verilator: bool = True,
) -> dict:
    """
    Main agent loop. Two-Oracle: spec-derived TB (primary) or LLM TB (fallback).
    Returns state dict with best_candidate, history, metrics, svg_path.
    """
    work_dir = work_dir or WORK_DIR
    work_dir.mkdir(parents=True, exist_ok=True)
    use_verilator = use_verilator and _verilator_available()

    state = {
        "best_candidate": None,
        "iteration": 0,
        "status": "INIT",
        "history": [],
        "metrics": {},
        "svg_path": None,
        "spec_ir": spec_ir,
    }

    summary = spec_ir_to_summary(spec_ir)
    spec_tb = generate_spec_tb(spec_ir)
    rtl_code = tb_code = module_name = None

    _banner("RTL AGENT PIPELINE v3 - Two-Oracle", "=")
    if spec_tb:
        print("📋 Spec-derived testbench available (primary oracle)")
    else:
        print("📋 Using LLM testbench (auxiliary oracle)")

    for attempt in range(1, max_retries + 1):
        state["iteration"] = attempt
        _banner(f"ITERATION {attempt} / {max_retries}", "-")

        # Step 1: Generate or Repair
        if attempt == 1:
            print("🤖 Writer Agent: Generating RTL + Testbench...")
            try:
                result = generate_rtl(spec_ir, text_model)
                rtl_code = result["rtl_code"]
                tb_code = result["testbench_code"]
                module_name = result["module_name"]
                print(f"  → Module: {module_name}")
                print(f"  → {result.get('explanation', '')[:200]}...")
            except Exception as e:
                print(f"❌ Generation failed: {e}")
                break
        else:
            prev = state["history"][-1]
            action_type = prev.get("action_type", "FIX_FUNCTION")
            print(f"🔧 Reviewer Agent: Repairing ({action_type})...")
            try:
                result = repair_rtl(
                    spec_ir,
                    rtl_code,
                    tb_code,
                    prev["compile_result"],
                    prev["run_result"],
                    action_type,
                    attempt,
                    max_retries,
                    text_model,
                )
                rtl_code = result["rtl_code"]
                tb_code = result["testbench_code"]
                module_name = result.get("module_name", module_name)
                print(f"  → Changes: {result.get('changes_made', '')[:300]}...")
            except Exception as e:
                print(f"❌ Repair failed: {e}")
                break

        # Use spec-derived TB if available, else LLM TB
        active_tb = spec_tb if spec_tb else tb_code

        # Step 2: Verilator (optional, fast lint)
        verilator_result = None
        if use_verilator:
            dut_path = work_dir / f"{module_name}.sv"
            dut_path.write_text(rtl_code)
            print("\n⚙️  Tool: Verilator lint...")
            verilator_result = run_verilator(dut_path, work_dir, module_name)
            if verilator_result["returncode"] != 0:
                print(f"   Verilator: {verilator_result['stderr'][:300]}...")

        # Step 3: Icarus compile + simulate
        print("\n⚙️  Tool: Icarus compile...")
        compile_result, sim_out = write_and_compile(
            rtl_code, active_tb, module_name, work_dir
        )
        print(f"   Return code: {compile_result['returncode']}")
        if compile_result["stderr"]:
            print(f"   Stderr: {compile_result['stderr'][:400]}...")

        run_result = None
        if compile_result["returncode"] == 0:
            print("\n⚙️  Tool: vvp simulation...")
            run_result = run_simulation(sim_out, work_dir)
            print(f"   Return code: {run_result['returncode']}")
            print(f"   Output: {run_result['stdout'][:600]}...")

        # Step 4: Controller classifies failure
        action_type = classify_failure(verilator_result, compile_result, run_result)
        if compile_result["returncode"] == 0 and (not run_result or run_result["returncode"] == 0):
            status = "PASS"
        else:
            status = "FAIL"

        state["status"] = status
        state["history"].append({
            "attempt": attempt,
            "status": status,
            "action_type": action_type,
            "verilator_result": verilator_result,
            "compile_result": compile_result,
            "run_result": run_result,
            "rtl_code": rtl_code,
            "tb_code": tb_code,
            "module_name": module_name,
        })

        print(f"\n📊 Decision: {status} (action: {action_type})")

        if status == "PASS":
            state["best_candidate"] = state["history"][-1]
            print("✅ Verification passed. Running post-pass...")

            if run_post_pass:
                dut_path = work_dir / f"{module_name}.sv"
                if dut_path.exists():
                    print("\n⚙️  Tool: Yosys synthesis...")
                    syn_result = run_synthesis(dut_path, work_dir, top_module=module_name)
                    if syn_result["returncode"] == 0:
                        state["metrics"] = parse_yosys_stat(syn_result["stdout"])
                        print(f"   Metrics: {state['metrics']}")

                    print("\n⚙️  Tool: Yosys show (circuit diagram)...")
                    vis_result = run_visualize(dut_path, work_dir, top_module=module_name)
                    if vis_result.get("svg_path"):
                        state["svg_path"] = vis_result["svg_path"]
                        print(f"   SVG: {vis_result['svg_path']}")
            break
        elif attempt == max_retries:
            print(f"⛔ Max retries ({max_retries}) reached.")
            for h in reversed(state["history"]):
                if h["compile_result"]["returncode"] == 0:
                    state["best_candidate"] = h
                    break
        else:
            print(f"🔄 Sending to Reviewer ({action_type})...")

    # Final report
    _banner("FINAL REPORT")
    print(f"Status:      {state['status']}")
    print(f"Iterations:  {state['iteration']} / {max_retries}")

    if state["best_candidate"]:
        best = state["best_candidate"]
        print(f"Best: Attempt {best['attempt']} ({best['status']})")

        final_dut = work_dir / "final_dut.sv"
        final_tb = work_dir / "final_tb.sv"
        final_dut.write_text(best["rtl_code"])
        final_tb.write_text(best["tb_code"])
        print(f"\n💾 Saved: {final_dut}, {final_tb}")

        if state["metrics"]:
            print(f"\n📐 Metrics: {state['metrics']}")
        if state["svg_path"]:
            print(f"🖼️  Diagram: {state['svg_path']}")

        print("\n--- RTL (excerpt) ---")
        print(best["rtl_code"][:1200] + ("..." if len(best["rtl_code"]) > 1200 else ""))
    else:
        print("❌ No passing candidate found.")

    feedback = {
        "final_status": state["status"],
        "total_iterations": state["iteration"],
        "metrics": state["metrics"],
        "svg_path": state["svg_path"],
        "spec_derived_tb": spec_tb is not None,
        "history": [
            {
                "attempt": h["attempt"],
                "status": h["status"],
                "action_type": h.get("action_type"),
                "compile_rc": h["compile_result"]["returncode"],
                "sim_rc": h["run_result"]["returncode"] if h["run_result"] else None,
            }
            for h in state["history"]
        ],
    }
    print("\n--- Feedback ---")
    print(json.dumps(feedback, indent=2))
    return state
