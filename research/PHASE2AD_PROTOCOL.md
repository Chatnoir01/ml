# Phase 2A-D — Neural Signal Attenuation with Depth

Status: preregistered before implementation results or Phase-2A-D neural execution.

Public preregistration: issue #62.
Base commit: `13f8ae0d019d126a15c52896b8bfc49fe6addd0e` (Phase 2A-R merged).

## Purpose

Phase 2A-R ended with `phase2ar_inconclusive_signal`. Fresh-seed adjacent rank correlations stayed above the frozen stability threshold, but S-box-specific heterogeneity weakened sharply after moving from 4 to 5 ToySPN rounds.

Phase 2A-D is a new experiment that tests depth attenuation directly. Phase 2A-R is not retuned. This phase cannot qualify a Neural Oracle and cannot authorize neural evolutionary pressure or Phase 2B.

## Frozen panel

Reuse exactly `src/adversarial_sbox/phase2a_candidates.py` with panel digest:

`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`

All six candidates must revalidate before training:
- differential uniformity = 8
- nonlinearity = 100
- max |LAT| = 56
- algebraic degree = 7
- bijective
- SAC within the existing hard bound.

No candidate selection, replacement, filtering, or result-based retry is allowed.

## Frozen neural design

Architecture/representation: `byte_tanh_mlp` only.

Depths:
- R3: 3 rounds
- R4: 4 rounds
- R5: 5 rounds

Input differences for every depth:
- `0x00000001`
- `0x00000100`

Depth is the only experimental factor that changes across R3/R4/R5.

## Fresh paired neural seeds

These values were searched on current `main` before issue #62 and had no repository matches.

Dataset seeds:
`73009, 73013, 73019, 73037, 73039, 73043, 73061, 73063, 73079, 73091`

Model seeds:
`83003, 83009, 83023, 83047, 83059, 83063, 83071, 83077, 83089, 83101`

Pair by index. Reuse the same paired seeds across all candidates, differences, and depths. No result-based retry or replacement.

## Exact training budget

Each depth: 6 candidates × 2 differences × 10 paired replicates = 120 trainings.

Total: **360 neural trainings exactly**.

No neural score enters GA selection, mutation, ranking, acceptance, proposal generation, or any evolutionary feedback.

## Frozen per-depth endpoints

For each candidate at each depth:
- score = mean neural advantage over its 20 trainings;
- null score = mean deterministic held-out-label null advantage over the same 20 trainings.

For each depth independently:
- blocked S-box heterogeneity permutation test preserving `(difference, paired replicate)` blocks;
- 10,000 deterministic permutations;
- fixed heterogeneity permutation seeds: R3=`92103`, R4=`92104`, R5=`92105`;
- candidate score range;
- between-candidate dispersion `V_r = population variance(candidate mean advantages)`.

The heterogeneity seeds were searched on current `main` before implementation and had no repository matches. The same pre-implementation amendment is recorded publicly in issue #62.

## Primary confirmatory attenuation test: 4→5 rounds

Primary statistic:

`Delta45 = V4 - V5`.

Null randomization:
- preserve each matched `(candidate, difference, replicate)` pair;
- independently swap the R4/R5 neural-advantage observations with probability 0.5;
- recompute `Delta45`;
- repeat 10,000 times with fixed seed `92045`.

One-sided p-value tests whether observed `Delta45 > 0` is larger than expected under R4/R5 exchangeability.

Frozen minimum meaningful attenuation:

`V5 / V4 <= 0.75`

which requires at least a 25% reduction in between-S-box variance.

## Secondary depth context

Compute analogous paired R3→R4 statistic with seed `92034` and record the descriptive trajectory `V3, V4, V5`.

The R3→R4 result is secondary and cannot rescue a failed primary 4→5 test.

## Frozen classification

All engineering/provenance requirements must pass:
1. exactly 360 trainings;
2. exact fresh seed registry;
3. frozen panel digest and classical revalidation;
4. deterministic receipts and byte-identical aggregate rerun;
5. neural evolutionary pressure = false.

Baseline R4 signal must be interpretable:
6. R4 blocked heterogeneity p < 0.05;
7. R4 candidate score range >= 0.015;
8. at least one R4 candidate mean advantage >= 0.04 and exceeds its R4 mean null advantage by >= 0.02.

Classification:
- if any requirement 1–8 fails: `phase2ad_inconclusive_baseline_or_provenance`;
- else if `Delta45 > 0`, paired permutation p < 0.05, and `V5 / V4 <= 0.75`: `phase2ad_depth_attenuation_supported`;
- otherwise: `phase2ad_depth_attenuation_not_supported`.

R5 heterogeneity p is recorded but is not a prerequisite for the attenuation test; loss of R5 heterogeneity is part of what the hypothesis is designed to explain.

## No-run lock

No Phase-2A-D neural training may run until:
- protocol and public issue exist;
- RED→GREEN contract evidence exists;
- exact 360-training workflow is reviewed;
- CI and historical benchmark are green;
- PR diff is inspected;
- a dedicated execution marker is committed to freeze the scientific SHA.

## Interpretation boundary

Educational/defensive 32-bit ToySPN only. No deployed primitive, no operational key recovery, no AES weakness claim, no production-security claim, no physical side-channel claim, and no neural-resistance claim.

Regardless of result, Phase 2B remains blocked. Any Neural Oracle qualification requires a separately preregistered confirmation experiment.