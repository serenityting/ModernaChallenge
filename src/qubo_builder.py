"""
qubo_builder.py
================
Formulates pseudoknot-free RNA secondary-structure (MFE) prediction as a QUBO.

Decision variable:
    x_(i,j) = 1  if nucleotides i and j (0-indexed, i < j) are base-paired
             0  otherwise

Objective (to MINIMIZE):
    H = H_energy + PENALTY_SHARED * H_shared_base + PENALTY_CROSS * H_crossing

H_energy rewards favorable pairs (GC > AU > GU) and rewards adjacent stacked
pairs (a first-order approximation of the Turner nearest-neighbor stacking
term), so the QUBO has genuine quadratic structure rather than degenerating
into an independent-set problem.

H_shared_base forbids any nucleotide from being used in more than one pair.
H_crossing forbids crossing (pseudoknotted) pairs, restricting the search to
nested structures -- the same solution space ViennaRNA's default MFE algorithm
explores, which keeps the comparison fair.

This module is solver-agnostic: it produces a plain dict-based QUBO
{(var_a, var_b): coeff} plus metadata, which is then handed to whichever
backend (simulated annealing, QAOA, brute force, D-Wave) the caller chooses.
"""

from dataclasses import dataclass, field
from itertools import combinations
from typing import Dict, List, Tuple

# ----------------------------------------------------------------------
# Base-pairing rules
# ----------------------------------------------------------------------

WC_PAIRS = {("A", "U"), ("U", "A"), ("G", "C"), ("C", "G")}
WOBBLE_PAIRS = {("G", "U"), ("U", "G")}

# Reward weights (larger = more favorable / more negative contribution).
# Loosely ordered the way real stacking free energies order (GC strongest).
PAIR_WEIGHT = {
    "GC": 3.0,
    "AU": 2.0,
    "GU": 1.0,
}

STACK_BONUS = 1.5   # extra reward when two candidate pairs are "stacked":
                     # (i, j) and (i+1, j-1) both present -> mimics stacking ΔG


def _pair_type(b1: str, b2: str) -> str:
    s = "".join(sorted([b1, b2]))
    if s == "CG":
        return "GC"
    if s == "AU":
        return "AU"
    if s == "GU":
        return "GU"
    raise ValueError(f"Not a canonical pair: {b1}{b2}")


def is_canonical_pair(b1: str, b2: str) -> bool:
    return (b1, b2) in WC_PAIRS or (b1, b2) in WOBBLE_PAIRS


@dataclass
class RNAFoldQUBO:
    sequence: str
    min_loop: int = 3          # minimum unpaired bases in a hairpin loop
    max_span: int = None       # optional cap on j - i (None = no cap)
    penalty_shared: float = 6.0
    penalty_crossing: float = 6.0

    candidate_pairs: List[Tuple[int, int]] = field(default_factory=list)
    var_index: Dict[Tuple[int, int], int] = field(default_factory=dict)
    Q: Dict[Tuple[int, int], float] = field(default_factory=dict)  # QUBO in variable-index space
    offset: float = 0.0

    def __post_init__(self):
        self.sequence = self.sequence.upper().replace("T", "U")
        self._enumerate_candidates()
        self._build_qubo()

    # ------------------------------------------------------------------
    def _enumerate_candidates(self):
        n = len(self.sequence)
        pairs = []
        for i, j in combinations(range(n), 2):
            if j - i - 1 < self.min_loop:
                continue
            if self.max_span is not None and (j - i) > self.max_span:
                continue
            b1, b2 = self.sequence[i], self.sequence[j]
            if is_canonical_pair(b1, b2):
                pairs.append((i, j))
        self.candidate_pairs = pairs
        self.var_index = {pair: k for k, pair in enumerate(pairs)}

    @property
    def num_variables(self) -> int:
        return len(self.candidate_pairs)

    # ------------------------------------------------------------------
    def _build_qubo(self):
        Q: Dict[Tuple[int, int], float] = {}

        def add(a, b, val):
            key = (a, b) if a <= b else (b, a)
            Q[key] = Q.get(key, 0.0) + val

        # --- energy reward terms (linear, on the diagonal) ---
        for (i, j) in self.candidate_pairs:
            v = self.var_index[(i, j)]
            ptype = _pair_type(self.sequence[i], self.sequence[j])
            w = PAIR_WEIGHT[ptype]
            add(v, v, -w)   # negative = reward (we minimize)

        # --- stacking bonus (quadratic): reward (i,j) & (i+1,j-1) together ---
        pair_set = set(self.candidate_pairs)
        for (i, j) in self.candidate_pairs:
            if (i + 1, j - 1) in pair_set:
                v1 = self.var_index[(i, j)]
                v2 = self.var_index[(i + 1, j - 1)]
                add(v1, v2, -STACK_BONUS)

        # --- constraint: no shared bases ---
        # any two candidate pairs that share an index are mutually exclusive
        n_pairs = len(self.candidate_pairs)
        for a in range(n_pairs):
            i1, j1 = self.candidate_pairs[a]
            for b in range(a + 1, n_pairs):
                i2, j2 = self.candidate_pairs[b]
                if len({i1, j1} & {i2, j2}) > 0:
                    add(a, b, self.penalty_shared)

        # --- constraint: no crossing (pseudoknot) pairs ---
        for a in range(n_pairs):
            i1, j1 = self.candidate_pairs[a]
            for b in range(a + 1, n_pairs):
                i2, j2 = self.candidate_pairs[b]
                if len({i1, j1} & {i2, j2}) > 0:
                    continue  # already penalized above
                if (i1 < i2 < j1 < j2) or (i2 < i1 < j2 < j1):
                    add(a, b, self.penalty_crossing)

        self.Q = Q

    # ------------------------------------------------------------------
    def to_dimod_bqm(self):
        import dimod
        linear = {}
        quadratic = {}
        for (a, b), coeff in self.Q.items():
            if a == b:
                linear[a] = linear.get(a, 0.0) + coeff
            else:
                quadratic[(a, b)] = quadratic.get((a, b), 0.0) + coeff
        for v in range(self.num_variables):
            linear.setdefault(v, 0.0)
        return dimod.BinaryQuadraticModel(linear, quadratic, self.offset, dimod.BINARY)

    # ------------------------------------------------------------------
    def decode(self, assignment: Dict[int, int]) -> List[Tuple[int, int]]:
        """Turn a {var_index: 0/1} assignment into a list of (i, j) base pairs."""
        return [self.candidate_pairs[v] for v, val in assignment.items() if val == 1]

    def pairs_to_dotbracket(self, pairs: List[Tuple[int, int]]) -> str:
        n = len(self.sequence)
        db = ["."] * n
        for (i, j) in pairs:
            db[i] = "("
            db[j] = ")"
        return "".join(db)

    def repair_infeasible(self, pairs: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
        Greedily resolve constraint violations (shared bases / crossings) by
        keeping the most favorable pairs first. Needed because penalty-method
        QUBOs solved heuristically can return infeasible samples.
        """
        def score(p):
            i, j = p
            ptype = _pair_type(self.sequence[i], self.sequence[j])
            return PAIR_WEIGHT[ptype]

        pairs_sorted = sorted(pairs, key=score, reverse=True)
        used_bases = set()
        kept: List[Tuple[int, int]] = []
        for (i, j) in pairs_sorted:
            if i in used_bases or j in used_bases:
                continue
            crosses = any((i < k < j < l) or (k < i < l < j) for (k, l) in kept)
            if crosses:
                continue
            kept.append((i, j))
            used_bases.add(i)
            used_bases.add(j)
        return sorted(kept)


if __name__ == "__main__":
    seq = "GGGAAAUCC"
    qb = RNAFoldQUBO(seq)
    print("Sequence:", seq)
    print("Candidate pairs:", qb.candidate_pairs)
    print("Num variables (qubits needed):", qb.num_variables)
    print("QUBO terms:", len(qb.Q))
