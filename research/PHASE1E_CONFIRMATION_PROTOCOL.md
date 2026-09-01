# Phase 1E — frozen hotspot-guided confirmation protocol

Status: **preregistered before any Phase-1E confirmation seed is used**.

## Frozen configuration

Exactly the development-selected configuration is confirmed without retuning:

- guidance: `combined`
- cycle length: `4`
- beam width: `8`
- evaluations per side per seed: `600`
- verified warm start fingerprint: `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

Guided and unguided sides use the same adaptive frontier-preserving beam logic. The only experimental difference is hotspot anchoring of the guided cycle proposal.

## Frozen confirmation seeds

`1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051`

These seeds were registered and reserved before the Phase-1E development run.

## Per-seed outcome

For each seed, the guided and unguided best candidates are compared using the already-frozen Phase-1D continuation rank. Ties remain ties.

A target success means a run finds a candidate with `NL>=100` and `DU<=8` within its 600 unique evaluations.

A hard-admissible success means the run finds a candidate satisfying all current hard constraints:

- `NL>=100`
- `DU<=8`
- max linear correlation `<=64`
- algebraic degree `>=6`
- `|SAC-0.5|<=0.05`

## Statistical test

Use an exact one-sided sign test on non-tied per-seed continuation-rank outcomes under `p=0.5`.

`p = P[X >= guided_wins | X ~ Binomial(guided_wins + unguided_wins, 0.5)]`.

The rank-superiority condition passes only if:

- guided wins > unguided wins; and
- exact one-sided `p <= 0.05`.

## Frozen narrow-confirmation criteria

Phase 1E warm-start operator confirmation is GREEN only if **all** conditions hold:

1. provenance gate reproduces the exact historical start fingerprint and metrics;
2. guided target successes are at least `3/9`;
3. guided target successes are strictly greater than unguided target successes;
4. guided hard-admissible successes are at least `3/9`;
5. guided hard-admissible successes are strictly greater than unguided hard-admissible successes;
6. rank-superiority sign test passes (`p<=0.05` and guided wins > unguided wins);
7. median guided nonlinearity is not lower than unguided;
8. median guided DU is not higher than unguided;
9. median guided maximum linear correlation is not higher than unguided.

Any failed criterion makes Phase 1E confirmation RED. Negative results are retained without post-hoc threshold changes.

## Scope of any positive result

Even a GREEN Phase-1E confirmation proves only that the hotspot-guided `combined_cycle4` operator repeatedly improves the verified warm-start frontier under this toy/research setup. It does **not** make global Gate 1 green and does not unlock the neural oracle by itself.

Global Gate 1 still requires a separately preregistered fresh-population GA-vs-equal-budget-random confirmation with repeated hard-admissible candidates.
