"""
run_all.py
==========
Runs the entire submission pipeline end to end, in order:
  1. Curated benchmark (ViennaRNA vs SA / brute force / QAOA)
  2. Scaling analysis (qubit count, QUBO density, runtime vs length)
  3. Noise / sampling-budget robustness (optional advanced task)
  4. Figure generation

Usage:
    python3 src/run_all.py
    python3 src/run_all.py --skip-qaoa-noise   # skip the slower noisy-QAOA sweep
"""
import argparse
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import benchmark
import scaling_analysis


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-qaoa-noise", action="store_true",
                         help="Skip the noisy-QAOA sweep (slower, ~1-2 min)")
    args = parser.parse_args()

    print("\n########## STEP 1/4: Curated benchmark ##########")
    benchmark.main()

    print("\n########## STEP 2/4: Scaling analysis ##########")
    scaling_analysis.main()

    print("\n########## STEP 3/4: Noise / sampling robustness ##########")
    import noise_robustness
    df_sa = noise_robustness.sa_noise_sweep()
    df_sa.to_csv("results/sa_sampling_robustness.csv", index=False)
    if not args.skip_qaoa_noise:
        try:
            df_qaoa = noise_robustness.qaoa_depolarizing_noise_sweep()
            df_qaoa.to_csv("results/qaoa_noise_robustness.csv", index=False)
        except Exception as e:
            print(f"[warn] QAOA noise sweep failed/skipped: {e}")

    print("\n########## STEP 4/4: Figures ##########")
    # make_plots.py runs its logic at import time; import here, after results exist
    import make_plots  # noqa: F401

    print("\nAll done. See REPORT.md, results/, and figures/.")


if __name__ == "__main__":
    main()
