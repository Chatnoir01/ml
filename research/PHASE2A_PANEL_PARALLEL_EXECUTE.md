# Phase 2A parallel panel reconstruction authorization

`AUTHORIZED_PHASE2A_PARALLEL_PANEL_RECONSTRUCTION`

`NO_SCIENTIFIC_DESIGN_CHANGE`

The first panel workflow used a single sequential job to replay all nine reserved Phase-1O confirmation seeds twice. Before it produced a panel result, that orchestration was identified as likely to exceed the job timeout because Phase-1O replay is CPU-expensive.

This marker authorizes only an engineering-equivalent parallelization:

- the same nine frozen confirmation seeds;
- the same frozen Phase-1O Arm-A replay code;
- each seed is still replayed twice and must match deterministically;
- the same frozen terminal fingerprints must match seed-by-seed;
- the same classical-only one-per-seed / lexicographic six-candidate selection rule;
- the same independent classical revalidation and panel digest;
- zero neural training.

No seed, cryptographic threshold, candidate-selection rule, neural regime, neural seed, qualification threshold, or evolutionary behavior is changed by this orchestration correction.
