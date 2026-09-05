# Phase 1K — ITO-aware Pareto integration protocol

## Status

Engineering/instrumentation phase. This phase does **not** green global Gate 1 and does not enable the neural oracle.

## Goal

Add Improved Transparency Order (ITO) as a genuine multi-objective criterion without changing any historical Phase 1 ranking mode and without collapsing heterogeneous security metrics into an arbitrary weighted scalar.

## Frozen objective directions

The Pareto vector is:

1. nonlinearity — maximize;
2. differential uniformity — minimize;
3. maximum absolute linear correlation — minimize;
4. Improved Transparency Order — minimize;
5. absolute SAC deviation from 0.5 — minimize;
6. algebraic degree — maximize.

Dominance requires no regression on any objective and a strict improvement on at least one objective.

## Selection

Non-dominated sorting plus standard NSGA-II crowding distance is used inside the ITO-evaluated shortlist. Deterministic tie-breaking is required for reproducibility.

## Staged-cost rule

ITO is more expensive than the classical CryptoShield gates. Therefore:

- every unique candidate is evaluated by the unchanged classical evaluator;
- candidates are pre-ranked using the existing frozen `feasibility_first` ordering;
- only the top `shortlist_size` candidates receive ITO evaluation;
- Pareto/NSGA-II parent selection occurs only after ITO evaluation;
- classical and ITO evaluation counts are reported separately.

No historical `constraint_distance` or `feasibility_first` behavior may change.

## Current engineering acceptance criteria

1. red test exists before implementation;
2. objective directions are unit-tested;
3. strict Pareto dominance is unit-tested;
4. non-dominated sorting is unit-tested;
5. NSGA-II selection is deterministic;
6. staged evolution is deterministic at fixed seed;
7. ITO evaluations are strictly fewer than classical evaluations in the staged smoke test;
8. Python 3.10/3.11/3.12 CI remains green;
9. AES ITO reference from Phase 1J remains green;
10. a dedicated CI benchmark records classical-vs-ITO wall-clock cost on the same runner.

## Interpretation boundary

A successful Phase 1K engineering integration means the framework can search with an ITO-aware Pareto objective under controlled cost. It is not evidence that the resulting S-Boxes are superior to AES, more DPA-resistant in hardware, or ready for neural co-evolution.
