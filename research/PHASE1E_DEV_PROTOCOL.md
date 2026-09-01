# Phase 1E — hotspot-guided permutation operator protocol

Status: **warm-start operator development only — not global Gate-1 evidence**.

## Question

Phase 1D preserved the verified `NL=98 / DU=8 / corr=60 / degree=7` frontier but no beam/swap configuration reached `NL>=100` at `DU<=8`. Phase 1E changes the proposal operator itself: mutations must touch input positions implicated in current DDT or LAT worst-case hotspots, rather than choosing all mutation positions uniformly.

## Frozen start gate

Every run starts from the exact Phase-1B candidate reproduced by `reproduce_phase1b_frontier_candidate()` and must match fingerprint:

`d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

with `NL=98`, `DU=8`, max correlation `60`, degree `7`.

## Seed isolation

Development seeds: `907, 911, 919, 929, 937`.

Reserved confirmation seeds: `1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051`.

All are registered centrally before execution. Confirmation seeds cannot be consumed by development.

## Equal-budget comparison

Each side evaluates exactly 600 unique candidates per seed and uses beam width 8.

- **Guided adaptive search:** every cycle mutation has at least one anchor selected from the current parent's declared hotspot set.
- **Unguided adaptive comparator:** same adaptive beam logic and same cycle length, but all mutation positions are uniform random choices.

Both sides preserve only structural-frontier states (`DU<=8`, max correlation `<=64`, degree `>=6`) in their beam. This isolates the proposal guidance effect rather than comparing adaptive search to a weaker non-adaptive baseline.

## Hotspot definitions

- **DDT:** input indices participating in a non-zero-input DDT cell attaining the current maximum differential count.
- **LAT:** input indices whose signed contribution supports a non-trivial LAT cell attaining the current maximum absolute correlation.
- **combined:** union of DDT and LAT hotspot indices.

If a hotspot set is empty, the proposal falls back to uniform mutation and records the fallback.

## Preregistered configurations

1. `ddt_cycle2`
2. `ddt_cycle3`
3. `lat_cycle2`
4. `lat_cycle3`
5. `combined_cycle3`
6. `combined_cycle4`

## Frozen selection rule

Configurations are ordered by:

1. guided runs finishing with `NL>=100` and `DU<=8`;
2. fewer corresponding unguided successes;
3. guided hard-admissible runs;
4. fewer corresponding unguided admissible runs;
5. guided wins over unguided by the frozen continuation rank;
6. higher median guided NL;
7. lower median guided DU;
8. lower median guided maximum correlation;
9. declaration order.

## Development stop rule

If no guided configuration reaches `NL>=100` with `DU<=8` on any development seed, no Phase-1E confirmation is executed and all reserved confirmation seeds remain unused.

If at least one guided configuration succeeds, exactly one configuration is selected by the frozen rule and a separate confirmation protocol must be committed before any reserved seed is used.

Global Gate 1 remains RED regardless of a Phase-1E development result because this is a warm-start operator experiment, not a fresh-population GA-vs-random confirmation.
