# Phase 1G development protocol — annealed escape from the NL=98 frontier

## Scope

Phase 1G is a **warm-start mechanism-development experiment**, not global Gate-1 evidence.

The question is narrow: previous warm-start searches kept only candidates that remained on the structural frontier, which can trap the search near `NL=98 / DU=8 / corr=60`. Phase 1G tests whether allowing **bounded temporary excursions outside the frontier**, with simulated-annealing acceptance and forced resets to the best known frontier state, can cross to a hard-admissible S-box more reproducibly.

No neural component is introduced. Global Gate 1 remains RED unless a later fresh-population confirmation protocol passes.

## Provenance gate

Before accepting any Phase-1G result, the runner must reproduce the exact historical Phase-1B frontier candidate through the existing receipt function and assert:

- nonlinearity: `98`
- differential uniformity: `8`
- max linear correlation: `60`
- algebraic degree: `7`
- SAC: `0.501708984375`
- fingerprint: `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

Any mismatch aborts the experiment.

## Seeds

Development seeds, declared before any Phase-1G result:

`1301, 1303, 1307, 1319, 1321`

Reserved confirmation seeds, quarantined during development:

`1409, 1423, 1427, 1429, 1433, 1439, 1447, 1451, 1453`

The reserved seeds MUST NOT be used in development. If the development prerequisite fails, they remain unused.

## Shared operator and comparator

Both arms begin from the exact verified historical frontier candidate.

The proposal operator is frozen to the Phase-1E operator that previously produced the single development hit:

- guidance: `combined` DDT + LAT hotspot indices
- mutation: permutation-preserving cycle rotation
- cycle length: `4`
- full classical metrics evaluated for every unique candidate

### Strict comparator

The comparator is the existing strict Phase-1E guided adaptive search:

- guidance `combined`
- cycle length `4`
- beam width `8`
- only structural-frontier candidates may enter the adaptive archive
- exact budget: `600` unique full classical evaluations per seed

### Annealed arm

The annealed chain starts from the same verified candidate and uses the same combined/cycle-4 proposal mechanism, but can temporarily accept states outside the strict frontier.

A candidate is eligible for temporary excursion only if all of the following hold:

- algebraic degree `>= 6`
- differential uniformity `<= du_cap`
- max linear correlation `<= corr_cap`

For eligible candidates define the frozen scalar escape score:

`score = NL - 2 * max(0, DU - 8) - 0.25 * max(0, corr - 64)`

Acceptance rule:

- if candidate score is at least current score: accept;
- otherwise accept with probability `exp((candidate_score - current_score) / T)`;
- temperature decays linearly from `T_start` to `T_end` across the 600 full evaluations;
- ineligible candidates are evaluated and charged to the budget but cannot become the current state.

The best strict-frontier candidate seen at any point is retained independently of the current excursion state. After `reset_after` consecutive accepted states without a return to the strict frontier, the current state is reset to that best frontier candidate. This prevents permanent drift while still permitting controlled barrier crossing.

## Frozen development configurations

Declaration order is part of the tie-break.

1. `mild`: `du_cap=10`, `corr_cap=68`, `T_start=1.0`, `T_end=0.05`, `reset_after=24`
2. `mid`: `du_cap=12`, `corr_cap=72`, `T_start=1.5`, `T_end=0.05`, `reset_after=32`
3. `wide`: `du_cap=14`, `corr_cap=80`, `T_start=2.0`, `T_end=0.10`, `reset_after=48`
4. `hot_mid`: `du_cap=12`, `corr_cap=72`, `T_start=3.0`, `T_end=0.10`, `reset_after=64`

For every configuration and seed:

- annealed arm: exactly `600` unique full classical evaluations;
- strict comparator: exactly `600` unique full classical evaluations.

Cheap control-flow operations do not count as extra fitness evaluations. No extra full classical evaluation may be added after observing results.

## Recorded diagnostics

Per run record at minimum:

- best frontier metrics and fingerprint;
- target and hard-admissible success, with first evaluation index;
- number of accepted proposals;
- number of accepted off-frontier proposals;
- number of returns to the strict frontier after an excursion;
- number of forced resets;
- maximum observed DU and max correlation among accepted states;
- final current-state metrics;
- exact evaluation count.

## Target definitions

Structural target:

- `NL >= 100`
- `DU <= 8`
- max linear correlation `<= 64`
- algebraic degree `>= 6`

Hard admissibility additionally requires the existing SAC gate.

## Frozen selection rule

Choose one configuration lexicographically by:

1. annealed hard-admissible runs;
2. annealed structural-target runs;
3. hard-admissible success margin over strict comparator;
4. structural-target success margin over strict comparator;
5. annealed wins minus strict wins on the existing continuation rank;
6. higher median annealed nonlinearity;
7. lower median annealed differential uniformity;
8. lower median annealed max linear correlation;
9. declaration order.

## Development stop rule

**If no annealed configuration produces at least one hard-admissible development success, Phase-1G confirmation MUST NOT be executed.**

In that case:

- all reserved Phase-1G confirmation seeds remain unused;
- the negative result is retained;
- global Gate 1 remains RED;
- neural-oracle work remains blocked.

If one or more configurations produce a hard-admissible success, select exactly one using the frozen rule above. A separate confirmation protocol, including fixed criteria, must then be committed **before** any reserved confirmation seed is used.

## Interpretation constraint

Even a positive Phase-1G warm-start confirmation would establish only that controlled excursions improve the verified frontier continuation mechanism. It would not by itself establish global Gate 1. Fresh-population matched evidence and repeated hard-admissibility would still be required before unblocking the neural-oracle stage.
