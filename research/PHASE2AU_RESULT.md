# Phase 2A-U — Frozen Result

## Official verdict

**`phase2au_oracle_qualified`**

This file freezes the preregistered Phase 2A-U 4-round Neural Oracle qualification result exactly as produced by the scientific workflow. No in-place retuning is authorized from this result.

## Provenance

- public preregistration: issue #82
- execution lock: issue #83
- scientific SHA: `9ed3fcc0a1d8099edffb1e4db170851a4884e448`
- workflow run: `34059256750`
- exact neural trainings: `192`
- aggregate artifact ID: `9996948547`
- aggregate artifact ZIP SHA-256: `4f20fe58cf19ba572c58d50450169a50b299d2bf58c42163e7a6c5c5fc3bea42`
- aggregate payload SHA-256: `2e07461fadcada365e4e83ed38d8c0efd2c9270b636f0e25995687dd4c619dd8`
- frozen panel digest: `35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`
- architecture: `byte_tanh_mlp`
- ToySPN depth: `4`
- input differences: `0x00000001`, `0x00000100`
- paired replicates per block: `8`
- independent blocks: `A`, `B`
- blocked heterogeneity permutations per block: `10,000`
- neural evolutionary pressure: `false`

## Frozen prerequisite checks

All prerequisites passed:

- exact 192 training/provenance count: PASS
- frozen panel digest and classical revalidation: PASS
- deterministic receipts: PASS
- signal condition in Block A: PASS
- signal condition in Block B: PASS
- fresh Phase 2A-U seed registry disjoint from the known prior frozen Phase-2 seed registries: PASS
- neural evolutionary pressure absent: PASS

Therefore the preregistered qualification rule is interpretable.

## Block A

Candidate mean neural advantages in frozen panel order:

`[0.35732526115800195, 0.2665009319627707, 0.3384496688351554, 0.2992917837303632, 0.3414399953604309, 0.34647654603278183]`

Candidate mean null advantages:

`[0.022083052731542173, 0.02624956658879555, 0.02046762253102294, 0.031947399371524056, 0.02784443522861106, 0.02970987535409813]`

- mean neural advantage: `0.3249140311799173`
- heterogeneity variance: `0.0010067234298033686`
- blocked heterogeneity p: `9.999000099990002e-05`
- candidate score range: `0.09082432919523126`
- rank order by candidate index: `[0, 5, 4, 2, 3, 1]`
- signal condition: PASS
- exact 96 trainings: PASS

## Block B

Candidate mean neural advantages in frozen panel order:

`[0.3676229831162543, 0.2616530898121695, 0.3404441007106906, 0.29533869079266306, 0.32895175732276694, 0.35475696682617225]`

Candidate mean null advantages:

`[0.021073182301940975, 0.032324810580361525, 0.025996071271948168, 0.03266953187829159, 0.025496281115562902, 0.02787496817638173]`

- mean neural advantage: `0.3247945980967861`
- heterogeneity variance: `0.0013081172586182762`
- blocked heterogeneity p: `9.999000099990002e-05`
- candidate score range: `0.1059698933040848`
- rank order by candidate index: `[0, 5, 2, 4, 3, 1]`
- signal condition: PASS
- exact 96 trainings: PASS

## Cross-block stability

- Spearman correlation of candidate mean scores: `0.9428571428571428`
- top-2 overlap: `2`
- absolute candidate score differences:
  `[0.010297721958252348, 0.004847842150601189, 0.001994431875535163, 0.003953092937700131, 0.012488238037663968, 0.00828042079339042]`
- mean absolute candidate-score difference (MAD): `0.0069769579588572035`

## Preregistered qualification checks

All frozen qualification criteria passed:

- Block A heterogeneity `p < 0.05`: PASS
- Block B heterogeneity `p < 0.05`: PASS
- Block A score range `>= 0.05`: PASS
- Block B score range `>= 0.05`: PASS
- cross-block Spearman `>= 0.80`: PASS
- top-2 overlap `>= 1`: PASS
- cross-block MAD `<= 0.05`: PASS

Therefore the frozen classification is:

**`phase2au_oracle_qualified`**

## Interpretation boundary

Within this exact frozen educational/defensive ToySPN setup, the 4-round `byte_tanh_mlp` scoring procedure reproduced S-box-specific heterogeneity and candidate ranking strongly enough across two independent fresh replicate blocks to satisfy every preregistered Phase 2A-U Oracle-qualification criterion.

This qualification is bounded to the frozen six-candidate panel, ToySPN construction, 4-round depth, two input-difference family, training procedure, and scoring definition. It is not a universal neural-cryptanalysis result and does not establish a property of AES or any deployed cipher.

Phase 2A-U did **not** feed any neural score into evolution. No GA↔NN co-evolution was executed. No operational key recovery, deployed-cipher weakness, physical side-channel resistance, production-security guarantee, or neural-resistance claim is made.

The PASS makes a **separately preregistered Phase 2B matched-budget experiment eligible** under the consequence rule from issue #82. Phase 2B is not started or authorized by this file alone; it still requires its own protocol, controls, budget, receipts, and human-supervised execution gate.
