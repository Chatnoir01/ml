# Phase 2A-U — Fresh-panel fixed-depth cross-architecture Neural Oracle qualification

Status: preregistered publicly in issue #79 before implementation, panel reconstruction, or Phase-2A-U neural training.

Execution lock: issue #80.

Base: `main` after Phase 2A-T merge `d040f11df1755a06a08fddf92065a29ee31f4d99`.

## Purpose

Phase 2A failed only the cross-regime candidate-rank replication check while both sides showed significant S-box-specific heterogeneity. That comparison changed architecture, depth, and input-difference family simultaneously. Phase 2A-T subsequently replicated a strong depth-4 S-box separation peak on fresh neural seeds.

Phase 2A-U isolates architecture stability at a single frozen depth/difference family and uses a fresh classical panel so qualification is not based only on the repeatedly inspected Phase-2A panel.

No neural score may influence evolution during Phase 2A-U.

## Fresh classical source seeds

Use exactly:

`(90601, 90617, 90631, 90641, 90647, 90659, 90671, 90677, 90679, 90697, 90703, 90709)`

For every seed:
- replay frozen Phase-1O Arm A with exactly `340` classical evaluations;
- replay independently twice;
- require identical ordered terminal fingerprints;
- preserve full terminal permutations and classical metrics;
- execute no neural model during panel construction.

Eligible terminal candidates must recompute exactly:
- bijective 8x8;
- DU `8`;
- NL `100`;
- max absolute linear correlation `56`;
- algebraic degree `7`;
- `|SAC - 0.5| <= 0.05`.

Selection is classical-only:
1. at most one eligible candidate per source seed;
2. if multiple eligible terminal candidates occur for one seed, select the lexicographically smallest SHA-256 S-box fingerprint;
3. among per-seed representatives, select the lexicographically smallest six fingerprints;
4. if fewer than six source seeds are eligible, verdict is `phase2au_inconclusive_prerequisites` and zero neural training is authorized.

The six full permutations, source seeds, fingerprints, classical metrics, panel digest, and replay provenance must be committed before neural execution.

## Frozen neural regime

Educational 32-bit ToySPN only.

Both architectures use exactly:
- rounds: `4`;
- differences: `0x00000001`, `0x00000100`;
- existing frozen round keys, balanced pair generator, train/validation/test split, architecture hyperparameters, optimizer/training procedures, AUC implementation, and deterministic held-out-label null diagnostic.

Architectures:
- `bit_relu_mlp`;
- `byte_tanh_mlp`.

## Fresh paired neural seeds

Dataset seeds:
`(100003, 100019, 100043, 100049, 100057, 100069, 100103, 100109)`

Model seeds:
`(110003, 110017, 110023, 110039, 110051, 110071, 110083, 110107)`

The eight paired seed pairs are reused across all candidates, differences, and architectures. No retry/replacement based on results.

## Exact neural budget

Per architecture: `6 x 2 x 8 = 96` trainings.

Total: **192 neural trainings exactly**.

## Training endpoints

Every record must include:
- test AUC;
- neural advantage `2 * abs(test_AUC - 0.5)`;
- deterministic null AUC / null advantage;
- validation AUC;
- test accuracy;
- candidate fingerprint/source seed;
- architecture;
- rounds;
- input difference;
- dataset seed;
- model seed.

Candidate score per architecture = mean neural advantage across that candidate's 16 trainings.

## Per-architecture heterogeneity

Within each architecture, use a blocked S-box heterogeneity permutation test that preserves `(difference, paired replicate)` blocks and shuffles only S-box identity within each block.

Exactly 10,000 deterministic permutations:
- `bit_relu_mlp`: seed `120011`;
- `byte_tanh_mlp`: seed `120017`.

Report heterogeneity variance, p-value, candidate score range, signal condition, and rank order.

## Cross-architecture endpoint

Compute Spearman rank correlation between the six candidate scores from `bit_relu_mlp` and `byte_tanh_mlp`.

## Frozen consensus score

For candidate `i`:

`consensus_i = (bit_relu_score_i + byte_tanh_score_i) / 2`

No normalization or weighting.

For consensus:
- score range;
- blocked heterogeneity over `(architecture, difference, paired replicate)` blocks;
- exactly 10,000 deterministic permutations with seed `120041`;
- candidate rank order.

## Frozen seed robustness

Split paired replicates before execution:
- half A: indices `0,1,2,3`;
- half B: indices `4,5,6,7`.

Recompute candidate consensus scores within each half using both architectures and both differences. Compute Spearman correlation between half-A and half-B six-candidate consensus scores.

## Frozen signal condition

For each architecture, at least one candidate must have:
- mean neural advantage `>= 0.04`;
- mean neural advantage minus mean null advantage `>= 0.02`.

## Prerequisites

All required before scientific interpretation:
1. exactly six fresh panel candidates selected by the frozen classical-only rule;
2. exact classical tuple/fingerprint revalidation;
3. all twelve source seeds deterministic across two 340-evaluation replays;
4. exactly 192 neural trainings with complete provenance;
5. deterministic panel/aggregate receipts;
6. neural evolutionary pressure `false`.

Any failure => `phase2au_inconclusive_prerequisites`.

## Qualification criteria

If prerequisites pass, all must pass:
1. bit-ReLU heterogeneity `p < 0.05`;
2. byte-tanh heterogeneity `p < 0.05`;
3. bit-ReLU candidate score range `>= 0.015`;
4. byte-tanh candidate score range `>= 0.015`;
5. cross-architecture Spearman `>= 0.60`;
6. bit-ReLU signal condition;
7. byte-tanh signal condition;
8. consensus heterogeneity `p < 0.05`;
9. consensus score range `>= 0.015`;
10. split-half consensus Spearman `>= 0.60`.

All pass => `phase2au_depth4_consensus_oracle_qualified`.
Otherwise => `phase2au_oracle_not_qualified`.

Where applicable, thresholds reuse the original Phase-2A qualification thresholds rather than Phase-2A-T observed effect sizes.

## Transition rule

PASS makes a separately preregistered matched-budget Phase 2B GA-only vs GA+NN experiment eligible. It does not start evolution or choose a neural weight.

FAIL is preserved; no in-place retuning on these candidates/seeds.

## Interpretation boundary

ToySPN educational/defensive evidence only. No operational key recovery, AES/deployed-cipher weakness, production-security claim, physical side-channel claim, neural-resistance proof, or successful GA↔NN co-evolution claim.