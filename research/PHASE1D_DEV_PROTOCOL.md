# Phase 1D — verified frontier continuation protocol

Status: **warm-start development only — not global Gate-1 evidence**.

## Question

Phase 1B once produced a candidate with `NL=98`, `DU=8`, maximum linear
correlation `60`, degree `7`. Phase 1C showed that fresh-population search did not
reproduce `DU<=8` in 30 development runs. Phase 1D therefore asks a narrower
operator question: after exactly reproducing that historical Phase-1B candidate,
can adaptive frontier-preserving local search gain the remaining two NL points
without leaving `DU<=8` or weakening the other structural gates?

## Historical receipt gate

Before any continuation result is accepted, the frozen Phase-1B configuration
must reproduce all of:

- seed: `307`
- population: 12
- generations: 8
- elite: 2
- tournament: 3
- swaps: 3
- crossover: 0.0
- immigrants: 0.0
- offspring multiplier: 3
- ranking: `feasibility_first`
- `NL=98`
- `DU=8`
- maximum linear correlation `60`
- algebraic degree `7`
- fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

A mismatch aborts the experiment.

## Seed isolation

Development seeds:

`701, 709, 719, 727, 733`

Reserved confirmation seeds, declared before development results:

`809, 811, 821, 823, 827, 829, 839, 853, 857`

Reserved confirmation seeds cannot be consumed by development.

## Equal-budget comparator

For each development seed, adaptive search and the comparator each evaluate 600
unique candidates. Both begin from the same verified DU=8 historical candidate.

- **Adaptive**: accepted structural-frontier children can become future parents;
  a bounded beam retains the best frontier states.
- **Direct comparator**: every mutation is sampled directly from the original
  historical candidate and never becomes a new parent.

This comparison tests whether adaptive continuation is useful; it is not a
fresh-population GA-vs-random Gate-1 test.

## Preregistered development configurations

1. `beam1_swap1`: beam width 1, one swap
2. `beam4_swap1`: beam width 4, one swap
3. `beam8_swap1`: beam width 8, one swap
4. `beam16_swap1`: beam width 16, one swap
5. `beam8_swap2`: beam width 8, two swaps
6. `beam8_swap3`: beam width 8, three swaps

All use exactly 600 adaptive and 600 direct-comparator evaluations per seed.

## Frozen selection rule

Configurations are ordered by:

1. adaptive hard-admissible runs;
2. adaptive runs finishing with `NL>=100` and `DU<=8`;
3. fewer corresponding direct-comparator successes;
4. adaptive wins over the equal-budget direct comparator;
5. higher median adaptive NL;
6. lower median adaptive DU;
7. lower median adaptive maximum linear correlation;
8. declaration order.

## Development stop rule

If no configuration achieves `NL>=100` with `DU<=8` on any development seed,
Phase 1D confirmation is not executed and the reserved seeds remain unused.

If at least one configuration succeeds, exactly one configuration is selected by
the frozen rule, then a separate confirmation protocol is committed before any
reserved confirmation seed is used.
