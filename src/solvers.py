"""
solvers.py
==========
Three solver backends for the RNA-folding QUBO built by qubo_builder.RNAFoldQUBO:

1. brute_force_solve   - exact enumeration, used only to validate small cases
2. simulated_annealing_solve - "quantum-inspired" classical heuristic (D-Wave neal)
3. qaoa_solve           - gate-based quantum optimization (Qiskit Aer simulator)

Each returns a dict:
    {
      "assignment": {var_idx: 0/1, ...},   # best sample found
      "energy": float,                     # QUBO objective value
      "runtime_sec": float,
      "num_variables": int,
      "extra": {...solver-specific diagnostics...}
    }
"""

import time
import itertools
import numpy as np


def _qubo_energy(Q, assignment, offset=0.0):
    e = offset
    for (a, b), coeff in Q.items():
        if a == b:
            e += coeff * assignment.get(a, 0)
        else:
            e += coeff * assignment.get(a, 0) * assignment.get(b, 0)
    return e


# ----------------------------------------------------------------------
def brute_force_solve(qb, max_vars=20):
    """
    Exact solve by exhaustive enumeration. Only tractable for num_variables
    up to ~20 (2^20 = ~1M evaluations). Used purely to sanity-check the
    heuristic/quantum solvers on small instances.
    """
    n = qb.num_variables
    if n > max_vars:
        raise ValueError(f"brute_force_solve: {n} variables exceeds max_vars={max_vars}")

    t0 = time.time()
    best_e = None
    best_assignment = None
    for bits in itertools.product([0, 1], repeat=n):
        assignment = dict(enumerate(bits))
        e = _qubo_energy(qb.Q, assignment, qb.offset)
        if best_e is None or e < best_e:
            best_e = e
            best_assignment = assignment
    runtime = time.time() - t0

    return {
        "assignment": best_assignment,
        "energy": best_e,
        "runtime_sec": runtime,
        "num_variables": n,
        "extra": {"method": "brute_force", "states_evaluated": 2 ** n},
    }


# ----------------------------------------------------------------------
def simulated_annealing_solve(qb, num_reads=500, num_sweeps=1000, seed=None):
    """
    Quantum-inspired classical solver: simulated annealing on the QUBO,
    using D-Wave's `neal` sampler. This is the strongest "practical today"
    baseline and scales to thousands of variables.
    """
    import neal

    bqm = qb.to_dimod_bqm()
    sampler = neal.SimulatedAnnealingSampler()

    t0 = time.time()
    sampleset = sampler.sample(bqm, num_reads=num_reads, num_sweeps=num_sweeps, seed=seed)
    runtime = time.time() - t0

    best = sampleset.first
    assignment = dict(best.sample)
    energy = best.energy

    # feasibility diagnostics across all reads
    num_feasible = 0
    for datum in sampleset.data(fields=["sample"]):
        pairs = qb.decode(dict(datum.sample))
        used = set()
        feasible = True
        for (i, j) in pairs:
            if i in used or j in used:
                feasible = False
                break
            used.add(i); used.add(j)
        if feasible:
            for a, (i1, j1) in enumerate(pairs):
                for (i2, j2) in pairs[a + 1:]:
                    if (i1 < i2 < j1 < j2) or (i2 < i1 < j2 < j1):
                        feasible = False
                        break
                if not feasible:
                    break
        if feasible:
            num_feasible += 1

    return {
        "assignment": assignment,
        "energy": energy,
        "runtime_sec": runtime,
        "num_variables": qb.num_variables,
        "extra": {
            "method": "simulated_annealing",
            "num_reads": num_reads,
            "num_sweeps": num_sweeps,
            "feasible_rate": num_feasible / num_reads,
        },
    }


# ----------------------------------------------------------------------
def qaoa_solve(qb, reps=3, maxiter=150, shots=2048, seed=42):
    """
    Gate-based QAOA on a local Aer simulator (no real QPU access needed).
    Practical only for small instances (roughly <= 18-20 qubits) on a
    simulator; real NISQ hardware would be limited similarly or further
    by connectivity/noise.
    """
    from qiskit_optimization import QuadraticProgram
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit.primitives import StatevectorSampler

    n = qb.num_variables
    qp = QuadraticProgram()
    for v in range(n):
        qp.binary_var(name=f"x{v}")

    linear = {}
    quadratic = {}
    for (a, b), coeff in qb.Q.items():
        if a == b:
            linear[f"x{a}"] = linear.get(f"x{a}", 0.0) + coeff
        else:
            key = (f"x{a}", f"x{b}")
            quadratic[key] = quadratic.get(key, 0.0) + coeff
    qp.minimize(linear=linear, quadratic=quadratic, constant=qb.offset)

    ising_op, ising_offset = qp.to_ising()

    t0 = time.time()
    sampler = StatevectorSampler(seed=seed)
    optimizer = COBYLA(maxiter=maxiter)
    qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=reps)
    result = qaoa.compute_minimum_eigenvalue(ising_op)
    runtime = time.time() - t0

    # Recover best bitstring from the optimal circuit by sampling
    from qiskit import QuantumCircuit
    circuit = qaoa.ansatz.assign_parameters(result.optimal_point)
    circuit.measure_all()
    sampler_run = StatevectorSampler(seed=seed)
    job = sampler_run.run([circuit], shots=shots)
    counts = job.result()[0].data.meas.get_counts()
    best_bitstring = max(counts, key=counts.get)

    # Qiskit bitstrings are little-endian relative to qubit order; map back
    assignment = {}
    bitstring_rev = best_bitstring[::-1]
    for v in range(n):
        assignment[v] = int(bitstring_rev[v])

    energy = _qubo_energy(qb.Q, assignment, qb.offset)

    return {
        "assignment": assignment,
        "energy": energy,
        "runtime_sec": runtime,
        "num_variables": n,
        "extra": {
            "method": "qaoa_simulator",
            "reps": reps,
            "maxiter": maxiter,
            "shots": shots,
            "optimal_eigenvalue": float(result.eigenvalue.real) + ising_offset,
            "circuit_depth": circuit.depth(),
            "num_qubits": circuit.num_qubits,
            "top_bitstring_counts": counts.get(best_bitstring, None),
        },
    }
