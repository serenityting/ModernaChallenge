"""
metrics.py
==========
Structural comparison metrics between a candidate structure (from a
quantum / quantum-inspired solver) and the ViennaRNA MFE reference.
"""

import math
import RNA


def eval_turner_energy(sequence: str, dotbracket: str) -> float:
    """True Turner-model free energy (kcal/mol) of a candidate structure,
    independent of whatever simplified energy model the QUBO used."""
    fc = RNA.fold_compound(sequence)
    return fc.eval_structure(dotbracket)


def mfe_reference(sequence: str):
    structure, mfe = RNA.fold(sequence)
    return structure, mfe


def dotbracket_to_pairs(db: str):
    stack = []
    pairs = set()
    for idx, ch in enumerate(db):
        if ch == "(":
            stack.append(idx)
        elif ch == ")":
            i = stack.pop()
            pairs.add((i, idx))
    return pairs


def base_pair_distance(db1: str, db2: str) -> int:
    p1, p2 = dotbracket_to_pairs(db1), dotbracket_to_pairs(db2)
    return len(p1.symmetric_difference(p2))


def pair_accuracy(candidate_db: str, reference_db: str) -> dict:
    """Sensitivity / PPV / F1 / MCC treating the reference (MFE) as ground truth."""
    n = len(reference_db)
    cand_pairs = dotbracket_to_pairs(candidate_db)
    ref_pairs = dotbracket_to_pairs(reference_db)

    tp = len(cand_pairs & ref_pairs)
    fp = len(cand_pairs - ref_pairs)
    fn = len(ref_pairs - cand_pairs)

    # unpaired-correct bases as an approx for TN in MCC (base-level, not pair-level)
    ref_paired_bases = set()
    for (i, j) in ref_pairs:
        ref_paired_bases.add(i); ref_paired_bases.add(j)
    cand_paired_bases = set()
    for (i, j) in cand_pairs:
        cand_paired_bases.add(i); cand_paired_bases.add(j)
    tn = n - len(ref_paired_bases | cand_paired_bases)

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else (1.0 if tp == 0 else 0.0)
    ppv = tp / (tp + fp) if (tp + fp) > 0 else (1.0 if tp == 0 else 0.0)
    f1 = (2 * sensitivity * ppv / (sensitivity + ppv)) if (sensitivity + ppv) > 0 else 0.0

    denom = math.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn) - (fp * fn)) / denom if denom > 0 else 0.0

    return {
        "true_positive_pairs": tp,
        "false_positive_pairs": fp,
        "false_negative_pairs": fn,
        "sensitivity": sensitivity,
        "ppv": ppv,
        "f1": f1,
        "mcc": mcc,
        "bp_distance": len(cand_pairs.symmetric_difference(ref_pairs)),
    }


def full_comparison(sequence: str, candidate_db: str):
    ref_db, ref_mfe = mfe_reference(sequence)
    cand_energy = eval_turner_energy(sequence, candidate_db)
    energy_gap = cand_energy - ref_mfe
    acc = pair_accuracy(candidate_db, ref_db)
    exact_match = candidate_db == ref_db
    return {
        "sequence": sequence,
        "reference_structure": ref_db,
        "reference_mfe_kcal": ref_mfe,
        "candidate_structure": candidate_db,
        "candidate_turner_energy_kcal": cand_energy,
        "energy_gap_kcal": energy_gap,
        "exact_match": exact_match,
        **acc,
    }


if __name__ == "__main__":
    seq = "GGGAAAUCC"
    cand = "(((...)))"
    result = full_comparison(seq, cand)
    for k, v in result.items():
        print(f"{k}: {v}")
