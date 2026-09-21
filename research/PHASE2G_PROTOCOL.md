# Phase 2G — Adaptive GA↔NN curriculum feedback loop

Governing preregistration: #118
Execution lock: #119
Base main: `aa0cc1857b30f8175d130c44c19b625dc518dabd`

## Status

PREREGISTERED / NOT EXECUTED.

No real Phase-2G adaptive training, GA feedback execution, or held-out H validation is authorized until the separate execution marker exists.

Required marker, only after all pre-marker gates are GREEN:

`research/PHASE2G_EXECUTE.md`

with exact token:

`AUTHORIZED_PHASE2G_ADAPTIVE_COEVOLUTION_EXPERIMENT`

## Scientific question

Does retraining a shared depth-4 `byte_tanh_mlp` distinguisher from the current GA population at fixed checkpoints produce candidate-specific adaptive pressure that improves blind held-out terminal neural robustness versus a compute-matched fixed-curriculum control, while preserving classical security and outperforming a shuffled adaptive control?

## Arms

Exactly four matched arms:

- `C`: classical evolution. The shared checkpoint model is trained for audit only and its scores cannot alter selection.
- `F`: shared model retrained from scratch at every checkpoint on the seed's exact initial population; scores may act only inside B1.
- `A`: shared model retrained from scratch at every checkpoint on the arm's exact current population; scores may act only inside B1.
- `S`: same adaptive curriculum/training as A, but candidate↔score association is deterministically shuffled inside each eligible B1 band.

No fifth arm, warm start, persistence tag, terminal neural reranking, wider band, global neural ranking, alternate architecture, extra difference, or outcome-driven variant is allowed.

## Classical geometry

Exact historical geometry:

- population 20
- shortlist 8
- parents 4
- proposals per parent 4
- proposals per generation 16
- generations 20
- exactly 340 unique full classical evaluations per arm/seed
- matched initial population per seed
- historical proposal engine
- hard constraints mandatory
- terminal selection classical-only

Protected key remains:

`(admissible, NL, -DU, -max|LAT|, algebraic_degree)`

## Frozen B1 local pressure geometry

The Phase-2F B1 band is unchanged. Relative to the active cutoff reference, a neural crossing is permitted only when all hold:

- same admissibility
- `abs(NL - NL_cutoff) <= 2`
- `abs(DU - DU_cutoff) <= 2`
- `abs(max_abs_LAT - max_abs_LAT_cutoff) <= 2`
- algebraic degree exactly equal

No neural score may cross an outside-band blocker.

## Checkpoint schedule

Exactly before generations:

`(0, 5, 10, 15)`

Curriculum must be frozen before checkpoint training.

- C/A/S curriculum: exact current 20-candidate population.
- F curriculum: exact initial 20-candidate population at every checkpoint.
- canonical curriculum ordering: ascending fingerprint.

No manual candidate replacement, weighting, cross-arm import, or held-out information is permitted.

## Shared checkpoint model

Frozen training geometry per `(arm, evolution seed, checkpoint, difference, replicate)`:

- architecture: `byte_tanh_mlp`
- depth: 4
- differences: `(0x00000001, 0x00000100)`
- 20 curriculum S-boxes
- 400 labeled pairs/S-box
- 200 cipher + 200 random pairs/S-box
- exact global pair count: 8,000
- deterministic per-S-box split: 280 / 60 / 60
- exact global split: 5,600 / 1,200 / 1,200
- 8 paired dataset/model replicates per difference
- exactly 16 model trainings/checkpoint
- initialization from checkpoint model seed
- no warm start or state reuse

Candidate scores between checkpoints are inference-only and use checkpoint-scoped Q seeds. A score is cached by `(arm, evolution seed, checkpoint, fingerprint)` and is the mean neural advantage across the 16 shared models. Lower is better inside B1.

## Evolution seeds

Exact reserved tuple:

`(726011, 726023, 726037, 726049, 726061, 726073, 726087, 726099, 726113)`

Must be centrally registered and disjoint from all prior evolution registries.

## Checkpoint neural seeds

Checkpoint index `c in {0,1,2,3}` maps to generations `0,5,10,15`.

T dataset base:
`(776003, 776017, 776031, 776043, 776059, 776071, 776083, 776097)`

M model base:
`(786009, 786021, 786033, 786047, 786061, 786073, 786087, 786101)`

Q inference dataset base:
`(796003, 796017, 796029, 796043, 796057, 796071, 796083, 796099)`

Checkpoint block is exactly elementwise `base + 1000*c`.

The registry must materialize and validate all 96 T/M/Q values and prove role separation plus disjointness from every prior frozen/executed Phase-2 neural seed.

## Held-out terminal block H

H is inaccessible until all 36 terminals freeze.

Dataset seeds:
`(876003, 876017, 876029, 876043, 876057, 876071, 876083, 876099)`

Model seeds:
`(886007, 886019, 886031, 886043, 886061, 886073, 886091, 886103)`

Terminal H scoring uses the frozen candidate-specific procedure:

- `byte_tanh_mlp`
- depth 4
- both frozen differences
- pair count 8,192
- split 5,734 / 1,228 / 1,230
- 8 paired replicates
- exactly 16 trainings per terminal
- lower mean neural advantage is better

## Exact training budget

Per arm/seed:

- 4 checkpoints × 16 = 64 checkpoint trainings

Across 36 arm/seed cells:

- 2,304 checkpoint trainings

Held-out H:

- 36 × 16 = 576 trainings

Exact total scientific neural trainings:

**2,880**

Inference scoring is not training and must be receipted separately.

## Adaptation-activity prerequisite

Before efficacy interpretation:

1. A checkpoint curriculum at checkpoint 1/2/3 must differ from the seed's initial curriculum on at least 6/9 seeds; and
2. A and F must produce a different candidate-score ordering in at least one fully eligible B1 band on at least 6/9 seeds.

Failure => `phase2g_inconclusive_prerequisites`.

## Mechanism activity

A must produce at least one real cross-protected-key score-caused selected-membership change on at least 6/9 seeds.

This is a support gate, not a provenance prerequisite.

## Classical non-degradation

For all 9 seeds, terminal A must be componentwise no worse than terminal C:

- admissibility / target status
- NL >= C
- DU <= C
- max|LAT| <= C
- algebraic degree >= C

## Frozen support rule

`phase2g_adaptive_coevolution_supported` only if all pass:

1. adaptation-activity prerequisite passes;
2. A mechanism activity on >=6/9 seeds;
3. A held-out H lower than F on >=8/9 seeds;
4. one-sided exact paired sign test A < F has `p < 0.05`;
5. mean paired reduction `mean(F - A) >= 0.02`;
6. classical non-degradation A vs C on all 9 seeds;
7. A lower than S on >=6/9 seeds;
8. mean A < mean S;
9. A lower than C on >=6/9 seeds;
10. mean A < mean C.

If prerequisites are valid but any support condition 2-10 fails:

`phase2g_adaptive_coevolution_not_supported`

Any seed/budget/checkpoint/curriculum/model/receipt/blindness/determinism/B1/adaptation-prerequisite failure:

`phase2g_inconclusive_prerequisites`

## RED-first / execution separation

Implementation begins with failing contracts for missing Phase-2G functionality. Only implementation defects may be repaired after RED.

Before marker:

- Python 3.10/3.11/3.12 Phase 0 GREEN
- historical Phase 1 Benchmark GREEN
- all Phase-2G tests GREEN
- full seed registry GREEN
- H blindness GREEN
- exact budget and deterministic aggregate tests GREEN
- frozen previous result payloads unchanged
- exact pre-marker SHA recorded
- marker absent

No scientific threshold, seed, checkpoint, curriculum rule, architecture, B1 width, arm, endpoint, or budget may be changed in response to Phase-2G outputs.

Scope remains educational/defensive ToySPN only.
