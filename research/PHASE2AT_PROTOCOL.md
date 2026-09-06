# Phase 2A-T Protocol — Fresh-Seed Replication of the Depth-4 Separation Peak

Public preregistration: issue #76. Execution lock: issue #77.

## Purpose

Phase 2A-S rejected its preregistered global monotonic 3→4→5 attenuation hypothesis. Its frozen data instead showed a post-result non-monotonic profile: near-saturated overall distinguishing with very small between-S-box separation at depth 3, strongest S-box-specific separation at depth 4, and smaller separation at depth 5.

Phase 2A-T is a new fresh-seed replication of that profile hypothesis. It does not revise or retune Phase 2A-S.

## Frozen panel

Use exactly the six candidates committed in `src/adversarial_sbox/phase2a_candidates.py` with panel digest:

`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30`

Before training, every candidate must revalidate as bijective and satisfy DU=8, NL=100, max |LAT|=56, algebraic degree=7 and the existing SAC hard bound.

## Frozen neural design

- architecture: `byte_tanh_mlp`
- ToySPN depths: exactly `(3, 4, 5)`
- input differences at every depth: `0x00000001`, `0x00000100`
- pair count, split, training implementation and deterministic null-label diagnostic unchanged from the existing Phase-2A family
- no neural evolutionary pressure

## Fresh paired seeds

Dataset seeds:
`(73003, 73019, 73031, 73043, 73061, 73079, 73091, 73103)`

Model seeds:
`(83003, 83017, 83029, 83047, 83059, 83071, 83089, 83101)`

Eight paired replicates are reused across every candidate, difference and depth.

Blocked-permutation seeds:
`{3: 93001, 4: 93011, 5: 93023}`

Blocked permutations per depth: exactly `10_000`.

## Exact budget

Each depth/difference cell: 6 candidates × 8 paired replicates = 48 trainings.

Each depth: 96 trainings.

Total: exactly **288 neural trainings**.

## Frozen endpoints

For every depth compute:
- candidate mean neural advantage across 16 trainings;
- candidate mean deterministic null advantage;
- mean neural advantage across the six candidates `M_r`;
- blocked between-S-box heterogeneity variance `H_r` and its permutation p-value;
- candidate score range `R_r`;
- existing signal condition;
- descriptive candidate ranks and Spearman `rho_34`, `rho_45`.

## Frozen prerequisites

Before interpreting the profile require all:
1. exact 288 training/provenance count;
2. panel digest and classical revalidation pass;
3. deterministic receipts;
4. signal condition passes at all three depths;
5. neural evolutionary pressure is absent.

If any fail: `phase2at_inconclusive_prerequisites`.

## Primary replication rule

Directional depth-4 peak conditions:
- `H4 > H3` and `H4 > H5`;
- `R4 > R3` and `R4 > R5`;
- `M3 > M4 > M5`.

Depth 4 must additionally have blocked heterogeneity `p < 0.05` for full replication.

Classification:
- prerequisites fail → `phase2at_inconclusive_prerequisites`
- all directional conditions and depth-4 p<0.05 → `phase2at_depth4_peak_replicated`
- all directional conditions but depth-4 p>=0.05 → `phase2at_peak_direction_only`
- otherwise → `phase2at_depth_profile_not_replicated`

The exact Phase-2A-S observed H/R ratios are deliberately not reused as new thresholds.

## Interpretation boundary

This is a ToySPN educational/defensive experiment only. It does not perform operational key recovery and makes no AES/deployed-cipher weakness, physical side-channel, production-security, neural-resistance or successful GA↔NN claim.

Phase 2B remains blocked regardless of Phase 2A-T outcome. A Neural Oracle still requires a separately preregistered qualification/confirmation experiment.
