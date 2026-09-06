# Phase 2A-U2 — Frozen Fresh-Seed Oracle Requalification Result

## Official verdict

**`phase2au2_oracle_qualified`**

Phase 2A-U2 repaired the post-hoc Phase 2A-U seed-provenance defect and re-ran the frozen 4-round Neural Oracle qualification on two seed blocks proven disjoint from the complete prior frozen/executed Phase-2 neural registry.

No in-place retuning is authorized from this result.

## Provenance

- remediation preregistration: issue #85
- provenance defect: issue #86
- execution lock: issue #89
- scientific execution SHA: `8f5ff968a13e14515fbae3b6c263c08f88a22760`
- workflow run: `34061373215`
- workflow conclusion: `success`
- exact neural trainings: `192 / 192`
- aggregate artifact ID: `9997583020`
- aggregate artifact ZIP SHA-256: `1c5bede819068fef2249ecb99415818b9b2be6c30c758a1cc74e767755d7c57c`
- aggregate payload SHA-256: `d5b904483859f0f443d97098d6f63de9a086969c6105dd40ddeb412bb88b6750`
- frozen panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- architecture: `byte_tanh_mlp`
- ToySPN depth: `4`
- input differences: `0x00000001`, `0x00000100`
- pair count per training: `8192`
- exact split sizes: train=`5734`, validation=`1228`, test=`1230`
- paired replicates per block: `8`
- independent blocks: `A`, `B`
- blocked heterogeneity permutations per block: `10,000`
- neural evolutionary pressure: `false`

## Evidence artifacts

Summary:
- ID `9997583020`
- SHA-256 `1c5bede819068fef2249ecb99415818b9b2be6c30c758a1cc74e767755d7c57c`

Cells:
- A-d1: ID `9997577965`, SHA-256 `58bc5b5ac5bbca24f5653a8d4b0422c3da397b02e836e3eac198740c067363ba`
- A-d100: ID `9997577442`, SHA-256 `e13020e209ddb00ee01f2733b8bc6ac8900195961e3f0f8f03ed454245a482bd`
- B-d1: ID `9997575602`, SHA-256 `f1d228b7d1d0cfd2d930e1837b5ddf38db3cbd93223ae1ab7fc2a954db8d8042`
- B-d100: ID `9997578159`, SHA-256 `08afa870f73f9f0ddbf9e7536e13a456471189ee14fa86c1de2474d32e21656c`

The aggregate was computed twice from the same four cell artifacts and the two JSON outputs were byte-identical before the official result was uploaded.

## Frozen prerequisite checks

All prerequisites passed:

- exact 192 training/provenance count: **PASS**
- frozen panel digest and classical revalidation: **PASS**
- deterministic receipts: **PASS**
- exact pair count `8192`: **PASS**
- exact split sizes `5734 / 1228 / 1230`: **PASS**
- signal condition in Block A: **PASS**
- signal condition in Block B: **PASS**
- complete U2 seed registry exact and disjoint from all prior frozen/executed Phase-2 neural registries: **PASS**
- neural evolutionary pressure absent: **PASS**

Therefore `prerequisites_pass = true`.

## Block A

Candidate mean neural advantages in frozen panel order:

`[0.3757506339892249, 0.2667843517859274, 0.3113315829281651, 0.2877567106186147, 0.3462052678735267, 0.3340911648519804]`

Candidate mean null advantages:

`[0.023441641059773956, 0.029701676178121736, 0.02776829774153495, 0.02245651149188565, 0.026449079716052572, 0.022276412976196105]`

- mean neural advantage: `0.3203199520079065`
- heterogeneity variance: `0.001323245390865378`
- blocked heterogeneity p: `9.999000099990002e-05`
- candidate score range: `0.10896628220329752`
- rank order: `[0, 4, 5, 2, 3, 1]`
- signal condition: **PASS**
- exact 96 trainings: **PASS**

## Block B

Candidate mean neural advantages in frozen panel order:

`[0.3695929641949338, 0.2826123091399054, 0.33636341428799643, 0.2875621502909336, 0.3475247489881187, 0.3625433521990396]`

Candidate mean null advantages:

`[0.026827899568801, 0.030138102983859105, 0.02367407002393509, 0.02188550592865659, 0.022502975532860965, 0.02588493284810077]`

- mean neural advantage: `0.33103315651682125`
- heterogeneity variance: `0.0011690737188734983`
- blocked heterogeneity p: `9.999000099990002e-05`
- candidate score range: `0.08698065505502839`
- rank order: `[0, 5, 4, 2, 3, 1]`
- signal condition: **PASS**
- exact 96 trainings: **PASS**

## Cross-block stability

- Spearman correlation: `0.9428571428571428`
- top-2 overlap: `1`
- absolute candidate score differences:
  `[0.00615766979429111, 0.015827957353978017, 0.025031831359831336, 0.00019456032768105924, 0.0013194811145920138, 0.028452187347059177]`
- mean absolute candidate-score difference (MAD): `0.01283061454957212`

## Preregistered qualification checks

All frozen qualification criteria passed:

- Block A heterogeneity `p < 0.05`: **PASS**
- Block B heterogeneity `p < 0.05`: **PASS**
- Block A score range `>= 0.05`: **PASS**
- Block B score range `>= 0.05`: **PASS**
- cross-block Spearman `>= 0.80`: **PASS**
- top-2 overlap `>= 1`: **PASS**
- cross-block MAD `<= 0.05`: **PASS**

Therefore the frozen classification is:

**`phase2au2_oracle_qualified`**

## Interpretation

Within this exact educational/defensive ToySPN setup, the 4-round `byte_tanh_mlp` scoring procedure reproduced strong S-box-specific heterogeneity and stable candidate ranking across two genuinely fresh neural replicate blocks after correcting the Phase 2A-U provenance defect.

This U2 PASS restores the scientific consequence gate required before first neural evolutionary pressure. The historical Phase 2A-U output remains preserved as historical evidence, with its freshness defect documented separately in `research/PHASE2AU_AUDIT.md`.

## Consequence boundary

Phase 2A-U2 did **not** feed neural scores into evolution. It is not GA↔NN co-evolution.

This PASS makes a **separately preregistered matched-budget Phase 2B GA ← Oracle experiment eligible**. Phase 2B must still freeze its control/treatment arms, evolutionary budget, Oracle use, seeds, primary endpoint, statistics, invalidation rules, and human-supervised execution gate before any neural pressure enters selection.

No deployed-cipher, AES, physical side-channel, operational key-recovery, production-security, or universal neural-cryptanalysis claim is made.
