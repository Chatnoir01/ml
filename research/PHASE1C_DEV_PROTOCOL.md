# Phase 1C development protocol — balanced feasibility

This is a development experiment, not confirmatory evidence. It is committed
before the Phase-1C sweep is executed.

## Fresh development seeds

`503, 509, 521, 523, 541`

These seeds were reserved in `experiment_seeds.py` after V2 confirmation and are
disjoint from every earlier baseline, development and confirmation run. V3
confirmation seeds `601, 607, 613, 617, 619, 631, 641, 643, 647` are already
reserved and forbidden to this development sweep.

## Shared settings

Every configuration uses:

- population: 12
- generations: 8
- elite count: 2
- tournament size: 3
- crossover rate: 0.0
- immigrant fraction: 0.0
- offspring multiplier: 3
- search rank: `balanced_feasibility_v1`
- scientific comparison: `balanced_primary_key_v1`
- exact unique evaluation budget per method/seed: `12 + 8 * 10 * 3 = 252`

Equal-budget random search receives the same 252 unique evaluations.

## Configurations

Only mutation radius changes:

1. `balanced_swap1`: 1 swap
2. `balanced_swap2`: 2 swaps
3. `balanced_swap3`: 3 swaps
4. `balanced_swap4`: 4 swaps
5. `balanced_swap5`: 5 swaps

## Development selection rule

Select lexicographically by:

1. `admissible_ga - admissible_random`;
2. `admissible_ga`;
3. `structural_admissible_ga - structural_admissible_random`;
4. `structural_admissible_ga`;
5. `dual_nl_du_gate_ga - dual_nl_du_gate_random`;
6. `dual_nl_du_gate_ga`;
7. `ga_wins - random_wins` under `balanced_primary_key_v1`;
8. median max-structural-violation improvement (`random - GA`);
9. median total-structural-violation improvement (`random - GA`);
10. median NL margin (`GA - random`);
11. median DU improvement (`random - GA`);
12. median max-linear-correlation improvement (`random - GA`).

If still exactly tied, select the first configuration in declaration order.

## Gate discipline

No development result can turn Gate 1 green. A selected configuration must be
frozen and tested once on the already-reserved V3 confirmation seeds under a
separately committed confirmation protocol.
