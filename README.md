# RTL Agent Pipeline v3

**Research Paper / NL → Spec IR → Two-Oracle Agent → RTL**

Automated RTL generation from research papers and technical PDFs via a Two-Oracle agent with spec-derived conformance checking and action-constrained repair.

## Structure

```
agent/
├── config.py              # API key (env), model names, paths
├── spec/
│   ├── schema.py          # Spec IR schema, validation, action types
│   ├── canonicalizer.py   # LLM → Spec IR (merged with extraction)
│   └── test_generator.py  # Spec IR → deterministic Verilog TB
├── agents/
│   ├── writer.py          # Generates RTL + auxiliary TB from Spec IR
│   └── reviewer.py       # Targeted repair (FIX_PARSE, FIX_WIDTH, etc.)
├── controller.py          # Failure classification, action routing (no LLM)
├── tools/
│   ├── verilator.py       # Verilator lint (fast syntax/semantic)
│   ├── simulator.py       # Icarus (iverilog + vvp)
│   ├── synthesis.py       # Yosys (area, cell count)
│   ├── visualizer.py      # Yosys show → SVG
│   ├── metrics.py         # Parse Yosys stat
│   └── formal.py          # SymbiYosys (optional)
├── input_layer.py         # PDF/text → Spec IR
├── pipeline.py            # Main loop (Two-Oracle)
├── run_local.py           # Local runner
└── rtl_agent_pipeline.ipynb
```

## Research Contributions

1. **Two-Oracle RTL Agent**: Simulation (Icarus) + spec-derived conformance (programmatic tests from Spec IR), reducing LLM co-adaptation.
2. **Action-constrained controller**: Rule-based failure classification and targeted repair prompts (FIX_PARSE, FIX_PORTS, FIX_WIDTH, FIX_FUNCTION, etc.).
3. **Spec IR–driven flow**: Structured spec extraction and deterministic test generation from Spec IR.

## Setup

### Colab

1. Open `rtl_agent_pipeline.ipynb` in Google Colab
2. Run Cell 1: Install iverilog, verilator, yosys, graphviz, pip packages
3. Run Cell 2: Add `GEMINI_API_KEY` in Colab Secrets
4. Run Cell 3: Load pipeline
5. Run Cell 4: Choose text or PDF input → run agent

### Local

```bash
# System tools (macOS: brew; Linux: apt)
# brew install icarus-verilog verilator yosys graphviz
# apt install iverilog verilator yosys graphviz

pip install -r requirements.txt
export GOOGLE_API_KEY=your_key
python run_local.py
```

## Tools (all open source, free)

- **Verilator** – fast syntax/semantic lint
- **Icarus Verilog** – simulation
- **Yosys** – synthesis, area, cell count, circuit diagram (SVG)
- **Graphviz** – for Yosys `show` command
- **SymbiYosys** – formal verification (optional)

## API Usage

Uses **Gemini 2.5 Flash-Lite** (15 RPM, 1000 RPD free tier). Set `GOOGLE_API_KEY` or `GEMINI_API_KEY` in environment.
