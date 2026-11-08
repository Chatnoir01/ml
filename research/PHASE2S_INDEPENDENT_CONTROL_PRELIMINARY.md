# Phase 2S — Preliminary cross-language one-bit control

**Preliminary exploratory note only. NOT an official CI outcome, not a registered confirmation, not a new cipher weakness.** This note describes a V8 JavaScript calculation run interactively against the actual frozen six-candidate Python panel. A standalone Node.js reproduction script is now checked into `scripts/phase2s_independent_probe.cjs`; its exact-head GitHub Actions execution must be checked separately.

## Method

- Six original frozen, fingerprint-verified ToySPN S-Boxes (DU=8, NL=100, max |LAT|=56, algebraic degree=7), two chosen plaintext differences (1,256).
- Original 11-bit rotation and three fixed diagnostic public key schedules: historical, XOR-perturbed, rotated-perturbed.
- 3,4,5 rounds. **108** (6×2×3×3) toy cells.
- Independent xorshift32 generator with seed `0x52010471 XOR input_difference`, used only for experimental sampling; **not cryptographically secure**.
- Positive pairs have the registered plaintext XOR difference; negative pairs do not, and all plaintext blocks are unique across training and evaluation.
- Per cell: 1,536 positive/negative pairs per class in training; 3,072 positive/negative pairs per class in held-out evaluation.
- Choose the single output XOR bit with the biggest absolute class-frequency gap **on training only**; freeze its sign, compute the signed test gap. Output is a one-bit differential advantage proxy: for a binary feature, signed `2*(AUC-0.5)`.
- Train/test samples and scoring code differ from the Python source baseline, which uses `random.Random` with distinct seeds and 2,048/4,096 per-class splits. Numeric agreement should be evaluated qualitatively, not presumed exact.

## Exploratory average signed holdout scores

These means pool the two input differences and six frozen candidates for a given schedule/depth.

| Public key schedule | 3 rounds | 4 rounds | 5 rounds |
|---|---:|---:|---:|
| Historical | 0.495769 | 0.164985 | 0.028538 |
| XOR perturbed | 0.497613 | 0.167236 | 0.039904 |
| Rotated perturbed | 0.503499 | 0.163276 | 0.037327 |

No uncertainty intervals or confirmatory p-values were calculated for these post-hoc summaries.

At four rounds on historical keys, the descriptive six-candidate Pearson correlation with frozen neural scores is approximately `0.682` for input difference 1 and `0.788` for input difference 256. Other key schedules give different correlations (approximately 0.467 to 0.832 across these six-candidate comparisons). **With only six candidates, such correlations are fragile and cannot establish causality, generalization or statistical significance.**

## Bit-position observation (hypothesis-generating)

Winning XOR bit positions grouped nonrandomly in this exploratory sample:

- Input difference 1, historical schedule: positions 10–15 at 3 rounds; 17–22 at 4 rounds; broadly scattered by 5 rounds.
- Input difference 256, historical schedule: positions 18–23 at 3 rounds; 25–31 at 4 rounds; broadly scattered at 5 rounds.
- The ToySPN rotates by 11 bits between substitutions, so alignment/movement of active-bit structure is an obvious **candidate mechanism**, not a proven cause of the observed peak.

## What this changes

The primary neural phenomenon was **between-S-Box separation at four rounds**, whereas overall neural advantage decreased with depth. A simple non-neural one-bit distinguisher also has meaningful signal on this toy cipher at 3/4 rounds, and that signal decreases by 5 rounds in the exploratory calculation.

Therefore we must test whether the original neural distinguisher offers an improvement **over competitive classical features and baselines**, and whether any structure persists across new candidate panels, unseen keys, distinct diffusion maps and independent model architectures. The current result does not prove that neural learning adds no information, or that the four-round heterogeneity is caused by any one-bit feature.

**Next gates:** completed exact-head Python/Node CI and archived JSON outputs, fresh controlled rotation experiment, prospective panel/keys and multi-parameter classical baselines. No changes to previously frozen Phase 2A or 2G science.
