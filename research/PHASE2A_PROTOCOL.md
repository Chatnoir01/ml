# Phase 2A — Fresh-Panel Neural Oracle Qualification

Status: preregistered before implementation and before any Phase-2A neural training.

Public preregistration: issue #58.
Base commit: `58433814ef04ffde0fd3f3237034a8b660dd241b` (Phase 1O blind confirmation merged; Classical Gate 1 GREEN).

## Purpose

Phase 2A asks whether a frozen neural scoring procedure can rank **fresh Phase-1O-confirmation-derived, classically matched S-boxes** in a way that replicates under an independent challenger architecture/regime family.

Phase 2A is qualification only. No neural score may influence GA selection, Pareto ranking, mutation, acceptance, proposal generation, or any evolutionary feedback.

## Fresh classical panel

Reconstruct deterministically from the nine frozen Phase-1O confirmation seeds:

`2609, 2617, 2621, 2633, 2647, 2657, 2663, 2671, 2683`.

Use only Arm-A terminal JOINT candidates. Eligible candidates must recompute exactly:

- differential uniformity: `8`
- nonlinearity: `100`
- maximum absolute linear correlation: `56`
- algebraic degree: `7`
- bijective 8x8 S-box
- SAC within the existing classical hard constraint

Selection is classical-only and occurs before neural training:

1. At most one eligible candidate per source confirmation seed.
2. If one seed has multiple eligible candidates, keep the lexicographically smallest SHA-256 S-box fingerprint.
3. Across those per-seed representatives, choose the lexicographically smallest six fingerprints.
4. If fewer than six eligible candidates can be reconstructed, verdict is blocked and no neural training is authorized.

The selected full permutations, source seeds, fingerprints, and recomputed classical metrics must be committed before the first Phase-2A neural result.

## Frozen ToySPN scope

Educational 32-bit ToySPN only. This experiment is not an attack on a deployed cipher and performs no operational key recovery.

Use the same frozen round-key schedule, balanced-pair generator, disjoint train/validation/test split, training implementation and architecture hyperparameters already frozen by the neural heterogeneity experiment.

### Oracle side

- architecture: `bit_relu_mlp`
- rounds: `4`
- input differences: `0x00000001`, `0x00000100`

### Independent challenger side

- architecture: `byte_tanh_mlp`
- rounds: `5`
- input differences: `0x00010000`, `0x01000000`

## Fresh paired replicates

Dataset seeds:

`51001, 51007, 51011, 51031, 51047`

Model seeds:

`61001, 61007, 61027, 61031, 61043`

Seed pairs are reused across all six candidates within each experimental cell to preserve paired comparisons. No seed is replaced or retried because of its scientific result.

Total planned trainings:

- oracle: 6 candidates x 2 differences x 5 paired replicates = 60
- challenger: 6 candidates x 2 differences x 5 paired replicates = 60
- total = **120 neural trainings**

## Endpoints

For every training record:

- test AUC
- neural advantage = `2 * abs(test_AUC - 0.5)`
- deterministic held-out-label-permutation null AUC / null advantage
- validation AUC
- test accuracy
- S-box fingerprint
- source confirmation seed
- side (`oracle` or `challenger`)
- architecture
- round count
- input difference
- dataset seed
- model seed

For each candidate:

- oracle score = mean neural advantage across its 10 oracle trainings
- challenger score = mean neural advantage across its 10 challenger trainings

## Frozen aggregate tests

For each side independently, perform a blocked S-box heterogeneity permutation test preserving `(difference, paired replicate)` blocks and shuffling only S-box identity within a block. Use 10,000 deterministic permutations and report `(1 + exceedances) / 10001`.

Compute Spearman rank correlation between the six candidate oracle scores and six challenger scores.

## Qualification criteria

All must pass for `phase2a_oracle_qualified`:

1. Exactly 120 trainings with complete provenance.
2. All six panel candidates revalidate the frozen classical eligibility tuple before training.
3. Oracle-side blocked S-box heterogeneity p < 0.05.
4. Challenger-side blocked S-box heterogeneity p < 0.05.
5. Oracle score range >= 0.015.
6. Challenger score range >= 0.015.
7. Spearman correlation oracle vs challenger candidate scores >= 0.60.
8. At least one oracle candidate mean advantage >= 0.04 and exceeds its mean null advantage by >= 0.02.
9. At least one challenger candidate mean advantage >= 0.04 and exceeds its mean null advantage by >= 0.02.
10. Panel-construction and aggregate receipts are deterministic.

Any failure yields `phase2a_oracle_not_qualified`. The result must be preserved and no neural evolutionary pressure may be introduced or tuned in place on these candidates/seeds/regimes.

A PASS permits only a separately preregistered Phase 2B matched-budget GA-only versus GA+NN experiment.

## Interpretation boundary

A PASS would show that this frozen ToySPN neural scoring setup produces a fresh-panel S-box-specific ordering that replicates under the preregistered challenger. It would not prove neural resistance, production security, AES superiority, physical side-channel resistance, or closed-loop co-evolution success.
