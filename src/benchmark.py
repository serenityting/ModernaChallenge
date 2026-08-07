"""
benchmark.py
============
End-to-end benchmark: for each test sequence, build the QUBO, solve with
simulated annealing (quantum-inspired) and, where small enough, brute force
(exact validation) and QAOA (gate-based simulator), then compare every
candidate structure against the ViennaRNA classical MFE reference.

Run:
    python3 src/benchmark.py
Produces:
    results/benchmark_results.csv
    results/benchmark_results.md
"""

import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
import RNA

from qubo_builder import RNAFoldQUBO
from solvers import brute_force_solve, simulated_annealing_solve, qaoa_solve
from metrics import full_comparison

# ----------------------------------------------------------------------
TEST_SEQUENCES = {
    "hairpin_9nt":        "GGGAAAUCC",
    "hairpin_16nt":       "GGGGAAAACCCCAAAA",
    "cloverleaf_like_22nt": "GGGCGCAAGGAUAAGCGCCCUU",
    "challenge_example_44nt": "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG",
}

BRUTE_FORCE_MAX_VARS = 18
QAOA_MAX_VARS = 10   # keep tiny: QAOA sim runtime grows fast (see scaling analysis)


def run_for_sequence(name, sequence, run_qaoa=None):
    print(f"\n=== {name} ({len(sequence)} nt) ===")
    ref_structure, ref_mfe = RNA.fold(sequence)
    print(f"ViennaRNA MFE: {ref_structure}  ({ref_mfe:.2f} kcal/mol)")

    qb = RNAFoldQUBO(sequence)
    n_vars = qb.num_variables
    print(f"Candidate pairs / qubits required: {n_vars}")

    rows = []

    # --- Simulated annealing (quantum-inspired) ---
    t0 = time.time()
    sa_res = simulated_annealing_solve(qb, num_reads=500, num_sweeps=1000, seed=1)
    sa_pairs_raw = qb.decode(sa_res["assignment"])
    sa_pairs = qb.repair_infeasible(sa_pairs_raw)
    sa_db = qb.pairs_to_dotbracket(sa_pairs)
    sa_cmp = full_comparison(sequence, sa_db)
    rows.append({
        "instance": name, "length": len(sequence), "method": "simulated_annealing",
        "num_qubits_or_vars": n_vars, "runtime_sec": sa_res["runtime_sec"],
        "feasible_rate": sa_res["extra"]["feasible_rate"],
        "was_repaired": sa_pairs_raw != sa_pairs,
        **sa_cmp,
    })
    print(f"[SA]    structure: {sa_db}   energy_gap={sa_cmp['energy_gap_kcal']:.2f} kcal/mol  "
          f"f1={sa_cmp['f1']:.2f}  runtime={sa_res['runtime_sec']:.3f}s "
          f"feasible_rate={sa_res['extra']['feasible_rate']:.2f}")

    # --- Brute force (exact QUBO optimum) for validation, only if small enough ---
    if n_vars <= BRUTE_FORCE_MAX_VARS:
        bf_res = brute_force_solve(qb, max_vars=BRUTE_FORCE_MAX_VARS)
        bf_pairs = qb.decode(bf_res["assignment"])  # guaranteed feasible (global opt of penalized QUBO)
        bf_db = qb.pairs_to_dotbracket(bf_pairs)
        bf_cmp = full_comparison(sequence, bf_db)
        rows.append({
            "instance": name, "length": len(sequence), "method": "brute_force_exact_qubo",
            "num_qubits_or_vars": n_vars, "runtime_sec": bf_res["runtime_sec"],
            "feasible_rate": 1.0, "was_repaired": False,
            **bf_cmp,
        })
        print(f"[BF]    structure: {bf_db}   energy_gap={bf_cmp['energy_gap_kcal']:.2f} kcal/mol  "
              f"f1={bf_cmp['f1']:.2f}  runtime={bf_res['runtime_sec']:.3f}s  "
              f"(matches SA QUBO optimum: {bf_res['energy'] <= sa_res['energy'] + 1e-6})")

    # --- QAOA (gate-based, simulator) only for very small instances ---
    do_qaoa = run_qaoa if run_qaoa is not None else (n_vars <= QAOA_MAX_VARS)
    if do_qaoa:
        qaoa_res = qaoa_solve(qb, reps=2, maxiter=80, shots=2048)
        qaoa_pairs_raw = qb.decode(qaoa_res["assignment"])
        qaoa_pairs = qb.repair_infeasible(qaoa_pairs_raw)
        qaoa_db = qb.pairs_to_dotbracket(qaoa_pairs)
        qaoa_cmp = full_comparison(sequence, qaoa_db)
        rows.append({
            "instance": name, "length": len(sequence), "method": "qaoa_simulator",
            "num_qubits_or_vars": qaoa_res["extra"]["num_qubits"],
            "runtime_sec": qaoa_res["runtime_sec"],
            "feasible_rate": None, "was_repaired": qaoa_pairs_raw != qaoa_pairs,
            **qaoa_cmp,
        })
        print(f"[QAOA]  structure: {qaoa_db}   energy_gap={qaoa_cmp['energy_gap_kcal']:.2f} kcal/mol  "
              f"f1={qaoa_cmp['f1']:.2f}  runtime={qaoa_res['runtime_sec']:.1f}s  "
              f"circuit_depth={qaoa_res['extra']['circuit_depth']}")

    return rows


def main():
    all_rows = []
    for name, seq in TEST_SEQUENCES.items():
        all_rows.extend(run_for_sequence(name, seq))

    df = pd.DataFrame(all_rows)
    os.makedirs("results", exist_ok=True)
    df.to_csv("results/benchmark_results.csv", index=False)

    with open("results/benchmark_results.md", "w") as f:
        f.write("# Benchmark Results\n\n")
        f.write(df.to_markdown(index=False))
    print("\nSaved results/benchmark_results.csv and results/benchmark_results.md")
    return df


if __name__ == "__main__":
    main()
