# Phase 2A-R — Neural Rank-Instability Decomposition

Status: preregistered before implementation results or Phase-2A-R neural execution.

Public preregistration: issue #60.
Base commit: `d32912b3818a15152edcceef38f5221446a9d01f` (Phase 2A negative result merged).

## Purpose

Phase 2A showed statistically significant S-box-specific neural heterogeneity under both frozen neural regimes but failed cross-regime rank replication (`Spearman = -0.08571428571428572`). Because oracle and challenger differed simultaneously in neural architecture/representation, round count, and input-difference family, Phase 2A cannot localize the source of rank instability.

Phase 2A-R is a **diagnostic decomposition only**. It cannot qualify a Neural Oracle and cannot authorize neural evolutionary pressure or Phase 2B.

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

No candidate selection or replacement is allowed.

## Frozen bridge regimes

A. `bit_relu_mlp`, 4 rounds, differences `0x00000001`, `0x00000100`.

B. `byte_tanh_mlp`, 4 rounds, differences `0x00000001`, `0x00000100`.

C. `byte_tanh_mlp`, 5 rounds, differences `0x00000001`, `0x00000100`.

D. `byte_tanh_mlp`, 5 rounds, differences `0x00010000`, `0x01000000`.

Adjacent transitions isolate one frozen factor bundle:
- A→B: neural architecture/representation bundle only;
- B→C: round count only;
- C→D: input-difference family only.

## Fresh paired neural seeds

Dataset seeds:
`71001, 71009, 71023, 71039, 71059`

Model seeds:
`81001, 81013, 81031, 81041, 81047`

They were searched on current `main` before issue #60 and had no repository matches. The same paired seeds are reused across all six candidates and every regime/difference cell. No result-based retry or replacement is allowed.

## Exact training budget

Each regime: 6 candidates × 2 differences × 5 paired replicates = 60 trainings.

Total: **240 neural trainings exactly**.

No neural score enters GA selection, mutation, ranking, acceptance, proposal generation, or any evolutionary feedback.

## Endpoints and statistics

Preserve Phase-2A training endpoints and deterministic held-out-label permutation null diagnostic.

For every regime/candidate, score = mean neural advantage over the candidate's 10 trainings.

For each regime independently:
- blocked S-box heterogeneity permutation test preserving `(difference, paired replicate)` blocks;
- 10,000 deterministic permutations;
- candidate score range;
- same Phase-2A signal condition.

Compute adjacent Spearman correlations:
- `rho_AB`
- `rho_BC`
- `rho_CD`

Frozen rank-stability threshold: **rho >= 0.60**, inherited from Phase 2A and not estimated from Phase-2A-R results.

## Signal prerequisites

Before interpreting rank transitions, every regime must pass:
1. exact training/provenance count;
2. panel classical revalidation;
3. blocked heterogeneity p < 0.05;
4. candidate score range >= 0.015;
5. at least one candidate mean advantage >= 0.04 and exceeds its regime mean null advantage by >= 0.02;
6. deterministic receipts.

Any failed prerequisite yields `phase2ar_inconclusive_signal`.

## Frozen diagnostic classification

If all four regimes meet signal prerequisites, classify adjacent transitions by `rho >= 0.60`:

- only A→B unstable → `phase2ar_architecture_transition_localized`
- only B→C unstable → `phase2ar_round_transition_localized`
- only C→D unstable → `phase2ar_difference_transition_localized`
- two or three unstable transitions → `phase2ar_multiple_instabilities`
- all three stable → `phase2ar_no_adjacent_instability`

This classification is descriptive/diagnostic. None of these outcomes qualifies an oracle.

## Interpretation boundary

Educational 32-bit ToySPN only. No deployed primitive, no operational key recovery, no AES weakness claim, no production-security claim, no physical side-channel claim, and no neural-resistance claim.

Regardless of the result, Phase 2B remains blocked. A future oracle qualification requires a separately preregistered confirmation experiment with fresh panel/data as appropriate.
