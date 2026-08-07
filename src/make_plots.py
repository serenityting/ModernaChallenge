"""
make_plots.py
=============
Generates the figures used in the report/presentation from
results/scaling_results.csv and results/benchmark_results.csv.
"""

import pandas as pd
import matplotlib.pyplot as plt

scaling = pd.read_csv("results/scaling_results.csv")
bench = pd.read_csv("results/benchmark_results.csv")

plt.rcParams.update({"figure.dpi": 130, "font.size": 10})

# ---------------------------------------------------------------
# Fig 1: qubit / variable count vs sequence length (unbounded vs banded)
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(scaling.length_nt, scaling.candidates_unbounded, "o-", label="Unbounded candidate pairs (qubits)")
ax.plot(scaling.length_nt, scaling.candidates_banded_span30, "s-", label="Banded (max span=30) candidate pairs")
ax.set_xlabel("Sequence length (nt)")
ax.set_ylabel("Number of QUBO variables (qubits)")
ax.set_title("Qubit requirement vs. RNA sequence length")
ax.legend()
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("figures/fig1_qubit_scaling.png")
plt.close(fig)

# ---------------------------------------------------------------
# Fig 2: quadratic (two-qubit interaction) terms vs length -- proxy for
# circuit depth / annealer connectivity burden
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(scaling.length_nt, scaling.quadratic_terms_banded, "^-", color="darkorange")
ax.set_xlabel("Sequence length (nt)")
ax.set_ylabel("Quadratic terms (two-qubit interactions)")
ax.set_title("QUBO density vs. sequence length (banded, span ≤ 30)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("figures/fig2_quadratic_terms_scaling.png")
plt.close(fig)

# ---------------------------------------------------------------
# Fig 3: simulated annealing runtime vs length
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(scaling.length_nt, scaling.sa_runtime_sec, "o-", color="seagreen")
ax.set_xlabel("Sequence length (nt)")
ax.set_ylabel("Runtime (s)")
ax.set_title("Simulated-annealing (quantum-inspired) runtime vs. length\n(500 reads x 1000 sweeps)")
ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig("figures/fig3_sa_runtime_scaling.png")
plt.close(fig)

# ---------------------------------------------------------------
# Fig 4: energy gap and F1 vs length (quality degradation)
fig, ax1 = plt.subplots(figsize=(6.5, 4))
ax2 = ax1.twinx()
ax1.plot(scaling.length_nt, scaling.sa_energy_gap_kcal, "o-", color="crimson", label="Energy gap (kcal/mol)")
ax2.plot(scaling.length_nt, scaling.sa_f1_vs_mfe, "s--", color="steelblue", label="F1 vs MFE")
ax1.set_xlabel("Sequence length (nt)")
ax1.set_ylabel("Energy gap to true MFE (kcal/mol)", color="crimson")
ax2.set_ylabel("F1 score vs MFE reference", color="steelblue")
ax1.set_title("Structure-quality degradation vs. sequence length\n(random sequences, banded QUBO)")
fig.tight_layout()
fig.savefig("figures/fig4_quality_vs_length.png")
plt.close(fig)

# ---------------------------------------------------------------
# Fig 5: benchmark.py results -- energy gap by method for curated sequences
fig, ax = plt.subplots(figsize=(7, 4))
pivot = bench.pivot_table(index="instance", columns="method", values="energy_gap_kcal")
pivot.plot(kind="bar", ax=ax)
ax.set_ylabel("Energy gap to ViennaRNA MFE (kcal/mol)")
ax.set_title("Energy gap by solver, curated benchmark sequences")
ax.axhline(0, color="black", linewidth=0.8)
plt.xticks(rotation=20, ha="right")
fig.tight_layout()
fig.savefig("figures/fig5_benchmark_energy_gap.png")
plt.close(fig)

# ---------------------------------------------------------------
# Fig 6: runtime by method (log scale) for curated sequences
fig, ax = plt.subplots(figsize=(7, 4))
pivot2 = bench.pivot_table(index="instance", columns="method", values="runtime_sec")
pivot2.plot(kind="bar", ax=ax, logy=True)
ax.set_ylabel("Runtime (s, log scale)")
ax.set_title("Solver runtime by method, curated benchmark sequences")
plt.xticks(rotation=20, ha="right")
fig.tight_layout()
fig.savefig("figures/fig6_benchmark_runtime.png")
plt.close(fig)

print("Saved 6 figures to figures/")
