"""
scaling_analysis.py
====================
Studies how problem size (qubits/variables), QUBO density (interaction
terms -> two-qubit gates), and solver runtime scale with RNA sequence length.

Because gate-based QAOA on a classical simulator becomes impractically slow
well before real hardware limits would even bind (see benchmark.py: ~130s
for 9 qubits), this script:
  - measures QUBO size exactly (candidate pairs / variables, quadratic terms)
    across a range of lengths, with and without a max-span pruning window
  - runs the quantum-inspired (simulated annealing) solver across the full
    range, since it is the only backend that scales far enough to be
    informative
  - extrapolates approximate QAOA/annealer resource requirements from the
    measured QUBO size, rather than re-running QAOA at large n
"""

import sys, os, time, random
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import RNA

from qubo_builder import RNAFoldQUBO
from solvers import simulated_annealing_solve
from metrics import full_comparison

random.seed(7)
BASES = "AUCG"


def random_sequence(n):
    return "".join(random.choice(BASES) for _ in range(n))


LENGTHS = [10, 15, 20, 30, 40, 50, 60, 80, 100, 120, 150]


def main():
    rows = []
    for n in LENGTHS:
        seq = random_sequence(n)

        # --- unbounded span (full O(n^2)-candidate QUBO) ---
        t0 = time.time()
        qb_full = RNAFoldQUBO(seq, max_span=None)
        build_time_full = time.time() - t0
        n_vars_full = qb_full.num_variables
        n_quad_full = sum(1 for (a, b) in qb_full.Q if a != b)

        # --- banded / windowed pruning (max_span = 30), the standard trick
        #     for keeping long-sequence folding tractable classically AND
        #     on quantum hardware ---
        max_span = min(30, n - 1)
        qb_band = RNAFoldQUBO(seq, max_span=max_span)
        n_vars_band = qb_band.num_variables
        n_quad_band = sum(1 for (a, b) in qb_band.Q if a != b)

        # --- solve the banded QUBO with simulated annealing (quantum-inspired) ---
        sa_res = simulated_annealing_solve(qb_band, num_reads=300, num_sweeps=500, seed=3)
        sa_pairs = qb_band.repair_infeasible(qb_band.decode(sa_res["assignment"]))
        sa_db = qb_band.pairs_to_dotbracket(sa_pairs)
        cmp = full_comparison(seq, sa_db)

        # --- rough resource estimates for gate-based / annealer hardware ---
        # QAOA: 1 qubit per variable; each 2-body QUBO term -> one ZZ interaction
        # gate per QAOA layer (cost unitary), each layer also needs 1 single-qubit
        # rotation per qubit (mixer); depth grows ~ linearly with reps (p).
        p_layers = 3
        est_two_qubit_gates_per_layer = n_quad_band
        est_circuit_depth = p_layers * (2 + est_two_qubit_gates_per_layer / max(n_vars_band, 1))
        # D-Wave-style annealer: embedding overhead grows with the average
        # variable degree relative to hardware connectivity (~15-20 for Pegasus);
        # here we just report the graph density as a proxy signal.
        avg_degree = (2 * n_quad_band / n_vars_band) if n_vars_band > 0 else 0

        rows.append({
            "length_nt": n,
            "candidates_unbounded": n_vars_full,
            "quadratic_terms_unbounded": n_quad_full,
            "qubo_build_time_sec_unbounded": build_time_full,
            "candidates_banded_span30": n_vars_band,
            "quadratic_terms_banded": n_quad_band,
            "avg_variable_degree_banded": avg_degree,
            "est_qaoa_qubits": n_vars_band,
            "est_qaoa_circuit_depth_p3": est_circuit_depth,
            "sa_runtime_sec": sa_res["runtime_sec"],
            "sa_energy_gap_kcal": cmp["energy_gap_kcal"],
            "sa_f1_vs_mfe": cmp["f1"],
            "sa_feasible_rate": sa_res["extra"]["feasible_rate"],
        })
        print(f"n={n:4d}  vars(unbounded)={n_vars_full:5d}  vars(banded30)={n_vars_band:4d}  "
              f"quad(banded)={n_quad_band:5d}  SA time={sa_res['runtime_sec']:.3f}s  "
              f"gap={cmp['energy_gap_kcal']:.2f}  F1={cmp['f1']:.2f}")

    df = pd.DataFrame(rows)
    os.makedirs("results", exist_ok=True)
    df.to_csv("results/scaling_results.csv", index=False)
    with open("results/scaling_results.md", "w") as f:
        f.write("# Scaling Analysis Results\n\n")
        f.write(df.to_markdown(index=False))
    print("\nSaved results/scaling_results.csv and results/scaling_results.md")
    return df


if __name__ == "__main__":
    main()
