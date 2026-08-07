# ModernaChallenge
Aim:  To investigate whether quantum or quantum-inspired optimization methods can be used to formulate and explore the mRNA secondary-structure prediction problem. To reproduce known benchmark structures for small RNA sequences and analyze how quantum resource requirements scale with sequence length.
# Quantum-Inspired mRNA MFE Secondary-Structure Prediction

A working submission for the RNA-folding quantum optimization challenge: formulates
pseudoknot-free MFE secondary-structure prediction as a QUBO, solves it with a
quantum-inspired (simulated annealing) backend and a gate-based QAOA backend, and
benchmarks both against ViennaRNA's classical MFE reference.

**Start here:** [`REPORT.md`](REPORT.md) — the full write-up (background, formulation,
results, scaling analysis, noise robustness, future directions).

## Quick start

```bash
pip install ViennaRNA dwave-neal dimod qiskit qiskit-aer qiskit-algorithms \
            qiskit-optimization pandas matplotlib tabulate

python3 src/run_all.py               # full pipeline (~3-5 min)
python3 src/run_all.py --skip-qaoa-noise   # skip the slowest optional step
```

Or run pieces individually:

```bash
python3 src/qubo_builder.py       # sanity-check the QUBO construction on a toy sequence
python3 src/benchmark.py          # curated-sequence benchmark (Deliverables 2, 3, 5)
python3 src/scaling_analysis.py   # qubit/runtime scaling vs sequence length (Deliverable 6)
python3 src/noise_robustness.py   # optional advanced task: noise/sampling robustness
python3 src/make_plots.py         # regenerate figures/ from results/*.csv
```

## File guide

| File | Purpose |
|---|---|
| `src/qubo_builder.py` | Candidate base-pair enumeration + QUBO/Ising construction (the core formulation) |
| `src/solvers.py` | Brute-force (exact), simulated-annealing (quantum-inspired), and QAOA (gate-based) solvers |
| `src/metrics.py` | ViennaRNA-based energy evaluation + structural comparison metrics (BP distance, F1, MCC) |
| `src/benchmark.py` | Runs all solvers on curated test sequences, compares to ViennaRNA MFE |
| `src/scaling_analysis.py` | Qubit count / QUBO density / runtime vs. sequence length |
| `src/noise_robustness.py` | Optional advanced task: SA sampling-budget sweep + QAOA depolarizing-noise sweep |
| `src/make_plots.py` | Generates all figures from the results CSVs |
| `src/build_deck.js` | Regenerates `presentation.pptx` (run with `node src/build_deck.js`, requires `pptxgenjs`) |
| `src/run_all.py` | Orchestrates the full pipeline in one command |
| `results/*.csv`, `results/*.md` | Raw output tables |
| `figures/*.png` | Plots referenced in `REPORT.md` |
| `presentation.pptx` | Slide deck summarizing approach, results, and future directions |

## Requirements

- Python 3.10+
- `ViennaRNA` (classical benchmark)
- `dwave-neal`, `dimod` (quantum-inspired simulated annealing)
- `qiskit`, `qiskit-aer`, `qiskit-algorithms`, `qiskit-optimization` (gate-based QAOA + noise simulation)
- `pandas`, `matplotlib`, `tabulate` (results/plots)

No real quantum hardware or account credentials are required — everything runs on
local simulators, consistent with the challenge's stated allowance that "simulations
are sufficient."

## Known limitations (see REPORT.md §6.5 for full discussion)

- Pseudoknots are excluded by construction (matches ViennaRNA's default MFE algorithm).
- The QUBO energy model omits loop-length-dependent entropy terms present in the full
  Turner model — this is the primary source of the energy gap on non-trivial sequences.
- QAOA is demonstrated only in simulation and only up to ~9-10 qubits; see the scaling
  and noise-robustness sections for why this is a hard current ceiling, not an
  arbitrary choice.
