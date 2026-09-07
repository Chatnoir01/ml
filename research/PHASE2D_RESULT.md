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

OP1 exceeded O0 on only two of nine seeds. Therefore the bounded one-generation tag did not meet the preregistered mechanism-transmission criterion.

## Held-out OP1 versus O0

The paired held-out result was:

- wins: `2`
- losses: `0`
- ties: `7`
- exact one-sided sign-test p-value: `0.25`
- mean reduction `O0 - OP1`: `0.008002695027341602`

Per-seed reductions:

`[0.0, 0.07202408956310657, 0.0, 0.0, 0.0, 1.6568296784535974e-07, 0.0, 0.0, 0.0]`

The observed direction is not enough to satisfy the preregistered magnitude, frequency or significance gates.

## Specificity against shuffled persistence

For OP1 versus SP1:

- OP1 wins: `5/9`, below the required `6/9`;
- mean OP1: `0.3417081210235471`;
- mean SP1: `0.34214690638746104`.

The mean-direction gate passed, but the paired specificity gate did not. Thus the data do not support claiming that the bounded Oracle persistence mechanism is specifically better than the matched shuffled persistence control under the preregistered rule.

## Interpretation

Phase 2C-B established that Oracle ordering could cause real but short-lived membership perturbations. Phase 2D tested one narrowly defined response to that diagnosis: a one-generation persistence tag constrained to exact equality of the protected classical key.

That mechanism preserved classical non-degradation, but it did **not** satisfy the preregistered transmission, held-out efficacy, statistical-significance, effect-size or paired specificity requirements. Therefore this exact bounded-persistence coupling is not supported by Phase 2D.

This result does **not** imply that the Neural Oracle is universally useless, and it does not invalidate Phase 2B or Phase 2C. It only rejects support for this specific preregistered one-generation persistence mechanism under this frozen ToySPN experiment.

No AES, deployed-cipher, operational key-recovery or adaptive attack claim is made.

## Governance after freeze

No outcome-driven rerun, threshold relaxation, seed replacement, longer persistence duration or alternate mechanism may be folded into Phase 2D.

Any successor must be separately preregistered from this frozen negative result. Full adaptive bidirectional GA↔NN co-evolution remains outside Phase 2D and must not be inferred from these data.
