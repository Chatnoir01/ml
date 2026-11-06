# Phase 2R-E8 — eight consecutive historical Adam steps on one fixed synthetic fixture
**Prospective protocol, registered 2026-11-06 before first execution. Independent DRAFT branch stacked on #163.**

## Research question and negative-result handling

The original one-step Phase 2R-M evidence ([run 42143565464](https://github.com/Chatnoir01/ml/actions/runs/42143565464), source SHA `8b6a3bfdcca68211599237a38b6ebd9988d88ea6`) showed that changing only the OpenBLAS core from Haswell to Nehalem on the same host produced **5/6 bitwise-different backprop gradients and 4/6 changed weight tensors after the first Adam update**. The input, first minibatch, initial weights, Python 3.12.14, NumPy 2.5.3 and common CPU/SIMD/BLAS properties were identical. This is a single-sample numerical backend effect, not the root cause of the **64/144** historical Phase 2G trained model differences.

This **separate** experiment asks: over **exactly the first eight consecutive 256-row mini-batches of the historical first epoch**, under the same intentional kernel intervention, do bitwise numerical differences in gradients, Adam moments and parameter tensors **persist, appear/disappear, or grow in magnitude**?

No modification of the old 2G or one-step 2R-M experiment is allowed. The historical 2G verdict remains `phase2g_adaptive_coevolution_not_supported`.

## Frozen method (cannot adjust after seeing outcomes)

- One GitHub Actions job, one Ubuntu 24.04 host and two separate sequential Python processes with explicit `OPENBLAS_CORETYPE=HASWELL` and `OPENBLAS_CORETYPE=NEHALEM`. Confirm each **actual** selected OpenBLAS core by `threadpoolctl`; check normalized CPU/SIMD and BLAS version properties equality except chosen kernel.
- Exactly original Python **3.12.14**, NumPy **2.5.3**, `threadpoolctl==3.6.0`, five numeric-thread variables fixed to **1** before import. Same checkout commit.
- Use **only** original frozen *synthetic* Phase 2R fixture `phase2r-synthetic-v1` (20 S-Boxes), original Phase 2G shared split builder, input difference 1, replicate 0, T seed **776003**, M seed **786009**, original **5600/1200/1200** train/validation/test geometry and 12→48→24→1 `float32` architecture. No historical original secret samples or prospective Phase 2U labels.
- Initialize original six parameter tensors with the original exact NumPy recipe, record the original wire SHA and pre-permutation RNG-state SHA. Consume **one and only one** original `rng.permutation(5600)`, record full permutation SHA, post-permutation RNG SHA, and choose eight **nonoverlapping consecutive batches** of 256 rows (sample indices `order[0:256]` through `order[1792:2048]`). Assert all **2048** sample indices unique.
- Execute the original Phase 2G training math for precisely **8** batch forward/gradient/Adam updates, with original `WEIGHT_DECAY`, `BYTE_LEARNING_RATE`, exact `_sigmoid`, original `_adam_update` and historical update order across w1, b1, w2, b2, w3, b3. Carry forward each updated parameter, first moment and second moment; **never reset Adam moments between steps**. No second permutation/epoch and no training after step 8.
- At step 1, assert that **all 32 tensors** computed (batch inputs/labels, forward stages, gradients, updated parameters, moments and variances) match the separately frozen `original_first_step_tensors()` mathematical reference, bit for bit, before recording results. This is a hard implementation fidelity gate.
- At each of the 8 steps, preserve original exact 32 float32 tensors (same shapes as the one-step source) under `step_01/<stage>` ... `step_08/<stage>`, with versioned, shape-bound SHA receipts and lossless original NPZ. No held-out model evaluation, AUC, independent new candidate selection, metric-driven hyperparameter tuning or cryptographic security score.
- Independent comparison recomputes **512 original tensor digests** (256 stages × two kernel subprocesses), their original JSON receipt SHA and raw NPZ SHA, matches all eight batch feature and label tensors exactly, requires same full 5600-index permutation SHA, initial-state/RNG SHA and normalized host numerical profile except BLAS core, then calculates per-step: bitwise-different gradients/parameters/Adam moments/variances, changed float32 element counts, **maximum and mean absolute per-value deltas** and which parameters first diverge.
- Exactly **one** CI run per designed revision, no changing seed, batch count, kernel pair or input source after inspection of output; CI and machine artifacts are not durable scientific backup.

## Predeclared interpretation

1. **Different updated weights after step 8:** backend-sensitive parameter differences *persist* to a later point within the **same sampled first epoch**. This does **not** show growth in effect size, unless the recorded per-step absolute difference measurements explicitly support it. Changed SHA hashes alone are insufficient.
2. **All updated weights equal at step 8:** early bitwise differences *converge or disappear* by that checkpoint in this sample, even if gradients or moments differ. No global equivalence claim.
3. **Some weights differ intermittently:** report the exact step sequence, never summarize as monotonic amplification.
4. **Any nonmatching input batches, initial weights/RNG, unexpected CPU/BLAS drift or corrupted stage hashes:** invalid, no scientific result.
5. This is an **N=1 paired backend intervention**, not a statistical comparison across S-Boxes, no power or p-value. The single-stage AUC results and 64/144 original final-model anomaly do not become causally explained by this experiment.

## Safety and evidence

This is **eight genuine Adam minibatch updates** on a synthetic model, not an observation-only test. It is intentionally isolated from PR #161 and the previous #163 first-step result. It is **not a full epoch**, not the original 32-epoch scientific model training, not any of the 96 Phase 2U model trainings, and not an authorization for further training.

The original one-step protocol, historical negative results, original 39 Phase 2G artifacts and PR #161 observation-only code remain intact. Branch/PR stays **DRAFT**, no merge to main. The source run must be archived as original exact ZIP and independently rehashed before any result publication.
