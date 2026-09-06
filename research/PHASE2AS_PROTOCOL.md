# Phase 2A-S — Neural S-Box Signal Attenuation Across Round Depth

## Status

**PREREGISTERED — NO SCIENTIFIC TRAINING AUTHORIZED YET**

Public preregistration: issue #65. Execution lock: issue #67.

An earlier unexecuted branch draft used 5 paired seeds / 180 trainings. No Phase 2A-S workflow marker or scientific run existed under that draft. Issue #65 supersedes it before scientific execution. This protocol is the authoritative frozen design.

Phase 2A-R ended `phase2ar_inconclusive_signal`: the frozen six-S-box panel carried strong S-box-specific neural heterogeneity at 4 rounds but much weaker heterogeneity at 5 rounds. Phase 2A-S tests that uncertainty directly. It is diagnostic/confirmatory only and cannot authorize GA↔NN feedback.

## Scientific question

Holding architecture, representation, input-difference family, frozen S-box panel, data generation, training procedure and paired seeds fixed, does S-box-specific neural separation decrease as ToySPN depth increases from 3 to 4 to 5 rounds?

## Frozen panel

Reuse exactly the six committed candidates in `src/adversarial_sbox/phase2a_candidates.py`.

Panel digest:
`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`

Every candidate must revalidate before training:
- bijective 8x8 S-box;
- DU = 8;
- NL = 100;
- max |LAT| = 56;
- algebraic degree = 7;
- SAC within the existing hard bound.

No new candidate selection is allowed.

## Frozen neural regime

Use the existing deterministic `byte_tanh_mlp` ToySPN training implementation from Phase 2A/2A-R.

Only round depth changes:
- R3: 3 rounds;
- R4: 4 rounds;
- R5: 5 rounds.

Input differences at every depth:
- `0x00000001`
- `0x00000100`

No architecture, representation, optimizer, pair-count, epoch-count, null-label procedure or score definition may change between depths.

## Fresh paired neural seeds

Dataset seeds:
`(72001, 72019, 72031, 72043, 72053, 72071, 72089, 72101)`

Model seeds:
`(82003, 82013, 82021, 82037, 82051, 82067, 82073, 82087)`

Eight seed pairs are reused across all six candidates, both differences and depths 3/4/5. No seed may be retried or replaced because of its result.

Deterministic heterogeneity permutation seeds:
- R3: `92003`
- R4: `92009`
- R5: `92021`

## Exact training budget

Per depth:
- 6 candidates × 2 differences × 8 paired replicates = 96 trainings.

Total:
- 3 depths × 96 = **288 neural trainings exactly**.

No neural score may enter evolution.

## Frozen endpoints

Per training preserve the existing neural advantage and deterministic null-label diagnostic.

Per depth and candidate:
- candidate score = mean neural advantage across its 16 trainings.

For each depth compute:
- blocked S-box heterogeneity permutation p-value with exactly 10,000 deterministic permutations;
- between-candidate heterogeneity variance `H_r`;
- candidate score range `R_r`;
- existing Phase-2A signal condition;
- candidate rank order.

Across depths compute Spearman `rho_34` and `rho_45` descriptively.

## Frozen prerequisites

Before interpreting attenuation require all:
1. exact 288 training/provenance count;
2. frozen panel digest and classical revalidation pass;
3. deterministic receipts;
4. signal condition passes at all three depths;
5. no neural evolutionary pressure.

If any fails: `phase2as_inconclusive_prerequisites`.

## Primary attenuation criterion

Require all:
- `H3 > H4 > H5`;
- `H5 / H4 <= 0.50`;
- `R3 >= R4 > R5`;
- `R5 / R4 <= 0.75`.

Heterogeneity p-values are always reported but are not the sole attenuation criterion because the larger replication budget can make a smaller 5-round effect statistically significant. Effect magnitude is primary.

Classification:
- prerequisites fail → `phase2as_inconclusive_prerequisites`;
- all attenuation criteria pass → `phase2as_depth_attenuation_supported`;
- both monotonic orderings hold but one or both ratio thresholds fail → `phase2as_weak_attenuation`;
- otherwise → `phase2as_depth_attenuation_not_supported`.

No threshold, seed, candidate, depth or endpoint may change after scientific execution.

## Reproducibility / execution lock

Before scientific execution:
1. this protocol and seed registry committed;
2. RED runner contract recorded before runner implementation;
3. runner/aggregate implementation and synthetic tests GREEN;
4. exact 288-training workflow committed but dormant;
5. Python 3.10/3.11/3.12 CI GREEN;
6. historical Phase-1 benchmark GREEN;
7. PR diff inspected;
8. only then create `research/PHASE2AS_EXECUTE.md` containing `AUTHORIZED_PHASE2AS_DEPTH_ATTENUATION`.

The marker commit SHA is the frozen scientific SHA. No scientific parameter may change after observing results.

## Interpretation boundary

This experiment is educational/defensive and uses ToySPN only. It performs no operational key recovery and makes no claim of AES/deployed-cipher weakness, physical side-channel resistance, production security, neural resistance or successful GA↔NN co-evolution.

Even a positive result establishes only a controlled depth-dependent neural-separation effect on this frozen toy system. **Phase 2B GA↔NN remains blocked** pending a separately preregistered oracle qualification and fresh confirmation.