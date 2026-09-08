# Phase 2F — Minimal classical-band neural pressure

Status: **PREREGISTERED / PRE-MARKER / NOT EXECUTED**.

Governance: GitHub issues #115 (scientific preregistration) and #116 (execution lock).
Base main at preregistration: `a2ca53eac2cbf0793470e89ffc0e7bf76f489f59`.

Phase 2D remains the valid negative result `phase2d_bounded_persistence_not_supported`. Phase 2E remains descriptive only and does not rescue it.

## Question

Does a frozen neural score create useful candidate-specific evolutionary pressure when it may act inside the smallest predeclared local classical neighborhood around an actual selection cutoff, while hard constraints and terminal classical quality remain protected?

This is still one-way **GA ← frozen-procedure neural guidance**. It is not adaptive bidirectional GA↔NN co-evolution.

## Frozen search geometry

- population: 20
- shortlist: 8
- parents: 4
- proposals/parent: 4
- proposals/generation: 16
- generations: 20
- exactly 340 classical evaluations per arm/seed
- same initial population across matched arms
- historical Phase-1O proposal engine
- hard constraints mandatory
- terminal selection: historical classical-only

Protected scientific key:
`(admissible, NL, -DU, -max|LAT|, algebraic_degree)`.

## B1 local band

Reference = historical cutoff candidate at each shortlist/survival cutoff.

Candidate is B1-eligible iff all hold:
- same admissibility value as reference;
- `abs(NL - NL_ref) <= 2`;
- `abs(DU - DU_ref) <= 2`;
- `abs(max_abs_LAT - max_abs_LAT_ref) <= 2`;
- algebraic degree exactly equal.

The no-outside-candidate-crossing clause is implemented conservatively as the maximal **contiguous** run of B1-eligible candidates containing the historical cutoff reference. Expansion stops at the first outside-band candidate on each side. This clarification was recorded in #115 before scientific execution.

Only a band straddling the cutoff is an actionable boundary opportunity. No global neural reranking is allowed.

## Arms

- `C`: historical classical control; neural scores audit/padding only.
- `O0`: exact protected-key neural baseline; no persistence.
- `B1`: real frozen neural score inside the B1 cutoff band; no persistence.
- `SB1`: identical B1 machinery with deterministic shuffled candidate↔score association.

No terminal neural reranking in any arm.

## Fresh evolution seeds

`(526011, 526023, 526037, 526049, 526061, 526073, 526087, 526099, 526111)`

## Frozen neural measurement procedure

- architecture: `byte_tanh_mlp`
- ToySPN depth: 4
- differences: `(0x00000001, 0x00000100)`
- pair count: 8192
- split: `(5734, 1228, 1230)`
- 8 paired dataset/model replicates per candidate
- lower mean neural advantage is better

### Fitness Block G
Dataset seeds:
`(576003, 576017, 576031, 576043, 576059, 576071, 576083, 576097)`

Model seeds:
`(586009, 586021, 586033, 586047, 586061, 586073, 586087, 586099)`

### Held-out Block X
Dataset seeds:
`(676003, 676017, 676029, 676043, 676057, 676071, 676083, 676099)`

Model seeds:
`(686007, 686019, 686031, 686043, 686061, 686073, 686091, 686103)`

## Compute lock

Per arm/seed:
- 340 classical evaluations;
- exactly 32 candidate fitness scores;
- 16 trainings per candidate score;
- 512 fitness trainings.

Across 36 cells: 18,432 fitness trainings.

Held-out after terminal freeze only: 36 terminals × 16 = 576 trainings.

Total scientific neural trainings: **19,008**.

No partial group/band scoring. After score-budget closure, later opportunities are observational-only. Padding is deterministic, post-terminal and cannot affect evolution.

## Blindness

All 36 arm cells using only classical metrics + Block G → deterministic 36-terminal freeze → only then physically separate Block-X validation → deterministic aggregation.

Block X cannot affect implementation, retries, band width, score budget, candidate selection or terminal reranking.

## Mechanism activity

B1 must produce at least one real **cross-protected-key** score-caused membership change on at least 6/9 evolution seeds. Exact-key-only membership changes do not satisfy this gate.

## Classical non-degradation

For every seed, B1 terminal must be no worse than C componentwise on:
- admissibility/target status;
- NL;
- DU;
- max |LAT|;
- algebraic degree.

Held-out neural improvement cannot compensate for classical degradation.

## Support rule

`phase2f_minimal_band_pressure_supported` only if all seven pass:
1. B1 real cross-key mechanism activity on >=6/9 seeds;
2. B1 held-out X lower than O0 on >=8/9 seeds;
3. one-sided exact paired sign test B1<O0 has p<.05;
4. mean paired reduction `mean(O0-B1) >= .02`;
5. classical non-degradation vs C on all 9 seeds;
6. B1 held-out X lower than SB1 on >=6/9 seeds;
7. mean B1 held-out X strictly lower than mean SB1.

If prerequisites are valid but any support gate fails: `phase2f_minimal_band_pressure_not_supported`.

If provenance/seed/budget/blindness/receipt/determinism/band invariants fail: `phase2f_inconclusive_prerequisites`.

## Marker

Scientific execution remains forbidden until a later qualified commit creates:
`research/PHASE2F_EXECUTE.md`
with exact token:
`AUTHORIZED_PHASE2F_MINIMAL_BAND_EXPERIMENT`

## Anti-HARKing

No outcome-driven changes to seeds, B1 radii, arms, budgets, endpoints or support thresholds. No persistence tags. No terminal neural reranking. No adaptive retraining from GA outcomes. No full bidirectional loop.

Scope is educational/defensive ToySPN research only. No deployed-cipher/AES claim, operational key recovery, side-channel claim or adaptive attack deployment.
