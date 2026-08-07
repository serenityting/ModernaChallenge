"""
noise_robustness.py
====================
Optional advanced task: evaluate robustness under sampling noise.

We can't easily access noisy real QPU hardware here, so we study the
noise-analogue that's actually available and meaningful for both backends:

1. For simulated annealing (quantum-inspired): sweep num_reads / num_sweeps
   down to emulate the sample-starved, short-anneal regime typical of
   near-term hardware, and measure how solution quality (energy gap, F1,
   feasible_rate) degrades.

2. For QAOA: emulate hardware noise using Qiskit Aer's built-in depolarizing
   noise model at a couple of gate error rates, on the smallest instance
   (hairpin_9nt), and compare against the noiseless simulator result.
"""

import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))

import pandas as pd
from qubo_builder import RNAFoldQUBO
from solvers import simulated_annealing_solve
from metrics import full_comparison

SEQ = "GGAGCAAAACUUGUCGAUUGAGAACAAAAUACAGAAUUUGCUUG"  # challenge example, 44 nt


def sa_noise_sweep():
    qb = RNAFoldQUBO(SEQ)
    settings = [
        (2000, 2000), (500, 1000), (200, 500), (50, 200), (20, 50), (5, 20),
    ]
    rows = []
    for reads, sweeps in settings:
        res = simulated_annealing_solve(qb, num_reads=reads, num_sweeps=sweeps, seed=11)
        pairs = qb.repair_infeasible(qb.decode(res["assignment"]))
        db = qb.pairs_to_dotbracket(pairs)
        cmp = full_comparison(SEQ, db)
        rows.append({
            "num_reads": reads, "num_sweeps": sweeps,
            "runtime_sec": res["runtime_sec"],
            "feasible_rate": res["extra"]["feasible_rate"],
            "energy_gap_kcal": cmp["energy_gap_kcal"],
            "f1": cmp["f1"],
        })
        print(f"reads={reads:5d} sweeps={sweeps:5d}  "
              f"gap={cmp['energy_gap_kcal']:6.2f} kcal/mol  F1={cmp['f1']:.2f}  "
              f"feasible_rate={res['extra']['feasible_rate']:.2f}  time={res['runtime_sec']:.3f}s")
    return pd.DataFrame(rows)


def qaoa_depolarizing_noise_sweep():
    """
    QAOA under depolarizing noise on the 9-nt hairpin.

    To isolate the effect of hardware noise (rather than re-running a fresh,
    noise-sensitive classical optimization loop each time -- itself a known
    NISQ pain point but a confound here), we fix a single set of QAOA
    parameters (from a decent noiseless run) and sweep gate-error rates,
    measuring how much the *sampled* solution quality degrades.
    """
    from qiskit import transpile
    from qiskit.circuit.library import QAOAAnsatz
    from qiskit.quantum_info import SparsePauliOp
    from qiskit_aer import AerSimulator
    from qiskit_aer.noise import NoiseModel, depolarizing_error
    from qiskit_optimization import QuadraticProgram

    seq = "GGGAAAUCC"
    qb = RNAFoldQUBO(seq)
    n = qb.num_variables

    qp = QuadraticProgram()
    for v in range(n):
        qp.binary_var(name=f"x{v}")
    linear, quadratic = {}, {}
    for (a, b), coeff in qb.Q.items():
        if a == b:
            linear[f"x{a}"] = linear.get(f"x{a}", 0.0) + coeff
        else:
            quadratic[(f"x{a}", f"x{b}")] = quadratic.get((f"x{a}", f"x{b}"), 0.0) + coeff
    qp.minimize(linear=linear, quadratic=quadratic)
    ising_op, ising_offset = qp.to_ising()

    reps = 2
    ansatz = QAOAAnsatz(cost_operator=ising_op, reps=reps)
    # Fixed, reasonable (not re-optimized) parameters: linear-ramp schedule,
    # a common QAOA warm-start heuristic when skipping full optimization.
    import numpy as np
    betas = np.linspace(0.8, 0.1, reps)
    gammas = np.linspace(0.1, 0.8, reps)
    params = np.concatenate([gammas, betas])
    bound = ansatz.assign_parameters(params)
    bound.measure_all()

    rows = []
    for p1 in [0.0, 0.01, 0.03, 0.05, 0.10]:
        backend = AerSimulator()
        if p1 > 0:
            noise_model = NoiseModel()
            err1 = depolarizing_error(p1, 1)
            err2 = depolarizing_error(min(p1 * 3, 0.5), 2)
            noise_model.add_all_qubit_quantum_error(err1, ["rz", "sx", "x", "u", "u1", "u2", "u3"])
            noise_model.add_all_qubit_quantum_error(err2, ["cx", "cz", "ecr"])
            backend = AerSimulator(noise_model=noise_model)

        t0 = time.time()
        tqc = transpile(bound, backend, optimization_level=1)
        job = backend.run(tqc, shots=4096, seed_simulator=42)
        counts = job.result().get_counts()
        runtime = time.time() - t0

        best_bitstring = max(counts, key=counts.get)
        bits_rev = best_bitstring.replace(" ", "")[::-1]
        assignment = {v: int(bits_rev[v]) for v in range(n)}
        pairs_raw = qb.decode(assignment)
        pairs = qb.repair_infeasible(pairs_raw)
        db = qb.pairs_to_dotbracket(pairs)
        cmp = full_comparison(seq, db)

        rows.append({
            "depolarizing_p1": p1,
            "runtime_sec": runtime,
            "top_bitstring_prob": counts[best_bitstring] / sum(counts.values()),
            "num_distinct_bitstrings": len(counts),
            "energy_gap_kcal": cmp["energy_gap_kcal"],
            "f1_vs_mfe": cmp["f1"],
        })
        print(f"p1={p1:.2f}  top_prob={counts[best_bitstring]/sum(counts.values()):.3f}  "
              f"distinct_outcomes={len(counts)}  gap={cmp['energy_gap_kcal']:.2f}  "
              f"F1={cmp['f1']:.2f}  time={runtime:.2f}s")

    return pd.DataFrame(rows)


if __name__ == "__main__":
    print("=== Simulated annealing: robustness to reduced sampling budget ===")
    df_sa = sa_noise_sweep()
    os.makedirs("results", exist_ok=True)
    df_sa.to_csv("results/sa_sampling_robustness.csv", index=False)

    print("\n=== QAOA: robustness to depolarizing gate noise (9-qubit hairpin) ===")
    try:
        df_qaoa = qaoa_depolarizing_noise_sweep()
        df_qaoa.to_csv("results/qaoa_noise_robustness.csv", index=False)
    except Exception as e:
        print(f"QAOA noise sweep skipped/failed: {e}")
