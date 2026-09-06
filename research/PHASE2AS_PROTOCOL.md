# Phase 2A-S — round-depth neural signal attenuation

Status: preregistered before implementation and before scientific execution.

## Motivation

Phase 2A-R ended with `phase2ar_inconclusive_signal`. With the frozen six-S-box panel, 4-round regimes A/B passed the preregistered heterogeneity prerequisite, while 5-round regimes C/D did not. Adjacent rank correlations remained nominally above the frozen stability threshold, so Phase 2A-R did not localize the original Phase-2A rank disagreement.

This new phase tests one narrower hypothesis: under a fixed neural architecture/representation and fixed input-difference family, does increasing ToySPN depth from 3 to 4 to 5 rounds attenuate S-box-specific neural separation?

This is diagnostic/educational only. It cannot qualify a Neural Oracle and cannot authorize GA↔NN feedback.

## Frozen panel

Reuse exactly the six committed candidates in `src/adversarial_sbox/phase2a_candidates.py` and require panel digest:

`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`

Every candidate must revalidate before training as bijective with DU=8, NL=100, max |LAT|=56, algebraic degree=7 and the existing SAC hard bound.

No candidate replacement or new selection is allowed.

## Frozen model and differences

Hold constant across all depth cells:
- architecture/representation: `byte_tanh_mlp`
- input differences: `0x00000001`, `0x00000100`
- all existing Phase-2A training hyperparameters and deterministic null-label diagnostic

Only ToySPN round depth changes:
- R3: 3 rounds
- R4: 4 rounds
- R5: 5 rounds

## Fresh paired neural seeds

Dataset seeds:
- 72007
- 72019
- 72031
- 72043
- 72053

Model seeds:
- 82007
- 82021
- 82037
- 82051
- 82067

The five pairs are reused across every candidate, difference and depth. No scientific seed may be replaced/retried because of its result.

Permutation-test seeds:
- R3: 92003
- R4: 92009
- R5: 92033

Permutation repetitions: exactly 10,000 per depth.

## Exact budget

Per depth: 6 candidates × 2 differences × 5 paired replicates = 60 trainings.

Total: exactly **180 neural trainings**.

No neural score may enter evolution.

## Frozen endpoints

For each depth and candidate:
- candidate score = mean neural advantage over its 10 trainings;
- preserve mean null advantage and deterministic receipts.

For each depth independently compute:
- blocked S-box heterogeneity permutation p-value (10,000 deterministic permutations);
- candidate score range;
- maximum candidate mean neural advantage;
- regime mean null advantage.

Also compute adjacent candidate-rank Spearman correlations R3→R4 and R4→R5 as descriptive stability endpoints. The existing rho>=0.60 threshold is retained for reporting, but the primary Phase-2A-S hypothesis concerns signal attenuation, not rank-break localization.

## Signal-qualified depth

A depth is signal-qualified only if all hold:
1. exact training/provenance count;
2. panel revalidation;
3. heterogeneity p < 0.05;
4. candidate score range >= 0.015;
5. at least one candidate mean advantage >= 0.04 and exceeds the depth's mean null advantage by >= 0.02;
6. deterministic receipts.

## Frozen primary attenuation gate

Classify `phase2as_depth_attenuation_supported` only if ALL hold:
1. R3 and R4 are signal-qualified;
2. R5 fails signal qualification specifically because heterogeneity p>=0.05 and/or score range<0.015;
3. observed candidate score ranges are strictly ordered `range_R3 > range_R4 > range_R5` OR `range_R4 > range_R3 > range_R5`, so R5 is strictly the weakest range;
4. median absolute candidate advantage at R5 is lower than at R4;
5. exact 180 trainings and deterministic aggregate rerun;
6. no neural evolutionary pressure.

If R3/R4 do not both qualify: `phase2as_inconclusive_early_signal`.

If R5 also qualifies: `phase2as_no_depth_attenuation`.

If R5 fails but the frozen attenuation conditions 3–4 do not both hold: `phase2as_inconclusive_mixed_depth_effect`.

No threshold or seed may be changed after results.

## Interpretation boundary

This phase studies a ToySPN neural distinguisher only. It performs no operational key recovery and makes no claim about AES, deployed ciphers, physical side-channel resistance, production security, or neural resistance. Regardless of outcome, Phase 2B GA↔NN remains blocked. A future oracle qualification attempt requires a separately preregistered confirmation.