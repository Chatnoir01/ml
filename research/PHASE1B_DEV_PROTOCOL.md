# Phase 1B development protocol

This is a development/tuning experiment, not confirmatory evidence.

## Fresh development seeds

`307, 311, 313, 317, 331`

They are registered in `experiment_seeds.py` and are disjoint from every prior
baseline, development, and confirmation seed.

## Shared experiment settings

Every configuration uses:

- population: 12
- generations: 8
- elite count: 2
- tournament size: 3
- crossover rate: 0.0
- offspring multiplier: 3
- ranking mode: `feasibility_first`
- comparison mode: `primary`
- exact unique budget per method/seed: `12 + 8 * 10 * 3 = 252`

The equal-budget random baseline is charged the same 252 unique evaluations.

## Configurations

1. `f1_local1_noimm`: 1 swap, 0% immigrants
2. `f1_local3_noimm`: 3 swaps, 0% immigrants
3. `f1_local5_noimm`: 5 swaps, 0% immigrants
4. `f1_local3_20imm`: 3 swaps, 20% immigrant trials
5. `f1_local3_40imm`: 3 swaps, 40% immigrant trials

## Development selection rule

Select lexicographically by:

1. `admissible_ga - admissible_random`;
2. `admissible_ga`;
3. `primary_ga_wins - primary_random_wins`;
4. median NL margin (`GA - random`);
5. median DU improvement (`random - GA`);
6. median max-linear-correlation improvement (`random - GA`).

If still exactly tied, select the first configuration in the declaration order.

No result from this sweep is sufficient for a Gate-1 claim. A promoted
configuration must use the already-reserved V2 confirmation seeds and a frozen
confirmation protocol.
