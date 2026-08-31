# Phase 1C V3 confirmation protocol

This protocol is committed **before any Phase-1C confirmation execution**. The
configuration, seeds and pass criteria below are frozen. A failed confirmation
remains evidence and must never be recycled as tuning data.

## Reserved confirmation seeds

`601, 607, 613, 617, 619, 631, 641, 643, 647`

These seeds were reserved in `experiment_seeds.py` before the Phase-1C
development sweep and were never consumed by development.

## Frozen configuration

Selected by the preregistered Phase-1C development rule:

- population: 12
- generations: 8
- elite count: 2
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- immigrant fraction: 0.0
- offspring multiplier: 3
- search rank: `balanced_feasibility_v1`
- scientific comparison: `balanced_primary_key_v1`
- exact evaluation budget per method/seed: 252 unique S-Boxes

## Frozen Gate-1 criteria

### Gate 1A — balanced structural search superiority

All conditions must hold:

1. one-sided exact sign-test on non-tied balanced-primary outcomes has `p < 0.05`;
2. median maximum normalized structural violation is lower for GA than random;
3. median total normalized structural violation is lower for GA than random;
4. median NL is not lower for GA;
5. median differential uniformity is not higher for GA;
6. median maximum linear correlation is not higher for GA;
7. at least one of NL, DU or maximum linear correlation has a strict median improvement.

### Gate 1B — repeated hard admissibility

Both conditions must hold:

1. GA produces a fully hard-admissible S-Box in at least **2 of 9** runs;
2. GA produces more admissible runs than equal-budget random search.

### Diagnostic sub-gate — simultaneous NL/DU region

Record, but do not substitute for Gate 1B:

- number of runs with `NL>=100` and `DU<=8` for GA and random.

### Full Gate 1

`Gate 1A AND Gate 1B`.

Statistical superiority alone is insufficient. Entering the simultaneous NL/DU
region alone is also insufficient for full Gate 1.
