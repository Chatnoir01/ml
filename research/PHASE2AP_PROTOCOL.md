# Phase 2A-P — Fresh confirmation of an R4 neural-separation peak

Status: **PREREGISTERED / NO NEURAL EXECUTION AUTHORIZED**

Public preregistration: issue #70.
Base `main`: `ee059de7c4e8681d256054a4f20e9d3bedf24668`.

## Question
Does the frozen ToySPN + `byte_tanh_mlp` pipeline exhibit a reproducible local maximum of S-box-specific neural separation at 4 rounds relative to both 3 and 5 rounds?

This is a new follow-up to the frozen negative Phase 2A-D result; Phase 2A-D is not retuned.

## Frozen design
- panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- architecture: `byte_tanh_mlp`
- depths: `(3, 4, 5)`
- differences: `(0x00000001, 0x00000100)`
- same existing ToySPN keys, pair generator, split, training hyperparameters, neural-advantage endpoint and deterministic null endpoint
- only depth changes across R3/R4/R5

## Fresh paired seeds
Dataset seeds:
`(74003, 74011, 74017, 74021, 74027, 74047, 74051, 74071, 74077, 74093, 74101, 74131, 74143, 74149, 74161, 74167, 74179, 74189, 74197, 74201)`

Model seeds:
`(84011, 84017, 84029, 84037, 84047, 84053, 84059, 84061, 84067, 84083, 84089, 84101, 84109, 84127, 84131, 84137, 84143, 84163, 84179, 84181)`

Pair by index and reuse across all six candidates, both differences and all three depths. No result-based retry or replacement.

## Exact budget
Per depth: `6 × 2 × 20 = 240` trainings.

Total: **720 neural trainings exactly**.

Neural evolutionary pressure is forbidden.

## Primary blockwise peak endpoint
For each matched `(difference, replicate)` block at each depth:

`D_r,b = population variance across the six candidate neural advantages`.

There are 40 blocks per depth.

Primary contrasts:
- `C43 = mean(D4 - D3)`
- `C45 = mean(D4 - D5)`

Use one-sided paired sign-flip permutation tests over the 40 matched block differences with 20,000 deterministic permutations.

Permutation seeds:
- R4>R3: `94043`
- R4>R5: `94045`

Family-wise alpha: Bonferroni, so each primary p-value must be `< 0.025`.

Effect-size requirements:
- `mean(D3)/mean(D4) <= 0.75`
- `mean(D5)/mean(D4) <= 0.75`

## Secondary per-depth summaries
For each depth report candidate mean advantages/null advantages, candidate-score variance/range, blocked S-box heterogeneity with 20,000 deterministic permutations, and the existing signal condition.

Heterogeneity permutation seeds:
- R3: `95003`
- R4: `95004`
- R5: `95005`

## Frozen prerequisites
1. exactly 720 trainings;
2. exact seed/provenance matrix;
3. frozen panel digest and classical revalidation;
4. deterministic cell receipts and byte-identical aggregate rerun;
5. neural evolutionary pressure absent;
6. R4 baseline signal gate passes: heterogeneity p<0.05, range>=0.015, at least one candidate mean advantage>=0.04 and exceeds its mean null by>=0.02.

If any prerequisite fails: `phase2ap_inconclusive_prerequisite`.

## Frozen verdict
If prerequisites pass and both sides satisfy:
- contrast > 0;
- paired p < 0.025;
- neighbor/R4 mean block-dispersion ratio <= 0.75;
then `phase2ap_r4_peak_supported`.

Otherwise `phase2ap_r4_peak_not_supported`.

The aggregate must report each side independently, but a one-sided partial success cannot be promoted to the full peak verdict.

No in-place changes to seeds, panel, model, differences, depths, statistics, thresholds or budget after execution authorization.

## Interpretation boundary
Educational/defensive 32-bit ToySPN only. This cannot establish AES/deployed-cipher weakness, operational key recovery, physical side-channel resistance, production security, neural resistance, or successful GA↔NN co-evolution.

**Phase 2B remains blocked regardless of outcome.**
