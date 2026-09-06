# Phase 2A-S — depth / neural-signal attenuation preregistration

## Status
Preregistered before implementation or scientific execution.

## Motivation
Phase 2A-R ended `phase2ar_inconclusive_signal`. With fresh seeds, adjacent candidate rankings remained nominally stable, but the frozen S-box heterogeneity prerequisite passed at 4 rounds and failed at 5 rounds. This suggests — but does not establish — attenuation of candidate-specific neural separation with depth.

Phase 2A-S tests that hypothesis directly. It is diagnostic only. It cannot qualify a Neural Oracle and cannot authorize GA↔NN feedback.

## Frozen panel
Reuse exactly the six committed Phase-2A candidates in `src/adversarial_sbox/phase2a_candidates.py`, panel digest `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`.

Every candidate must revalidate before training as bijective with DU=8, NL=100, max |LAT|=56, algebraic degree=7, and the existing SAC hard bound. No candidate replacement or selection is allowed.

## Frozen neural regime
Hold architecture/representation and difference family fixed to the Phase-2A-R B/C bridge:
- architecture: `byte_tanh_mlp`
- differences: `0x00000001`, `0x00000100`
- depths: **3, 4, 5 rounds**

Only round depth changes.

## Fresh paired neural seeds
Use ten fresh paired replicates, fixed before execution:
- dataset seeds: 72001, 72019, 72031, 72043, 72053, 72077, 72089, 72101, 72109, 72139
- model seeds: 82003, 82013, 82021, 82037, 82051, 82067, 82073, 82091, 82109, 82129

Implementation must verify these seeds do not overlap Phase 2A / Phase 2A-R scientific seeds. No seed may be replaced or retried because of its result.

## Exact budget
For each depth: 6 candidates × 2 differences × 10 paired replicates = 120 trainings.

Total: **360 neural trainings exactly**.

No neural score may enter evolution.

## Frozen endpoints
Per candidate/depth, score = mean neural advantage across its 20 trainings.

For each depth independently:
1. exact provenance/training count;
2. deterministic null-label diagnostic preserved from Phase 2A;
3. blocked S-box heterogeneity permutation test with exactly 10,000 deterministic permutations;
4. candidate score range;
5. signal check using the existing Phase-2A definitions.

Also compute:
- candidate-rank Spearman rho(3,4), rho(4,5), rho(3,5);
- heterogeneity effect statistic used by the existing blocked permutation test at each depth;
- candidate score range at each depth.

## Frozen primary hypothesis / classification
Signal prerequisite at a depth requires the existing Phase-2A conditions: heterogeneity p < 0.05, candidate score range >= 0.015, and at least one candidate mean advantage >= 0.04 and >= its depth mean null advantage + 0.02, plus exact provenance and deterministic receipts.

Classify without retuning:
- if 3-round and 4-round signal prerequisites PASS, 5-round FAILS, and both the heterogeneity effect statistic and candidate score range at 5 rounds are strictly lower than at 4 rounds: `phase2as_depth_attenuation_supported`;
- if all 3 depths PASS: `phase2as_signal_persists_to_5_rounds`;
- if 3 or 4 rounds FAIL: `phase2as_inconclusive_baseline_signal`;
- otherwise: `phase2as_inconclusive_depth_effect`.

Rank correlations are secondary diagnostics and cannot override the primary classification.

## Reproducibility / execution lock
- red→green engineering evidence before scientific execution;
- scientific workflow remains dormant until a dedicated `research/PHASE2AS_EXECUTE.md` marker is committed after green CI, historical benchmark, and diff inspection;
- execution SHA is frozen by that marker;
- aggregate scientific payload is rerun deterministically and must match byte-for-byte/canonical digest;
- no result-dependent seed changes, threshold changes, retries, candidate replacement, or in-place tuning.

## Interpretation boundary
ToySPN / educational defensive research only. No operational key recovery. No claim of AES or deployed-cipher weakness, physical side-channel resistance, production security, neural resistance, or successful GA↔NN co-evolution.

Regardless of outcome, Phase 2B remains blocked. Any future oracle qualification requires a separately preregistered fresh-panel/fresh-seed confirmation.