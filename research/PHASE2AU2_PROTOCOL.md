# Phase 2A-U2 — Fresh-seed Neural Oracle requalification protocol

Public remediation preregistration: issue #85  
Provenance defect: issue #86  
Phase 2B lock: issue #87  
Aggregation hardening: issue #88  
Execution lock: issue #89  
Base `main`: `4400e10c3dcc8be8442a90a11cb33be157d737f8`

## Purpose

Phase 2A-U2 repairs a provenance defect discovered after the historical Phase 2A-U run. It asks the same frozen scientific question as Phase 2A-U, but requires neural seeds that are disjoint from every prior frozen/executed Phase-2 neural registry under the corrected central registry.

The historical Phase 2A-U outputs are preserved. U2 does not reinterpret or modify their observed scores. Phase 2B remains locked throughout U2.

## Frozen panel

Use exactly `src/adversarial_sbox/phase2a_candidates.py` with panel digest:

`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`

All six candidates must revalidate as bijective 8×8 with DU=8, NL=100, max |LAT|=56, algebraic degree=7, and SAC within the existing hard bound.

## Frozen neural regime

- architecture: `byte_tanh_mlp`
- ToySPN rounds: exactly `4`
- input differences: exactly `0x00000001`, `0x00000100`
- pair count: exactly `8192` per training
- deterministic split: exactly train=`5734`, validation=`1228`, test=`1230`
- existing optimizer/training procedure and deterministic null-label diagnostic unchanged
- no result-driven retry, early stopping, hyperparameter tuning, or seed replacement
- neural evolutionary pressure: `false`

## Fresh paired seeds

### Block A

Dataset seeds:
`(176003, 176017, 176029, 176041, 176057, 176069, 176081, 176093)`

Model seeds:
`(186007, 186019, 186031, 186043, 186061, 186073, 186091, 186103)`

### Block B

Dataset seeds:
`(177011, 177023, 177037, 177049, 177061, 177077, 177089, 177101)`

Model seeds:
`(187009, 187021, 187033, 187047, 187063, 187079, 187097, 187109)`

Blocked-permutation seeds:
- Block A: `196007`
- Block B: `196009`

Exactly `10,000` deterministic blocked permutations per block.

Before execution, the central Phase-2 neural seed registry must prove all 32 U2 dataset/model seed values are disjoint from every prior frozen/executed Phase-2 neural registry, including historical Phase 2A-U.

## Exact budget

Each block: 6 candidates × 2 differences × 8 paired replicates = 96 trainings.  
Total: **192 neural trainings exactly**.

No training outside this exact budget is authorized by this protocol.

## Frozen endpoints

Per block:
- candidate mean neural advantage over 16 trainings;
- blocked S-box heterogeneity variance and p-value;
- candidate score range;
- mean neural advantage;
- existing signal condition;
- exact candidate rank order.

Across blocks:
- Spearman correlation of six candidate means;
- top-2 overlap;
- per-candidate absolute score difference;
- mean absolute candidate-score difference (MAD).

## Frozen prerequisites

All required:
1. exact 192 training/provenance count;
2. exact frozen panel digest and classical revalidation;
3. deterministic receipts;
4. exact pair count and exact split sizes on every run;
5. signal condition passes in both blocks;
6. all 32 U2 neural seeds are exactly registered and disjoint from the complete prior Phase-2 neural registry;
7. neural evolutionary pressure is absent.

Failure of any prerequisite → `phase2au2_inconclusive_prerequisites`.

## Frozen qualification criteria

All required, unchanged from Phase 2A-U:
1. Block A heterogeneity `p < 0.05`;
2. Block B heterogeneity `p < 0.05`;
3. score range `>= 0.05` independently in both blocks;
4. cross-block Spearman `>= 0.80`;
5. top-2 overlap `>= 1`;
6. cross-block MAD `<= 0.05`.

All pass → `phase2au2_oracle_qualified`. Otherwise → `phase2au2_oracle_not_qualified`.

No threshold, seed, candidate, architecture, difference, endpoint, or budget may change after scientific execution based on observed results. A failure is preserved; no in-place retuning.

## Execution gate

No scientific U2 training may execute until all requirements in issue #89 are satisfied, including RED→GREEN CI on Python 3.10/3.11/3.12, provenance hardening, historical benchmark verification, marker-locked workflow, diff inspection, and a dedicated execution-marker commit freezing the scientific SHA.

## Consequence boundary

A U2 PASS makes a separately preregistered matched-budget Phase 2B **GA ← Oracle** experiment eligible. It does not itself inject neural scores into evolution and does not constitute full GA↔NN co-evolution.

Educational/defensive ToySPN only; no deployed-cipher, AES, physical side-channel, operational key-recovery, or production-security claim.
