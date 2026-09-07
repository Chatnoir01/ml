# Phase 2D — Frozen result

## Status

**FROZEN / VALID NEGATIVE / BOUNDED PERSISTENCE NOT SUPPORTED**

Official verdict:

`phase2d_bounded_persistence_not_supported`

This is a valid preregistered negative result. It is **not** a provenance failure and it does not justify post-result threshold, seed, arm, budget or persistence-rule changes.

## Provenance

- preregistration: #109
- execution lock: #110
- scientific marker commit: `2cc913e33cc5848f12ae5493f992b49fa89bc3d2`
- official workflow: `Phase 2D Bounded Persistence`
- workflow run: `34147455097`
- workflow conclusion: `success`
- aggregate payload SHA-256: `51f41197482c5695ed00267c69dfc81b937cf12871336457308755f8e5e64e5c`
- aggregate artifact ID: `10028618629`
- aggregate artifact ZIP SHA-256: `9fdf4db86a2f9b4cf71e6e90d824f293b045ea8ee3a8de1a756fff6a7049fa12`
- terminal-freeze artifact ID: `10028581841`
- terminal-freeze artifact ZIP SHA-256: `dcd5ff8bb46bc44504ca2906ab2156c5d7a84445415ed19b6ccbcaa15ad94f38`
- terminal-freeze payload SHA-256: `8b50e71ab8fc082d1c49fa9b7da0e896c3ecf0f851a82500617bc34927799107`

The exact official aggregate JSON is committed as `research/phase2d-result.json`; compact artifact provenance is committed as `research/phase2d-artifacts.json`.

## Frozen execution geometry

The experiment used exactly the preregistered four arms `C / O0 / OP1 / SP1` over nine fresh evolution seeds, for 36 arm/seed cells.

Each cell used:

- 340 classical evaluations;
- 32 Fitness-Block-F candidate scores;
- 16 neural trainings per candidate score;
- 512 Fitness-Block-F neural trainings per cell.

Totals:

- Fitness Block F: `36 × 512 = 18,432` neural trainings;
- all 36 terminals were frozen before Block W opened;
- held-out Block W: `36 × 16 = 576` neural trainings;
- total scientific neural trainings: `19,008`.

## Prerequisites

Every aggregate prerequisite passed:

- terminal freeze: **PASS**
- validation seed gate: **PASS**
- validation receipt integrity: **PASS**
- validation ↔ terminal-freeze identity: **PASS**
- terminal ↔ validation identity: **PASS**
- held-out scores finite: **PASS**

Classical non-degradation was also **true** for all nine matched seeds.

## Preregistered support gates

Phase 2D required **all seven** gates. Only two passed.

| Gate | Result | Frozen observation |
| --- | --- | --- |
| OP1 +2 transmission > O0 on ≥6/9 seeds | FAIL | `2/9` |
| OP1 lower Block-W endpoint than O0 on ≥8/9 seeds | FAIL | `2 wins / 0 losses / 7 ties` |
| one-sided exact paired sign test `p < 0.05` | FAIL | `p = 0.25` |
| `mean(O0 - OP1) >= 0.02` | FAIL | `0.008002695027341602` |
| classical non-degradation on all 9 seeds | PASS | `true` |
| OP1 lower Block-W endpoint than SP1 on ≥6/9 seeds | FAIL | `5/9` |
| mean OP1 Block-W endpoint < mean SP1 | PASS | `0.3417081210 < 0.3421469064` |

## Mechanism transmission

Frozen +2 descendant-persistence rates:

- O0: `[0.5, 0.09090909090909091, 0.0, 0.125, 0.0, 0.3333333333333333, 0.0, 0.2222222222222222, 0.0]`
- OP1: `[0.5, 0.1111111111111111, 0.0, 0.125, 0.0, 0.3333333333333333, 0.0, 0.2857142857142857, 0.0]`

## Final merge gates

- Phase-0 CI run `34149030750`: Python 3.10 / 3.11 / 3.12 all **PASS** on result-freeze commit `fd36ce2f098ce827afb3e5b7e848f167dd058492`.
- Historical Phase-1 benchmark run `34149030746`: **PASS** on the same result-freeze commit.

No post-result retuning, threshold relaxation, seed replacement, longer persistence, extra arm, or adaptive GA↔NN mechanism is included.