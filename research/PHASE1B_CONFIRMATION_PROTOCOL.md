# Phase 1B V2 confirmation protocol

This protocol is committed **before any V2 confirmation execution**. The
configuration, seeds, comparison mode, ranking mode and pass criteria are frozen.
A failed confirmation remains evidence and must not be reused as tuning data.

## Reserved confirmation seeds

`401, 409, 419, 421, 431, 433, 439, 443, 449`

These seeds were reserved in `experiment_seeds.py` before the Phase 1B
development sweep was observed and are disjoint from all earlier baseline,
development and confirmation seeds.

## Frozen configuration

Selected by the preregistered Phase 1B development rule:

- population: 12
- generations: 8
- elite count: 2
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- immigrant fraction: 0.0
- offspring multiplier: 3
- ranking mode: `feasibility_first`
- comparison mode: `primary`
- exact evaluation budget per method/seed: 252 unique S-Boxes

## Frozen Gate-1 criteria

### Gate 1A — primary search superiority

All conditions must hold:

1. one-sided exact sign-test on non-tied **primary** outcomes has `p < 0.05`;
2. median classical constraint violation is lower for GA than equal-budget random;
3. median NL is not lower for GA;
4. median differential uniformity is not higher for GA;
5. median maximum linear correlation is not higher for GA;
6. at least one of NL, differential uniformity or maximum linear correlation has
   a strict median improvement.

### Gate 1B — repeated hard admissibility

Both conditions must hold:

1. GA produces a fully hard-admissible S-Box in at least **2 of 9** runs;
2. GA produces more admissible runs than equal-budget random search.

The 2-of-9 threshold is fixed here before execution and is approximately the
same repetition fraction as the earlier 3-of-12 Phase-1 confirmation criterion.

### Full Gate 1

`Gate 1A AND Gate 1B`.

A significant sign test alone is insufficient. A single admissible candidate is
also insufficient for full Gate 1.
