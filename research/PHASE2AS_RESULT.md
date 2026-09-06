# Phase 2A-S — Frozen Result

## Official verdict

**`phase2as_depth_attenuation_not_supported`**

This file freezes the preregistered Phase 2A-S result exactly as produced by the scientific workflow. No in-place retuning is authorized from this result.

## Provenance

- public preregistration: issue #65
- execution lock: issue #67
- scientific SHA: `cea4d58a6d61f3f4809371d9496e28fcf909ea34`
- workflow run: `34023519266`
- exact neural trainings: `288`
- aggregate artifact ID: `9986308756`
- aggregate artifact ZIP SHA-256: `4568bc9056247cd2bbfaabd0e89285ec8ec22e59efdb4b3d331040f57148cfe7`
- aggregate payload SHA-256: `5f1e51ca5bb5205bc3b1ffaf21cd681eac8cbcc9a6b7430b6f74c9a636a1f0e2`
- frozen panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- architecture: `byte_tanh_mlp`
- depths: `3, 4, 5`
- input differences at every depth: `0x00000001`, `0x00000100`
- paired replicates: `8`
- blocked heterogeneity permutations per depth: `10,000`
- neural evolutionary pressure: `false`

## Frozen prerequisite checks

All prerequisites passed:

- exact 288 training/provenance count: PASS
- panel digest and classical revalidation: PASS
- deterministic receipts: PASS
- signal condition at all three depths: PASS
- neural evolutionary pressure absent: PASS

Therefore the primary magnitude-based attenuation criteria are interpretable under the preregistered rule.

## Depth results

| Depth | Heterogeneity variance H | Permutation p | Candidate score range R | Signal condition |
|---|---:|---:|---:|---|
| 3 | `3.834642664079041e-07` | `0.8543145685431457` | `0.001895628747876632` | PASS |
| 4 | `0.0009784073613733533` | `9.999000099990002e-05` | `0.08813938475965993` | PASS |
| 5 | `0.00010306389830195628` | `0.05909409059094091` | `0.02712136876076421` | PASS |

Adjacent candidate-rank Spearman correlations:

- `rho_34 = -0.6`
- `rho_45 = 0.7714285714285715`

Magnitude ratios:

- `H5 / H4 = 0.10533843301964675`
- `R5 / R4 = 0.30770998498252794`

## Preregistered attenuation checks

- `H3 > H4 > H5`: **FAIL**
- `H5 / H4 <= 0.50`: PASS
- `R3 >= R4 > R5`: **FAIL**
- `R5 / R4 <= 0.75`: PASS

Because the two monotonic 3→4→5 ordering requirements fail, the frozen classification is:

**`phase2as_depth_attenuation_not_supported`**

It must not be relabeled as `phase2as_weak_attenuation` or `phase2as_depth_attenuation_supported` after seeing the result.

## Candidate mean neural advantages

Depth 3:
`[0.9893108453472674, 0.9904698648518043, 0.99012800737415, 0.9897710626780869, 0.9912064740951441, 0.9896430712253846]`

Depth 4:
`[0.363619196633564, 0.2754798118739041, 0.32964023804459863, 0.2963209412862489, 0.3454390311546293, 0.3512278325073206]`

Depth 5:
`[0.04778618962411856, 0.03358988517455923, 0.03760992689564491, 0.036772374385989424, 0.060711253935323437, 0.05558210350781312]`

## Interpretation boundary

The preregistered global monotonic-depth hypothesis is **not supported**. The observed profile is non-monotonic:

- at 3 rounds, the distinguisher is nearly saturated for every candidate (mean neural advantages are all about 0.99), while between-S-box separation is extremely small;
- at 4 rounds, S-box-specific separation is strongest in this experiment;
- at 5 rounds, S-box-specific separation is much smaller than at 4 rounds while the 4→5 candidate ranking remains descriptively similar (`rho_45 ≈ 0.7714`).

The large local 4→5 reduction in effect magnitude is an observed result, but it does **not** rescue the preregistered 3→4→5 monotonic hypothesis. The depth-3 saturation pattern and the possibility of a peak-shaped depth profile are post-result hypotheses only and require a separately preregistered fresh-seed experiment before causal or confirmatory claims.

This ToySPN experiment does not establish AES/deployed-cipher weakness, key recovery, physical side-channel resistance, production security, neural resistance, or successful GA↔NN co-evolution.

**Phase 2B GA↔NN remains blocked.** A Neural Oracle still requires a separately preregistered qualification/confirmation path.
