# Phase 2G — Frozen result

## Status

**FROZEN / VALID NEGATIVE / ADAPTIVE COEVOLUTION NOT SUPPORTED**

Official verdict:

`phase2g_adaptive_coevolution_not_supported`

This is a valid preregistered negative result. It is **not** a provenance failure. The adaptive loop and mechanism gates were active, but the full preregistered support rule failed. No post-result seed, threshold, arm, checkpoint, budget, architecture, endpoint, B1 geometry, or terminal-rule change is authorized by this result.

## Provenance

- preregistration: #118
- execution lock: #119
- pre-marker scientific SHA: `6075576436389d997993b91fb56d921e5c58a2a1`
- scientific marker SHA: `030652489dd489a4705bbf64a12d7e6fa01ca03b`
- official workflow: `Phase 2G Adaptive Coevolution`
- workflow run: `35572084785`
- workflow conclusion: **success**
- terminal-freeze SHA-256: `8c44e05600566781c56e746415f723de022cea0372986f7afcd5175b413f16c2`
- held-out validation SHA-256: `69248626568d856d16f6dcc1ea293d6f16f943c38ca28e8372c0113010323c40`
- aggregate SHA-256: `1df1812bc58e088c6a639d7ccbb94e1f3a02feb0ebd9f8b04e4ac81b1ea983d2`

The exact official aggregate JSON is committed as `research/phase2g-result.json`; compact artifact provenance is committed as `research/phase2g-artifacts.json`.

## Frozen execution geometry

The experiment used exactly the preregistered four arms `C / F / A / S` over nine fresh evolution seeds, for **36 arm/seed cells**.

Per cell:
- 20 generations;
- 340 unique classical evaluations;
- four checkpoints at generations `0, 5, 10, 15`;
- 16 checkpoint neural trainings per checkpoint;
- 64 checkpoint trainings per cell;
- historical classical-only terminal selection.

Totals:
- checkpoint training: `36 × 64 = 2,304`;
- all 36 terminals frozen before H opened;
- held-out H: `36 × 16 = 576`;
- total scientific neural trainings: **2,880**.

## Prerequisite and mechanism activity

Both preregistered activity requirements passed strongly:

- A curriculum differed from initial at later checkpoints on **9/9 seeds**;
- A-vs-F fully eligible B1 score ordering differed on **9/9 seeds**;
- A produced at least one real cross-protected-key score-caused membership change on **9/9 seeds**.

So this result is **not inconclusive for lack of adaptive activity**. The adaptive feedback loop was measurably active.

## Held-out H comparisons

Lower neural advantage is better.

| Quantity | Frozen observation |
| --- | ---: |
| mean A | `0.2844938666599919` |
| mean F | `0.24243693462748478` |
| mean S | `0.31244688754372996` |
| mean C | `0.34902052233013925` |
| A lower than F | `0/9` |
| exact one-sided sign-test A<F | `p = 1.0` |
| mean(F-A) | `-0.04205693203250708` |
| A lower than S | `7/9` |
| A lower than C | `9/9` |

A therefore beat the shuffled control and the classical control on the preregistered held-out comparisons, but **did not beat the fixed-initial-curriculum neural arm F**.

## Classical non-degradation

The A terminal was componentwise no worse than C on **7/9 seeds**.

Passing seeds:
`726023, 726037, 726049, 726061, 726073, 726087, 726113`.

Failing seeds:
`726011, 726099`.

Because the preregistration required classical non-degradation on **all 9 seeds**, this support gate failed.

## Preregistered ten support checks

| Check | Result |
| --- | --- |
| adaptation activity | PASS |
| mechanism activity | PASS |
| A lower than F on ≥8/9 | FAIL |
| exact one-sided sign test A<F p<.05 | FAIL |
| mean(F-A) ≥ .02 | FAIL |
| classical non-degradation all 9 | FAIL |
| A lower than S on ≥6/9 | PASS |
| mean A < mean S | PASS |
| A lower than C on ≥6/9 | PASS |
| mean A < mean C | PASS |

Exactly **6/10** support checks passed. The frozen rule required **all 10**, therefore the official classification is:

`phase2g_adaptive_coevolution_not_supported`

## Narrow interpretation

The experiment established that the adaptive GA↔NN loop was operational and had real causal selection activity. The adaptive arm also outperformed both the shuffled association and the classical control on the held-out neural endpoint. However, the adaptive curriculum did not outperform the fixed-initial-curriculum neural arm and it violated the all-seed classical non-degradation requirement on two seeds.

This does **not** justify post-hoc rescue by changing seeds, thresholds, B1 width, checkpoint timing, model architecture, budgets, endpoints, or terminal selection. Any follow-up mechanism requires a new separately preregistered phase.

Scope remains educational/defensive ToySPN research only. No deployed-cipher/AES claim, operational key recovery, side-channel claim, or production cryptographic-security claim is made.
