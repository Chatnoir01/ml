# Phase 1C — DU-frontier development protocol

Status: **development only — not confirmatory**.

## Scientific objective

Phase 1B reached a development candidate with `NL=98`, `DU=8`, and maximum
linear correlation `60`, but the frozen V2 confirmation found no hard-admissible
candidate. Phase 1C targets the exact remaining frontier: preserve entry into
`DU<=8`, then raise nonlinearity from `98` to `>=100` without sacrificing the
other hard constraints.

The historical ranking functions remain untouched. Phase 1C uses a separate
`du_frontier_v1` ranking implemented in `phase1c.py`.

## Seed isolation

Development seeds:

`503, 509, 521, 523, 541`

Reserved confirmation seeds, declared before any Phase 1C development result is
observed:

`601, 607, 613, 617, 619, 631, 641, 643, 647`

The reserved confirmation seeds must not be used for tuning or development.

## Frozen development search family

Shared parameters:

- population size: 14
- generations: 10
- elite count: 2
- tournament size: 3
- crossover rate: 0.0
- offspring multiplier: 4
- comparison: primary classical security key
- hard constraints unchanged: `NL>=100`, `DU<=8`, max linear correlation `<=64`, degree `>=6`, SAC deviation `<=0.05`

Development configurations:

1. `local1_noimm`: mutation swaps 1, immigrant fraction 0.0
2. `local2_noimm`: mutation swaps 2, immigrant fraction 0.0
3. `local3_noimm`: mutation swaps 3, immigrant fraction 0.0
4. `local5_noimm`: mutation swaps 5, immigrant fraction 0.0
5. `local3_10imm`: mutation swaps 3, immigrant fraction 0.1
6. `local3_20imm`: mutation swaps 3, immigrant fraction 0.2

Each method receives exactly the same number of unique candidate evaluations as
its random-search comparator.

## Development selection rule

Configurations are ordered by the following frozen coordinates, descending unless
stated otherwise:

1. number of fully hard-admissible GA runs;
2. number of GA runs on the near frontier (`DU<=8`, `NL>=98`, linear<=64, degree>=6);
3. number of GA runs with `DU<=8`;
4. median GA nonlinearity;
5. lower median GA differential uniformity;
6. lower median GA maximum linear correlation;
7. primary GA wins over equal-budget random;
8. declaration order as final deterministic tie-break.

A development success does **not** establish Gate 1. After selecting one
configuration, its parameters must be frozen in a separate confirmation protocol
before any reserved confirmation seed is executed.
