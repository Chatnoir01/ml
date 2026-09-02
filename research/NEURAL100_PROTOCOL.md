# Neural residual screen — 100 frozen trainings

## Status

This experiment is an **exploratory neural-residual diagnostic**, not Phase 2 and not Gate-1 evidence. Global Gate 1 remains RED because fresh-population classical transfer has not yet been demonstrated. No neural fitness pressure is applied in this experiment.

## Question

Among S-boxes with exactly matched classical metrics, does the fixed reduced-round ToySPN expose a reproducible neural distinguishing signal, and does that signal differ between S-boxes strongly enough to justify a later adversarial co-evolution experiment?

## Frozen S-box panel

The source pool contains the 20 unique Phase-1H candidates already present in completed development/confirmation artifacts that satisfy exactly:

- nonlinearity `100`
- differential uniformity `8`
- maximum linear correlation `56`
- algebraic degree `7`
- SAC `0.5`

Before any neural result, select exactly the **ten lexicographically smallest SHA-256 fingerprints** from that source pool. Their full permutations are frozen in `neural100_candidates.py`. Every training job must recompute the classical metrics and fingerprint and abort on any mismatch.

## Exactly 100 trainings

Run 10 matched S-boxes × 10 paired replicates = **100 independent neural trainings**.

Replicates use the same dataset/model seed pair across all ten S-boxes, enabling paired comparison between candidates:

- dataset seeds: `31001, 31003, 31007, 31009, 31013, 31019, 31033, 31039, 31051, 31063`
- model seeds: `41011, 41017, 41023, 41039, 41047, 41051, 41057, 41077, 41081, 41083`

No seed may be replaced or retried because of its result.

## Frozen reduced-round environment

Use the existing educational 32-bit `ToySPN` only.

- rounds: `5`
- round keys, in order: `0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344, 0xA4093822, 0x299F31D0`
- input difference: `0x00000001`
- pair count per training: `8192`, exactly balanced
- dataset split: existing `70% / 15% / 15%`
- dataset generator: existing globally block-disjoint balanced-pair generator

The experiment makes no claim about a production cipher or full-round primitive.

## Frozen neural model

One deterministic NumPy MLP implementation is used for all 100 trainings:

- input: 96 binary features = 32 bits of left ciphertext + 32 bits of right ciphertext + 32 bits of XOR
- hidden layer: 64 ReLU units
- output: one logit
- optimizer: Adam
- epochs: `24`, fixed; no early stopping
- batch size: `256`
- learning rate: `0.002`
- L2 weight decay: `1e-4`
- initialization and minibatch order derive only from the frozen model seed

Validation AUC is recorded but does not choose epochs or hyperparameters. Test AUC is the scientific endpoint.

## Endpoint

For each run record:

- test AUC
- neural advantage `2 * abs(AUC - 0.5)`
- a same-score null AUC from a deterministic permutation of the held-out test labels (no additional training)
- test accuracy at threshold 0.5
- validation AUC
- exact data/model seeds and S-box fingerprint

## Frozen aggregate analysis

After all 100 runs, group by S-box fingerprint and compute candidate mean/median AUC and advantage, within-candidate standard deviation, null advantage, and the range of candidate mean advantages.

Use a paired permutation test for between-S-box heterogeneity: for each of 5000 deterministic permutations, independently permute the ten candidate labels **within each replicate**, preserving replicate difficulty. The statistic is the variance of candidate mean neural advantages. Report the exact Monte-Carlo p-value `(1 + exceedances) / 5001`.

Predeclared diagnostic labels:

1. `residual_signal_and_heterogeneity` if:
   - at least one candidate mean neural advantage is `>= 0.04`;
   - that candidate exceeds its mean null advantage by `>= 0.02`;
   - range of candidate mean advantages is `>= 0.02`; and
   - paired heterogeneity permutation `p < 0.01`.
2. `residual_signal_no_heterogeneity` if the first two conditions pass but the heterogeneity conditions do not.
3. `no_exploitable_residual_at_frozen_budget` otherwise.

These thresholds are diagnostic, not universal cryptographic security thresholds.

## Interpretation guard

A positive result only shows residual distinguishability/heterogeneity in this frozen reduced-round ToySPN, within the Phase-1H matched S-box family. It does **not** unblock the neural oracle, prove security, or establish generalization to other architectures/round counts. A later adversarial experiment would require fresh-population classical success first, then separate oracle/challenger architectures and untouched datasets.
