const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5 in

// ---- Palette: "Midnight Executive" + sharp mint accent ----
const NAVY = "1E2761";
const ICE = "CADCFC";
const WHITE = "FFFFFF";
const MINT = "02C39A";
const INK = "1B1F3B";
const GRAY = "5B6178";

const FONT_HEAD = "Cambria";
const FONT_BODY = "Calibri";

function titleSlideBg(slide) {
  slide.background = { color: NAVY };
}

// ============================================================
// Slide 1 — Title
// ============================================================
{
  const s = pres.addSlide();
  titleSlideBg(s);
  s.addShape("rect", { x: 0, y: 0, w: 13.33, h: 7.5, fill: { color: NAVY } });

  // simple abstract motif: concentric arcs suggesting a stem-loop
  for (let i = 0; i < 4; i++) {
    s.addShape("ellipse", {
      x: 9.6 - i * 0.35, y: 1.0 + i * 0.35, w: 4.6 + i * 0.7, h: 4.6 + i * 0.7,
      line: { color: MINT, width: 1.2, transparency: 40 + i * 10 },
      fill: { type: "none" },
    });
  }

  s.addText("QUANTUM-INSPIRED PREDICTION OF", {
    x: 0.7, y: 2.15, w: 8.5, h: 0.5, fontFace: FONT_BODY, fontSize: 16,
    color: MINT, bold: true, charSpacing: 2,
  });
  s.addText("mRNA Secondary Structure", {
    x: 0.7, y: 2.6, w: 9.2, h: 1.1, fontFace: FONT_HEAD, fontSize: 40,
    color: WHITE, bold: true,
  });
  s.addText("A QUBO formulation of Minimum-Free-Energy folding, benchmarked against ViennaRNA", {
    x: 0.7, y: 3.65, w: 8.5, h: 0.6, fontFace: FONT_BODY, fontSize: 16,
    color: ICE, italic: true,
  });

  s.addText("QAOA  ·  Simulated Annealing  ·  ViennaRNA  ·  Qiskit  ·  D-Wave neal", {
    x: 0.7, y: 6.6, w: 9, h: 0.4, fontFace: FONT_BODY, fontSize: 12, color: ICE,
  });
}

// ============================================================
// Slide 2 — The problem
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("The Problem: Folding mRNA to Minimum Free Energy", {
    x: 0.6, y: 0.4, w: 12, h: 0.7, fontFace: FONT_HEAD, fontSize: 28, bold: true, color: NAVY,
  });

  const rows = [
    ["Biology", "RNA folds into stems, loops, and bulges via base pairing (A–U, G–C, G–U). This secondary structure governs mRNA stability, translation efficiency, and where regulatory factors can bind."],
    ["Notation", "Dot-bracket strings encode nested structure: \"(\" / \")\" mark paired bases, \".\" marks unpaired.  e.g.  ((((....)))).... "],
    ["Computation", "The Minimum Free Energy (MFE) structure minimizes a sum of stacking + loop-penalty terms. Classically solved exactly (nested case) by Zuker's O(n\u00b3) dynamic program \u2014 implemented in ViennaRNA, our ground truth throughout."],
    ["Our angle", "Recast MFE search as a QUBO: one binary variable per candidate base pair, solved with a quantum-inspired (simulated annealing) and a gate-based (QAOA) backend, then benchmarked against ViennaRNA."],
  ];

  let y = 1.35;
  const rowH = 1.35;
  rows.forEach(([label, body], i) => {
    s.addShape("ellipse", { x: 0.6, y: y + 0.05, w: 0.22, h: 0.22, fill: { color: i % 2 === 0 ? MINT : NAVY } });
    s.addText(label.toUpperCase(), {
      x: 0.95, y: y, w: 2.0, h: rowH - 0.25, fontFace: FONT_BODY, fontSize: 14, bold: true, color: NAVY, valign: "top",
    });
    s.addText(body, {
      x: 3.1, y: y, w: 9.6, h: rowH - 0.25, fontFace: FONT_BODY, fontSize: 13.5, color: INK, valign: "top", lineSpacingMultiple: 1.15,
    });
    y += rowH;
  });
}

// ============================================================
// Slide 3 — QUBO formulation
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Formulation: RNA Folding as a QUBO", {
    x: 0.6, y: 0.4, w: 12, h: 0.7, fontFace: FONT_HEAD, fontSize: 28, bold: true, color: NAVY,
  });

  s.addText("Variable:  x(i,j) \u2208 {0,1}  \u2192  1 if bases i,j pair", {
    x: 0.6, y: 1.25, w: 12, h: 0.4, fontFace: "Courier New", fontSize: 15, color: NAVY, bold: true,
  });

  s.addShape("roundRect", {
    x: 0.6, y: 1.75, w: 5.7, h: 4.7, rectRadius: 0.08,
    fill: { color: "F4F6FB" }, line: { color: ICE, width: 1 },
  });
  s.addText([
    { text: "Objective  (minimize)\n\n", options: { bold: true, color: NAVY, fontSize: 14 } },
    { text: "H = \u03a3 \u2212w(i,j)\u00b7x(i,j)                pairing reward\n", options: { fontSize: 12, color: INK, breakLine: true } },
    { text: "  + \u03a3 \u22121.5\u00b7x(i,j)x(i+1,j\u22121)      stacking bonus\n", options: { fontSize: 12, color: INK, breakLine: true } },
    { text: "  + A\u00b7\u03a3 x_a x_b   (shared base)   penalty\n", options: { fontSize: 12, color: INK, breakLine: true } },
    { text: "  + B\u00b7\u03a3 x_a x_b   (crossing)     penalty\n\n", options: { fontSize: 12, color: INK, breakLine: true } },
    { text: "w(GC)=3, w(AU)=2, w(GU)=1;  A=B=6", options: { fontSize: 12, italic: true, color: GRAY } },
  ], { x: 0.9, y: 2.0, w: 5.1, h: 4.2, fontFace: "Courier New", valign: "top" });

  const bullets = [
    "Candidate pairs pruned by: canonical/wobble complementarity, min. loop \u2265 3 nt, optional max-span window",
    "Stacking-bonus term gives the QUBO genuine quadratic structure",
    "\u201cNo crossing\u201d constraint restricts to nested (pseudoknot-free) structures \u2014 matches ViennaRNA's default MFE search space",
    "Penalty weights A, B tuned against brute-force-verified small instances",
    "Directly convertible to an Ising Hamiltonian for QAOA / quantum annealing",
  ];
  const tb = [];
  bullets.forEach((b, i) => {
    tb.push({ text: b, options: { bullet: { code: "25AA" }, color: INK, fontSize: 13.5, breakLine: i < bullets.length - 1, paraSpaceAfter: 12 } });
  });
  s.addText(tb, { x: 6.7, y: 1.75, w: 6.0, h: 4.9, fontFace: FONT_BODY, valign: "top" });
}

// ============================================================
// Slide 4 — Solver architecture
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Three Solver Tiers", {
    x: 0.6, y: 0.4, w: 12, h: 0.7, fontFace: FONT_HEAD, fontSize: 28, bold: true, color: NAVY,
  });

  const cards = [
    { title: "Brute Force", sub: "exact validation", desc: "Exhaustive enumeration of the QUBO. Ground truth for the QUBO itself (not for physical MFE). Used up to 18 variables.", color: GRAY },
    { title: "Simulated Annealing", sub: "quantum-inspired", desc: "D-Wave's neal sampler. Our practical baseline: fast, scales to 1,000+ variables, matches brute-force optima exactly wherever tested.", color: MINT },
    { title: "QAOA", sub: "gate-based quantum", desc: "Qiskit statevector simulator, p=2\u20133 layers, COBYLA optimizer. Demonstrated up to ~9\u201310 qubits; correctness of mapping over raw performance.", color: NAVY },
  ];

  const cardW = 3.75, gap = 0.35, startX = 0.6, y0 = 1.5, cardH = 4.9;
  cards.forEach((c, i) => {
    const x = startX + i * (cardW + gap);
    s.addShape("roundRect", { x, y: y0, w: cardW, h: cardH, rectRadius: 0.1, fill: { color: "F7F8FC" }, line: { color: ICE, width: 1 } });
    s.addShape("roundRect", { x: x + 0.3, y: y0 + 0.35, w: 0.9, h: 0.9, rectRadius: 0.45, fill: { color: c.color } });
    s.addText(String(i + 1), { x: x + 0.3, y: y0 + 0.35, w: 0.9, h: 0.9, align: "center", valign: "middle", fontFace: FONT_HEAD, fontSize: 26, bold: true, color: WHITE });
    s.addText(c.title, { x: x + 0.3, y: y0 + 1.5, w: cardW - 0.6, h: 0.5, fontFace: FONT_HEAD, fontSize: 18, bold: true, color: NAVY });
    s.addText(c.sub.toUpperCase(), { x: x + 0.3, y: y0 + 1.95, w: cardW - 0.6, h: 0.35, fontFace: FONT_BODY, fontSize: 11, bold: true, color: c.color === WHITE ? NAVY : c.color, charSpacing: 1 });
    s.addText(c.desc, { x: x + 0.3, y: y0 + 2.45, w: cardW - 0.6, h: 2.3, fontFace: FONT_BODY, fontSize: 12.5, color: INK, valign: "top", lineSpacingMultiple: 1.2 });
  });
}

// ============================================================
// Slide 5 — Validation: exact match on 16-nt hairpin
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Validation: Exact Recovery of ViennaRNA's MFE", {
    x: 0.6, y: 0.4, w: 12, h: 0.7, fontFace: FONT_HEAD, fontSize: 26, bold: true, color: WHITE,
  });
  s.addText("16-nt hairpin  \u2014  GGGGAAAACCCCAAAA", {
    x: 0.6, y: 1.25, w: 10, h: 0.4, fontFace: "Courier New", fontSize: 15, color: ICE,
  });

  s.addShape("roundRect", { x: 0.6, y: 1.9, w: 12.1, h: 1.1, rectRadius: 0.08, fill: { color: "162055" }, line: { color: MINT, width: 1 } });
  s.addText([
    { text: "ViennaRNA MFE:   ", options: { color: ICE, fontSize: 15, bold: true } },
    { text: "((((....))))....   ", options: { color: WHITE, fontSize: 15, fontFace: "Courier New" } },
    { text: "\u22127.10 kcal/mol", options: { color: MINT, fontSize: 15, bold: true } },
  ], { x: 0.9, y: 2.0, w: 11.5, h: 0.4 });
  s.addText([
    { text: "QUBO (sim. annealing):   ", options: { color: ICE, fontSize: 15, bold: true } },
    { text: "((((....))))....   ", options: { color: WHITE, fontSize: 15, fontFace: "Courier New" } },
    { text: "\u22127.10 kcal/mol", options: { color: MINT, fontSize: 15, bold: true } },
  ], { x: 0.9, y: 2.5, w: 11.5, h: 0.4 });

  const stats = [
    ["0.00", "kcal/mol energy gap"],
    ["1.00", "F1 score vs. MFE"],
    ["0.14s", "solve time"],
  ];
  let x = 0.6;
  const w = 3.9;
  stats.forEach(([num, label]) => {
    s.addText(num, { x, y: 3.5, w, h: 1.1, align: "center", fontFace: FONT_HEAD, fontSize: 44, bold: true, color: MINT });
    s.addText(label.toUpperCase(), { x, y: 4.55, w, h: 0.4, align: "center", fontFace: FONT_BODY, fontSize: 12, color: ICE, charSpacing: 1 });
    x += w + 0.15;
  });

  s.addText("Bit-for-bit structural match, confirming the QUBO formulation and solver pipeline are correct \u2014 not just close.", {
    x: 0.6, y: 5.9, w: 12, h: 0.8, fontFace: FONT_BODY, fontSize: 14, italic: true, color: ICE, align: "center",
  });
}

// ============================================================
// Slide 6 — Benchmark results across sequences
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Benchmark Results Across Curated Sequences", {
    x: 0.6, y: 0.35, w: 12, h: 0.6, fontFace: FONT_HEAD, fontSize: 26, bold: true, color: NAVY,
  });

  s.addImage({ path: "figures/fig5_benchmark_energy_gap.png", x: 0.5, y: 1.05, w: 6.15, h: 3.5 });
  s.addImage({ path: "figures/fig6_benchmark_runtime.png", x: 6.75, y: 1.05, w: 6.15, h: 3.5 });

  const bullets = [
    "16-nt hairpin: exact match (0.0 kcal/mol gap). 22-nt & 44-nt: F1 = 0.90\u20130.92, gap grows with multiloop complexity.",
    "QAOA (simulator) on the 9-nt case: ~1,600\u00d7 slower than simulated annealing, and converged to a lower-quality structure.",
  ];
  const tb = [];
  bullets.forEach((b, i) => tb.push({ text: b, options: { bullet: { code: "25AA" }, color: INK, fontSize: 13, breakLine: i === 0, paraSpaceAfter: 8 } }));
  s.addText(tb, { x: 0.6, y: 4.75, w: 12.1, h: 1.4, fontFace: FONT_BODY, valign: "top" });
}

// ============================================================
// Slide 7 — Scaling: qubit count
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Scaling: Qubit / Variable Count vs. Sequence Length", {
    x: 0.6, y: 0.35, w: 12, h: 0.6, fontFace: FONT_HEAD, fontSize: 25, bold: true, color: NAVY,
  });
  s.addImage({ path: "figures/fig1_qubit_scaling.png", x: 0.5, y: 1.0, w: 6.1, h: 4.07 });
  s.addImage({ path: "figures/fig2_quadratic_terms_scaling.png", x: 6.75, y: 1.0, w: 6.1, h: 4.07 });

  s.addText([
    { text: "Unbounded candidate pairs grow ~quadratically (150 nt \u2192 4,140 qubits); a banded max-span window cuts this to ~1,356. ", options: { fontSize: 13, color: INK, breakLine: true } },
    { text: "But quadratic (two-qubit) terms \u2014 driven mainly by the no-crossing constraint \u2014 grow far faster (150 nt \u2192 166,870 terms, avg. degree ~246). This QUBO density, not raw qubit count, is the real scaling bottleneck for both QAOA circuit depth and D-Wave embedding.", options: { fontSize: 13, color: INK } },
  ], { x: 0.6, y: 5.2, w: 12.1, h: 1.9, fontFace: FONT_BODY, valign: "top", lineSpacingMultiple: 1.2 });
}

// ============================================================
// Slide 8 — Resource estimate table
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Estimated Quantum Resource Requirements", {
    x: 0.6, y: 0.4, w: 12, h: 0.6, fontFace: FONT_HEAD, fontSize: 26, bold: true, color: NAVY,
  });

  const header = ["Length (nt)", "Qubits (banded)", "2-qubit terms", "Est. QAOA depth (p=3)", "SA runtime"];
  const data = [
    ["20", "54", "896", "56", "0.18 s"],
    ["50", "330", "25,278", "236", "2.18 s"],
    ["80", "685", "78,032", "348", "7.21 s"],
    ["120", "988", "111,728", "345", "12.05 s"],
    ["150", "1,356", "166,870", "375", "17.72 s"],
  ];

  const rows = [header.map(h => ({ text: h, options: { bold: true, color: WHITE, fill: { color: NAVY }, fontSize: 13 } }))];
  data.forEach((r, i) => {
    rows.push(r.map(v => ({ text: v, options: { color: INK, fill: { color: i % 2 === 0 ? "F4F6FB" : WHITE }, fontSize: 13 } })));
  });

  s.addTable(rows, {
    x: 0.6, y: 1.3, w: 12.1, h: 3.0,
    colW: [2.2, 2.5, 2.5, 2.9, 2.0],
    border: { type: "solid", color: "E3E7F0", pt: 0.5 },
    align: "center", valign: "middle", fontFace: FONT_BODY,
  });

  s.addText([
    { text: "Practical ceiling: ", options: { bold: true, color: NAVY, fontSize: 14 } },
    { text: "exact recovery \u2264 ~20 nt; useful approximate recovery (F1 > 0.85) up to ~50 nt on the quantum-inspired backend; gate-based QAOA practically limited to \u2264 10\u201315 qubits even in simulation given current runtime and noise sensitivity (next slide).", options: { color: INK, fontSize: 14 } },
  ], { x: 0.6, y: 4.6, w: 12.1, h: 1.4, fontFace: FONT_BODY, valign: "top", lineSpacingMultiple: 1.2 });
}

// ============================================================
// Slide 9 — Noise robustness
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Robustness Under Sampling & Hardware Noise", {
    x: 0.6, y: 0.4, w: 12, h: 0.6, fontFace: FONT_HEAD, fontSize: 26, bold: true, color: NAVY,
  });

  // Left card: SA sampling budget
  s.addShape("roundRect", { x: 0.6, y: 1.25, w: 5.85, h: 5.2, rectRadius: 0.08, fill: { color: "F4F6FB" }, line: { color: ICE, width: 1 } });
  s.addText("Simulated Annealing \u2014 Sampling Budget", { x: 0.9, y: 1.5, w: 5.3, h: 0.5, fontFace: FONT_HEAD, fontSize: 16, bold: true, color: NAVY });

  const saRows = [
    ["Reads \u00d7 Sweeps", "Gap (kcal/mol)", "F1"],
    ["2000 \u00d7 2000", "6.2", "0.83"],
    ["200 \u00d7 500", "6.9", "0.76"],
    ["20 \u00d7 50", "7.9", "0.50"],
    ["5 \u00d7 20", "33.1", "0.23"],
  ];
  const saTbl = saRows.map((r, i) => r.map(v => ({
    text: v, options: { color: i === 0 ? WHITE : INK, bold: i === 0, fill: { color: i === 0 ? NAVY : (i % 2 === 0 ? WHITE : "EAEEF7") }, fontSize: 12.5 },
  })));
  s.addTable(saTbl, { x: 0.9, y: 2.1, w: 5.3, h: 1.9, align: "center", valign: "middle", fontFace: FONT_BODY, border: { type: "solid", color: "E3E7F0", pt: 0.5 } });
  s.addText("Quality holds until an aggressively reduced budget, then collapses sharply below ~20 reads \u00d7 50 sweeps.", {
    x: 0.9, y: 4.2, w: 5.3, h: 1.9, fontFace: FONT_BODY, fontSize: 12.5, italic: true, color: GRAY, valign: "top",
  });

  // Right card: QAOA noise
  s.addShape("roundRect", { x: 6.75, y: 1.25, w: 5.98, h: 5.2, rectRadius: 0.08, fill: { color: NAVY } });
  s.addText("QAOA \u2014 Depolarizing Gate Noise", { x: 7.05, y: 1.5, w: 5.4, h: 0.5, fontFace: FONT_HEAD, fontSize: 16, bold: true, color: WHITE });

  const qRows = [
    ["1-qubit error", "Top-bitstring prob.", "Distinct outcomes"],
    ["0.00 (noiseless)", "6.6%", "388 / 512"],
    ["0.01", "0.5%", "512 / 512"],
    ["0.05", "0.4%", "512 / 512"],
    ["0.10", "0.4%", "512 / 512"],
  ];
  const qTbl = qRows.map((r, i) => r.map(v => ({
    text: v, options: { color: i === 0 ? NAVY : WHITE, bold: i === 0, fill: { color: i === 0 ? MINT : "162055" }, fontSize: 12.5 },
  })));
  s.addTable(qTbl, { x: 7.05, y: 2.1, w: 5.4, h: 1.9, align: "center", valign: "middle", fontFace: FONT_BODY, border: { type: "solid", color: "2A3570", pt: 0.5 } });
  s.addText("Even 1% gate error collapses top-outcome probability >10\u00d7 and saturates all 512 possible bitstrings \u2014 amplitude concentration is destroyed almost immediately.", {
    x: 7.05, y: 4.2, w: 5.4, h: 1.9, fontFace: FONT_BODY, fontSize: 12.5, italic: true, color: ICE, valign: "top",
  });
}

// ============================================================
// Slide 10 — Limitations
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: WHITE };
  s.addText("Limitations, Stated Plainly", {
    x: 0.6, y: 0.4, w: 12, h: 0.7, fontFace: FONT_HEAD, fontSize: 28, bold: true, color: NAVY,
  });

  const items = [
    ["No loop-initiation entropy", "The QUBO's pairwise+stacking energy model omits hairpin/bulge/multiloop entropic penalties \u2014 the dominant source of the observed energy gap (e.g. it over-favors a 9-nt hairpin ViennaRNA's Turner model rejects outright)."],
    ["Pseudoknots excluded", "The no-crossing constraint restricts to nested structures, matching ViennaRNA's default MFE algorithm \u2014 a fair but limited comparison scope."],
    ["QUBO density, not qubit count, is the bottleneck", "The no-crossing constraint densely connects candidate-pair variables (avg. degree ~246 at 150 nt), inflating QAOA circuit depth and D-Wave embedding overhead far faster than variable count alone suggests."],
    ["QAOA is not yet competitive here", "Slower than simulated annealing by ~1,600\u00d7 at 9 qubits, lower solution quality, and its output distribution collapses toward uniform noise under even 1% gate error."],
  ];

  let y = 1.4;
  items.forEach(([title, body]) => {
    s.addShape("roundRect", { x: 0.6, y, w: 0.35, h: 0.35, rectRadius: 0.06, fill: { color: MINT } });
    s.addText(title, { x: 1.15, y: y - 0.05, w: 11.5, h: 0.4, fontFace: FONT_BODY, fontSize: 15, bold: true, color: NAVY });
    s.addText(body, { x: 1.15, y: y + 0.4, w: 11.5, h: 0.75, fontFace: FONT_BODY, fontSize: 12.5, color: INK, valign: "top", lineSpacingMultiple: 1.15 });
    y += 1.3;
  });
}

// ============================================================
// Slide 11 — Future directions + close
// ============================================================
{
  const s = pres.addSlide();
  s.background = { color: NAVY };
  s.addText("Future Directions", {
    x: 0.6, y: 0.5, w: 12, h: 0.7, fontFace: FONT_HEAD, fontSize: 30, bold: true, color: WHITE,
  });

  const cols = [
    ["Close the energy gap", "Add loop-length-dependent penalty terms via auxiliary variables / quadratization."],
    ["Sparsify the QUBO", "Bound the crossing constraint to a local window instead of all-pairs \u2014 directly targets the scaling bottleneck."],
    ["Try tensor networks", "The near-planar structure from the no-crossing constraint is a natural fit for MPS contraction at full mRNA-UTR scale."],
    ["Pseudoknot-aware model", "Drop the no-crossing term and benchmark against a pseudoknot-aware classical tool instead of ViennaRNA's default MFE."],
  ];
  let x = 0.6;
  const w = 2.95, gap = 0.15;
  cols.forEach(([t, b]) => {
    s.addShape("roundRect", { x, y: 1.55, w, h: 3.6, rectRadius: 0.08, fill: { color: "162055" }, line: { color: MINT, width: 0.75 } });
    s.addText(t, { x: x + 0.22, y: 1.8, w: w - 0.44, h: 0.9, fontFace: FONT_HEAD, fontSize: 15, bold: true, color: MINT, valign: "top" });
    s.addText(b, { x: x + 0.22, y: 2.65, w: w - 0.44, h: 2.3, fontFace: FONT_BODY, fontSize: 12, color: ICE, valign: "top", lineSpacingMultiple: 1.2 });
    x += w + gap;
  });

  s.addText("Code, data, and figures: github-style repo in the submission package \u2014 fully reproducible via `python3 src/run_all.py`", {
    x: 0.6, y: 5.55, w: 12, h: 0.5, fontFace: FONT_BODY, fontSize: 13, italic: true, color: ICE,
  });
  s.addText("Thank you", {
    x: 0.6, y: 6.2, w: 8, h: 0.8, fontFace: FONT_HEAD, fontSize: 26, bold: true, color: WHITE,
  });
}

pres.writeFile({ fileName: "RNA_Quantum_MFE_Presentation.pptx" }).then(() => {
  console.log("Saved RNA_Quantum_MFE_Presentation.pptx");
});
