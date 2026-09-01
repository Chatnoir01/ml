# Phase 1G development result — annealed escape

## Verdict

**Development negative. Phase 1G confirmation is not executed. Global Gate 1 remains RED and the neural-oracle phase remains blocked.**

The preregistered development stop rule required at least one annealed hard-admissible development success before any reserved confirmation seed could be used. Across all four preregistered configurations and five fresh development seeds per configuration, the annealed arm produced **0/20 hard-admissible runs** and **0/20 structural-target runs**.

The reserved confirmation seeds

`1409, 1423, 1427, 1429, 1433, 1439, 1447, 1451, 1453`

remain **UNUSED**.

## Frozen experiment

- branch: `research/phase1g-annealed-escape`
- frozen experimental SHA: `fcbfc71011dab4c099d04a49b4959960d4941a29`
- workflow run: `33519216715`
- development seeds: `1301, 1303, 1307, 1319, 1321`
- annealed budget: `600` unique full classical evaluations per seed
- strict comparator budget: `600` unique full classical evaluations per seed
- shared proposal: combined DDT+LAT hotspot, permutation-preserving cycle length 4
- historical warm start: exact verified Phase-1B frontier candidate (`NL=98`, `DU=8`, max corr `60`, degree `7`, SAC `0.501708984375`, fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`)

The frozen SHA passed the normal Phase 0 CI on Python 3.10, 3.11 and 3.12.

## Results

| Config | Annealed admissible | Annealed target | Annealed vs strict | Median annealed NL / DU / corr | Accepted off-frontier | Frontier returns | Forced resets |
|---|---:|---:|---:|---|---:|---:|---:|
| `mild` | 0/5 | 0/5 | 0 wins / 4 losses / 1 tie | 98 / 8 / 60 | 120 | 0 | 5 |
| `mid` | 0/5 | 0/5 | 0 wins / 3 losses / 2 ties | 98 / 8 / 60 | 482 | 1 | 15 |
| `wide` | 0/5 | 0/5 | 0 wins / 3 losses / 2 ties | 98 / 8 / 60 | 912 | 0 | 19 |
| `hot_mid` | 0/5 | 0/5 | 0 wins / 4 losses / 1 tie | 98 / 8 / 60 | 1248 | 2 | 19 |

The strict comparator also produced `0/5` hard-admissible and `0/5` structural-target runs in every configuration. Its median structural metrics were also `NL=98 / DU=8 / corr=60`.

Across the annealed configurations there were **2,762 accepted off-frontier states**, only **3 recorded returns to the strict frontier**, and **58 forced resets**. Despite substantially increasing off-frontier exploration, no evaluated candidate reached the structural target (`NL>=100`, `DU<=8`, corr<=64, degree>=6`) or full hard admissibility.

## Artifact receipts

All artifacts belong to workflow run `33519216715` at frozen SHA `fcbfc71011dab4c099d04a49b4959960d4941a29`.

- `mild`: artifact `9805210620`, `sha256:8729311bf7adefd273ce0fce017c93e74f76c560d66c916619413d7a531d182b`
- `mid`: artifact `9805358293`, `sha256:db1e04282b2c8f1547f34f979a100dfd62f8161d7dd0fd93ac14336c40f41a20`
- `wide`: artifact `9805390376`, `sha256:a430a04bb57d1d86d62b3fccf6954a7477c5b490e45447d7a716c74c15cd5bad`
- `hot_mid`: artifact `9805381141`, `sha256:51a958cda09e4afa5072914b787f75bb4dce43464ae3363b4315ab641f2cb6cd`

Artifacts are retained by the workflow for 90 days.

## Scientific interpretation

Phase 1G tested a different mechanism from the earlier strict-frontier searches: temporary structural degradation was explicitly allowed rather than filtered out immediately.

The result is informative. The annealed chains did in fact leave the frontier frequently, so the mechanism was not merely reproducing the strict search. However, those excursions almost never found a useful route back: only 3 frontier returns were recorded across 2,762 accepted off-frontier states, and none returned with an improvement sufficient to cross the `NL=100 / DU<=8` target.

Therefore the observed `NL≈98` plateau is not explained solely by the earlier rule that forbade temporary off-frontier states. Within the tested combined-hotspot cycle-4 neighborhood, bounded simulated-annealing excursions still fail to provide a reproducible bridge to the admissible region.

This does **not** prove that all non-greedy or annealed search is ineffective. It rules out the preregistered Phase-1G mechanism and parameter family at the frozen budget.

## Stop-rule action

The development prerequisite failed exactly as defined in `research/PHASE1G_DEV_PROTOCOL.md`:

- no selected configuration exists for confirmation;
- no confirmation protocol or confirmation workflow is created;
- no Phase-1G confirmation seed is consumed;
- no post-hoc temperature, cap, reset, budget or seed adjustment is performed;
- global Gate 1 remains RED;
- neural-oracle work remains blocked.

A future classical phase must introduce a new preregistered mechanism and new development seeds rather than retune Phase 1G after observing this result.
