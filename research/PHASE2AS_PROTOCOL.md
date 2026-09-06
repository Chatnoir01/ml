# Phase 2A-S — Depth-only S-box signal attenuation

Status: **PREREGISTERED / NO NEURAL EXECUTION AUTHORIZED**

Public preregistration: issue #68.
Base `main`: `13f8ae0d019d126a15c52896b8bfc49fe6addd0e`.

## Question

Holding the exact Phase-2A six-candidate panel, neural architecture, input differences, data-generation/split pipeline, hyperparameters and paired randomness fixed, does increasing ToySPN depth from 4 to 5 rounds reduce S-box-specific neural separation?

The 3-round condition is frozen context. The primary confirmatory contrast is 4→5 rounds.

## Frozen panel

Use only `src/adversarial_sbox/phase2a_candidates.py` with panel digest:

`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`

All six candidates must revalidate as bijective 8×8 S-boxes with DU=8, NL=100, max|LAT|=56, algebraic degree=7 and SAC within the existing hard bound.

## Frozen neural design

- architecture: `byte_tanh_mlp`
- depths: `(3, 4, 5)` ToySPN rounds
- input differences: `(0x00000001, 0x00000100)`
- round keys: existing `ROUND_KEYS[:rounds+1]`
- pair count, balanced generator, train/validation/test split and model hyperparameters: unchanged from Phase 2A-R
- endpoint: existing `neural_advantage = 2*abs(test_AUC-0.5)` plus deterministic null-label advantage

Only ToySPN round count changes across depth conditions.

## Fresh paired seeds

Dataset seeds (10):

`(72001, 72011, 72019, 72031, 72043, 72053, 72071, 72083, 72091, 72101)`

Model seeds (10):

`(82003, 82013, 82021, 82037, 82051, 82067, 82073, 82087, 82099, 82109)`

The ordered pairs are reused across every candidate, difference and depth. No retry/replacement is permitted based on outcomes.

## Exact budget

Per depth: `6 candidates × 2 differences × 10 replicates = 120` trainings.

Total: **360 neural trainings exactly**.

Neural evolutionary pressure is forbidden.

## Frozen statistics

For each depth and candidate, candidate score is the mean neural advantage over its 20 trainings.

For each depth report:
- blocked S-box heterogeneity with 10,000 deterministic permutations;
- candidate-score variance and range;
- existing signal condition;
- candidate scores and null scores.

### Primary 4→5 attenuation contrast

For every matched `(input_difference, replicate)` block, compute the population variance across the six candidate neural advantages.

Let `d_i = variance4_i - variance5_i` for the 20 matched blocks.

Use a one-sided paired sign-flip permutation test of the mean `d_i`, with 10,000 deterministic permutations and seed `92011`.

Effect-size ratio:

`mean_block_variance_5 / mean_block_variance_4`.

The same paired 3→4 statistics are reported as preregistered secondary context, using seed `92003`, but they do not gate the primary verdict.

Per-depth blocked-heterogeneity permutation seeds are frozen as:
- depth 3: `93003`
- depth 4: `93004`
- depth 5: `93005`

## Frozen verdict logic

Common prerequisites:
1. exactly 360 trainings and exact seed/provenance matrix;
2. exact panel digest and classical revalidation;
3. deterministic cell and aggregate receipts;
4. `neural_evolutionary_pressure == False` everywhere;
5. depth 4 passes existing signal prerequisites: blocked heterogeneity `p < 0.05`, candidate-score range `>= 0.015`, and at least one candidate mean advantage `>= 0.04` exceeding its candidate mean null advantage by `>= 0.02`.

If any common prerequisite fails:

`phase2as_inconclusive_prerequisite`

If prerequisites pass and both:
- primary paired 4→5 variance-reduction permutation `p < 0.05`;
- `mean_var_5 / mean_var_4 <= 0.60`;

then:

`phase2as_depth5_attenuation_confirmed`

If prerequisites pass and either:
- primary paired permutation `p >= 0.05`, or
- `mean_var_5 / mean_var_4 > 0.75`;

then:

`phase2as_depth5_attenuation_not_confirmed`

Otherwise:

`phase2as_depth5_attenuation_inconclusive`

No result-dependent retuning is allowed in Phase 2A-S.

## Interpretation boundary

This is an educational/defensive ToySPN experiment. A confirmed result is limited to this frozen toy setup and endpoint. It is not evidence of AES/deployed-cipher weakness, physical side-channel resistance, production security, neural resistance or successful GA↔NN co-evolution.

Phase 2B remains blocked regardless of Phase 2A-S outcome. Any later oracle qualification requires a separately preregistered confirmation.
