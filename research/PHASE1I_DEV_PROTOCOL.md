# Phase 1I development protocol — accelerated fresh-population VNS batch

## Scope

Phase 1I is the first accelerated **fresh-population** experiment built on the independently confirmed Phase-1H plateau-directed mechanism.

The scientific question is narrow and explicit:

> Which local neighborhood family can reproducibly cross the observed `NL≈98 / DU≈8–10` basin when the run starts from a genuinely fresh population rather than from the historical Phase-1B warm start?

This is a development/selection experiment. It does not use any Phase-1H development or confirmation seed. No neural component is introduced. Global Gate 1 remains RED unless a later independent fresh-population confirmation passes its separately preregistered criteria.

## Seeds

Development seeds, declared before Phase-1I implementation results:

`1709, 1721, 1723, 1733, 1741`

Reserved confirmation seeds, quarantined during development:

`1801, 1811, 1823, 1831, 1847, 1861, 1871, 1873, 1877`

The reserved confirmation seeds MUST NOT be used for development or tuning.

## Shared fresh discovery stage

Every directed configuration starts from a fresh random GA population. No historical S-box, Phase-1B candidate, Phase-1H candidate, or other hand-selected permutation is injected.

The shared discovery GA is frozen to:

- population size: `20`
- elite count: `4`
- tournament size: `3`
- mutation swaps: `3`
- crossover rate: `0.0`
- immigrant fraction: `0.10`
- offspring multiplier: `2`
- ranking: `feasibility_first`
- discovery generations: `13`

With the existing exact accounting formula, discovery consumes exactly:

`20 + 32 * 13 = 436` unique full classical evaluations.

For a given seed, all ten directed configurations use the same deterministic discovery configuration and therefore the same fresh discovery trajectory before their neighborhood stage diverges.

## Shared directed repair stage

After discovery, the directed arm reuses the evaluated discovery cache and initializes a repair archive from the best discovery candidates in a broad bridge region:

- differential uniformity `<= 12`
- max linear correlation `<= 72`
- algebraic degree `>= 6`

If fewer than the archive width satisfy the bridge region, the highest-ranked evaluated discovery candidates fill the remaining slots. No candidate is evaluated twice and cache reuse does not consume extra budget.

The repair archive width is `8`.

Each repair proposal is a permutation-preserving cycle mutation anchored on the current parent’s Phase-1H `ties` LAT/DDT hotspot union.

For each full evaluation, the operator first generates a frozen pool of cheap local proposals. Each proposal is scored by exact local projection on the currently tracked LAT/DDT plateau cells. The projection is not counted as a full classical fitness evaluation.

Dynamic cheap ranking is frozen as follows:

- if the parent has `DDT max > 8`, proposal selection prioritizes lower projected DDT max, then lower projected LAT max;
- otherwise it prioritizes lower projected LAT max, then lower projected DDT max;
- ties then prefer more reduced current-max cells, lower projected plateau sums, and proposal generation order.

After the selected proposal receives a full classical evaluation, it may enter the archive if it remains inside the broad bridge region. Archive ordering uses the existing feasibility/repair ordering: hard admissibility, structural target, structural gate count, nonlinearity, lower DU, lower max correlation, algebraic degree, then SAC proximity only as a final tie-break.

The directed repair stage consumes exactly `544` new unique full classical evaluations.

Therefore every directed arm consumes exactly:

`436 discovery + 544 repair = 980` full classical evaluations.

## Matched comparator

For each development seed, the comparator is the same fresh feasibility-first GA continued without directed repair through `30` generations.

Its exact budget is:

`20 + 32 * 30 = 980` unique full classical evaluations.

Thus every directed/comparator pair is matched at exactly `980` full classical evaluations. Cheap proposal projections are diagnostics and are not fitness evaluations.

## Frozen batch of ten neighborhood configurations

Declaration order is part of the final tie-break and MUST NOT change after the first Phase-1I result is observed.

1. `c2_p96` — cycle lengths `(2,)`, proposal pool `96`
2. `c3_p96` — cycle lengths `(3,)`, proposal pool `96`
3. `c4_p32` — cycle lengths `(4,)`, proposal pool `32`
4. `c4_p96` — cycle lengths `(4,)`, proposal pool `96`
5. `c5_p96` — cycle lengths `(5,)`, proposal pool `96`
6. `c6_p96` — cycle lengths `(6,)`, proposal pool `96`
7. `c8_p96` — cycle lengths `(8,)`, proposal pool `96`
8. `mix234_p96` — cycle lengths `(2, 3, 4)`, proposal pool `96`
9. `mix456_p96` — cycle lengths `(4, 5, 6)`, proposal pool `96`
10. `mix2468_p96` — cycle lengths `(2, 4, 6, 8)`, proposal pool `96`

For mixed configurations, each proposal independently chooses one listed cycle length uniformly with the seeded PRNG. No adaptive retuning based on observed success is allowed during Phase 1I development.

## Target definitions

Structural target:

- nonlinearity `>= 100`
- differential uniformity `<= 8`
- max linear correlation `<= 64`
- algebraic degree `>= 6`

Hard admissibility additionally requires the existing SAC gate.

SAC remains excluded from the primary scientific comparison and is used only for hard admissibility/final tie-breaking as already established by the project.

## Recorded diagnostics

For every directed/comparator pair record at minimum:

- exact full evaluation counts;
- best metrics and fingerprint;
- structural-target success and first evaluation index;
- hard-admissible success and first evaluation index;
- directed/comparator primary outcome;
- directed archive accept count;
- proposal pools generated;
- proposal cycle-length selection counts;
- selected proposals predicted to reduce the current LAT maximum;
- selected proposals predicted to reduce the current DDT maximum;
- duplicate proposal skips and pool shortfalls.

## Frozen development prerequisite

A configuration is eligible for selection only if all are true:

1. it produces hard-admissible candidates on at least `2/5` development seeds;
2. it produces structural-target candidates on at least `2/5` development seeds;
3. its hard-admissible run count is strictly greater than the matched continued-GA comparator count.

If no configuration is eligible, Phase-1I confirmation MUST NOT run. The reserved confirmation seeds remain unused, the negative batch is retained, global Gate 1 remains RED, and neural work remains blocked.

## Frozen selection rule

Among eligible configurations, select exactly one lexicographically by:

1. higher directed hard-admissible run count;
2. higher directed structural-target run count;
3. larger hard-admissible success margin over comparator;
4. larger structural-target success margin over comparator;
5. larger directed wins minus comparator wins on the existing primary/repair rank;
6. higher median directed nonlinearity;
7. lower median directed differential uniformity;
8. lower median directed max linear correlation;
9. lower median first hard-admissible evaluation among successful directed runs;
10. declaration order above.

No alternative configuration may be chosen after observing results.

## Confirmation rule

If one configuration meets the development prerequisite and is selected by the frozen rule, a **separate confirmation protocol must be committed before any reserved Phase-1I confirmation seed is used**.

Only that single selected configuration may enter confirmation. The other nine configurations are retired from confirmation regardless of how close they were.

## Interpretation constraint

A positive Phase-1I development result establishes only a candidate fresh-population neighborhood mechanism. A positive independent Phase-1I confirmation would be the first evidence capable of changing the project’s global Gate-1 status, subject to the separately preregistered confirmation criteria and independent metric verification.
