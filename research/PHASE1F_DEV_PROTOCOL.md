# Phase 1F — fresh-population guided bridge protocol

Status: **preregistered development only — no Phase-1F run has been executed**.

## Motivation

Phase 1E demonstrated one development-only hard-admissible warm-start hit with
`combined_cycle4` (`NL=100 / DU=8 / corr=56 / degree=7`) but the frozen nine-seed
warm-start confirmation produced `0/9` target and `0/9` hard-admissible successes.
The operator therefore cannot be promoted on warm-start evidence.

Phase 1F changes the scientific question. It does **not** start from the historical
`NL=98 / DU=8` candidate. Instead it asks whether the already-selected Phase-1E
`combined_cycle4` proposal can act as a local repair stage after a fresh-population
feasibility-first evolutionary search.

This is the first experiment in this line that directly tests a bridge from a
fresh random population to the hard-admissible region while retaining an exact
matched-budget random-search control.

## Fresh seeds

Development seeds, declared before execution:

`1103, 1109, 1117, 1123, 1129`

Reserved confirmation seeds, declared before execution:

`1201, 1213, 1217, 1223, 1229, 1231, 1237, 1249, 1259`

The confirmation seeds are forbidden during development. Previously used or
reserved Phase-1B/1C/1D/1E seeds remain quarantined and are not recycled.

## Shared fresh-population discovery configuration

Every Phase-1F memetic arm begins from a newly generated random permutation
population. No historical candidate is injected.

The discovery stage uses the already-versioned feasibility-first GA:

- population size: `20`
- elite count: `4`
- tournament size: `3`
- mutation swaps: `3`
- crossover rate: `0.0`
- immigrant fraction: `0.10`
- offspring multiplier: `2`
- ranking: `feasibility_first`

With these settings, a run with `g` discovery generations consumes exactly:

`20 + g * (20 - 4) * 2 = 20 + 32g`

unique full classical candidate evaluations.

## Guided bridge stage

After discovery, the memetic arm switches to a local bridge stage seeded only by
the best candidate found by that **same fresh-population run**.

The bridge operator is frozen from the Phase-1E selected family:

- guidance: combined DDT + LAT hotspots;
- cycle length: `4`;
- beam width: `8`.

There is no warm-start fingerprint gate in Phase 1F because the start is fresh by
design.

A candidate may become a future repair parent when it satisfies the broad bridge
region:

- differential uniformity `<=10`;
- maximum linear correlation `<=64`;
- algebraic degree `>=6`.

The repair rank is lexicographic and SAC cannot manufacture a structural success:

1. full hard admissibility;
2. structural target (`NL>=100`, `DU<=8`, max correlation `<=64`, degree `>=6`);
3. number of passed structural hard gates;
4. higher nonlinearity;
5. lower differential uniformity;
6. lower maximum linear correlation;
7. higher algebraic degree;
8. smaller SAC deviation from `0.5`.

The repair stage reuses the discovery evaluation cache. A permutation already
fully evaluated during discovery is never charged a second time. The stated
budget therefore counts unique full classical evaluations across the complete
memetic arm.

## Exact total budget

Every arm receives exactly **788 unique full classical evaluations per seed**.

Three preregistered discovery/repair splits are tested:

1. `bridge10_c4`: discovery `10` generations = `340` evaluations, then `448` guided repair evaluations;
2. `bridge13_c4`: discovery `13` generations = `436` evaluations, then `352` guided repair evaluations;
3. `bridge16_c4`: discovery `16` generations = `532` evaluations, then `256` guided repair evaluations.

The cycle operator itself is not retuned in Phase 1F; only the predeclared amount
of budget assigned before/after the bridge is varied.

## Matched controls

Each development seed has two controls, both at exactly `788` evaluations.

### Continued-GA control

The continued-GA arm uses the same fresh population seed and the same GA settings
but runs for `24` generations:

`20 + 24 * 32 = 788` evaluations.

Because it uses the same seed and configuration, its early trajectory is the
natural mechanism control for spending the remaining budget on ordinary
feasibility-first evolution rather than guided repair.

### Random-search control

An independent deterministic random-search seed is derived from the development
seed. It evaluates exactly `788` unique random bijective S-Boxes under the same
classical constraints and feasibility-first ranking.

## Outcomes

A **structural target** requires all primary structural gates:

- `NL>=100`;
- `DU<=8`;
- max linear correlation `<=64`;
- algebraic degree `>=6`.

A **hard-admissible success** additionally requires the unchanged SAC gate
`|SAC-0.5|<=0.05`.

Per seed, the final best memetic candidate is compared separately with the
continued-GA and random-search best candidates using the frozen
`primary_security_key`, which excludes SAC as a source of scientific wins.

## Frozen configuration selection

If development is eligible to continue, configurations are ordered
lexicographically by:

1. memetic hard-admissible runs;
2. hard-admissible margin vs continued GA;
3. hard-admissible margin vs random search;
4. memetic structural-target runs;
5. memetic primary wins minus losses vs continued GA;
6. memetic primary wins minus losses vs random search;
7. higher median memetic nonlinearity;
8. lower median memetic differential uniformity;
9. lower median memetic maximum linear correlation;
10. declaration order.

## Development stop rule

If **no Phase-1F memetic configuration produces a hard-admissible candidate on
any development seed**, Phase 1F confirmation is not executed and all nine
reserved Phase-1F confirmation seeds remain unused.

If at least one memetic configuration produces a hard-admissible candidate,
exactly one configuration is selected by the frozen rule. A separate confirmation
protocol with frozen acceptance criteria must then be committed **before** any
reserved Phase-1F confirmation seed is used.

## Scope

A positive development result is not Gate 1. Even a later positive Phase-1F
confirmation would need to satisfy separately frozen repeated-superiority and
hard-admissibility criteria before global Gate 1 could be reconsidered.

The neural-oracle phase remains blocked while Gate 1 is RED.
