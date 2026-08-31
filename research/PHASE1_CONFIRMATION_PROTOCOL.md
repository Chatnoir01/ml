# Phase 1 confirmatory protocol — preregistered

This protocol is committed **before** the confirmatory seeds are evaluated.
It freezes the selected development configuration, confirmatory seeds, comparison
metric, and decision thresholds so the criteria cannot be moved after seeing the
result.

## Frozen configuration

Selected by the already-declared development selection key
`(admissible_margin, primary_win_margin, median_NL_margin, DU_margin, LAT_margin)`.
When multiple configurations tie exactly, the first configuration in the
predeclared tuning order is selected. That rule selects:

- configuration: `local_3swap_x3`
- population size: 10
- generations: 6
- elite count: 2
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- offspring multiplier: 3
- unique evaluations per method/seed: 154

The random baseline receives the exact same number of unique evaluations.

## Fresh confirmatory seeds

These seeds were not used in development or the earlier CI probes:

`211, 223, 227, 229, 233, 239, 241, 251, 257`

No tuning is permitted on these seeds.

## Primary comparison

A per-seed scientific win is determined only by the frozen primary security key:

1. hard admissibility;
2. higher nonlinearity (NL);
3. lower differential uniformity (DU);
4. lower maximum linear correlation;
5. higher algebraic degree.

SAC and aggregate constraint-distance may be recorded but cannot create a
scientific win.

## Statistical test

Use a one-sided exact sign test on non-tied seed pairs under H0: P(GA win)=0.5.
The relative search advantage is confirmed only if all of the following hold:

- exact one-sided sign-test p-value <= 0.05;
- GA primary wins > random primary wins;
- median GA NL >= median random NL;
- median GA DU <= median random DU;
- median GA maximum linear correlation <= median random maximum linear correlation;
- admissible GA count >= admissible random count.

## Full Gate 1 criterion

Full Gate 1 requires the relative-search-advantage criteria above **and** repeated
production of candidates satisfying every hard classical gate:

- at least 3 of the 9 independent GA runs produce an admissible S-Box; and
- the GA produces strictly more admissible S-Boxes than equal-budget random search.

If relative advantage is confirmed but the admissibility-repeat criterion is not,
the result must be reported as **relative advantage confirmed / Gate 1 still open**.
If the sign test or non-regression criteria fail, Gate 1 remains red.

No fitness, operator, seed, budget, or criterion may be changed after the
confirmatory run starts and still count as this confirmation experiment.
