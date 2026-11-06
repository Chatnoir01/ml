# Phase 2R-EP1 — one full first-epoch CPU/BLAS contrast (2026-11-06)

**Prospectively registered before any run; separate DRAFT branch stacked on PR #164.** This is **one epoch of actual SGD/Adam computation on the pinned synthetic Phase 2R fixture**, NOT the original 32-epoch Phase 2G science or the 96 model trainings of Phase 2U.

## Motivation and fixed question

The original single-step comparison (PR #163) recorded 5/6 gradient and 4/6 updated-weight tensors different under a same-host forced OpenBLAS Haswell / Nehalem intervention. The eight-step comparison (PR #164) showed a strictly increasing number of bitwise-different **weights** from **73 to 469 of 1,825** over the first eight original minibatches, but does not establish what happens by the end of **one complete epoch**, including the last smaller minibatch.

**Question:** With exactly the same initial weights, initial random-generator state, fixed 5600-row synthetic training set and its first historical permutation, how many updated weights, momentum/variance scalars, and fixed synthetic test-set predicted probabilities differ after exactly ONE historical epoch (22 batches)? Do the two trained-for-one-epoch models produce the same *synthetic* test AUC and holdout advantage?

This study is **N=1** paired deterministic numerical comparison. The AUC diagnostic is secondary and observational, not a test of a new S-Box or cryptographic claim.

## Preregistered exact computation

- One GitHub Actions job, single Ubuntu 24.04 x86_64 host and **two independent sequential Python processes** (forced `OPENBLAS_CORETYPE=HASWELL`, forced `OPENBLAS_CORETYPE=NEHALEM`). Verify actual `threadpoolctl` reported dynamic-dispatch cores, **one BLAS thread**, same SIMD CPU feature list and same normalized OpenBLAS attributes otherwise.
- Pin **CPython 3.12.14, NumPy 2.5.3, threadpoolctl 3.6.0**; five numerical thread environment limits set to 1 before any process import.
- Reuse the **frozen synthetic Phase 2R 20-S-Box fixture** (`phase2r-synthetic-v1`) and ORIGINAL `build_shared_training_splits`: input difference=1, model replicate=0, original train/validation/test geometry **5600/1200/1200**, original dataset seed **776003** and original model seed **786009**; no real original Phase 2G candidate training evidence or prospective Phase 2U neural outcomes.
- Exactly the original 12→48→24→1 float32 network, model-seeded weight initialization, `np.random.Generator.permutation` **once**, original `_sigmoid`, six historical backpropagation gradients and original `_adam_update` with momentum and variance **carried forward**, original historical batch order and **22** consecutive training updates: **21 batches of 256 and final batch of 224**. No second permutation, no second epoch, no hyperparameter tuning or early stopping. The historical project has 32 full epochs; this is only the first.
- **Mathematical parity gate:** for steps 1–8, recompute all original 32 stage arrays using the independently frozen eight-step source implementation and compare their versioned shape-bound float32 SHA-256s. A divergence rejects this experiment; old PR #164's code remains untouched. After step 8 the new one-epoch implementation uses identical operation ordering and the original `_adam_update`.
- Capture each of **22×32 = 704 stage arrays** (including input/label, first/second matmul and tanh, logits, probs, six gradients, six updated parameters and six first/second moments) **per kernel**. Last-batch 224-row shapes explicitly checked. Two original NPZs carry **1,408** independent versioned stage SHA-256 receipts.
- Capture the **entire first-epoch permutation** SHA256, 22 exact nonoverlapping batch-index SHA256s and identical train/validation/test original split SHAs. For each step independently recompute per-stage binary equality, number of changed float32 values, maximum and weighted mean absolute differences for weights and moments. Strictly check all source JSON receipt SHAs, source commit, expected scope, runtime fingerprint and NPZ correspondence. Zero missing/extra tensors permitted.
- After the **22nd update**, evaluate both models **once** on the *same fixed synthetic* 1200-item test set with the original `_sigmoid(np.tanh(np.tanh(x @ w1 + b1) @ w2 + b2) @ w3+b3)` formula and original tie-aware `_auc_from_scores`, record bitwise probability SHA, number of differing probability float32s, maximum/mean absolute probability difference, each model's test AUC and the exact `2*abs(AUC-.5)` advantage. The *test set is NOT used* in weight updates. Do not select a superior kernel after comparing its score; it is only a numerical stability diagnostic.
- Fixed endpoints: differences in the six updated-weight tensors at step **22**, comparison of number/maximum/mean absolute differences between **steps 1, 8, 22** (no automatic monotonicity inference), probability differences and AUC contrast on that fixed synthetic test panel. No significance tests, no new seeds, no post-hoc outcome threshold.

## Interpretation before outcomes

- Bitwise weight differences at step22 establish that kernel-dependent floating-point effects persisted through the first epoch **on this synthetic N=1 control only**.
- A **changed test probability array with identical AUC** demonstrates that a change in model output bytes need not change rank-based AUC. A **changed AUC** is a functional metric difference on this fixed synthetic test set, not proof of changed real-world cryptographic security or complete historical Phase2G fitness rankings.
- If all stage and prediction bytes match, this sample provides no continued kernel sensitivity at this endpoint.
- If any original input, full permutation, model state, RNG, software or CPU/BLAS attributes (except requested core), or original NPZ receipt is different or unverified, result is **INVALID**; do not claim a controlled contrast.
- Neither result causally attributes the original **64/144** historic trained-state SHA mismatches to BLAS/CPU, because original 2026-09 run CPU/runtime data and exact source tensors are unavailable. No exponential-amplification or worldwide-discovery claim is permitted.

## Safety, time and evidence

This workflow performs **44 bounded mini-batch updates total** across 2 model instances (22 each) on synthetic research data. It is NOT the frozen 32-epoch historical training, not an experiment on Phase2U's 12 sealed candidates, and not any of Phase2U's 96 preregistered neural fits. It is an **explicitly separate scientific stage**, not an edit to earlier frozen documents. Source run original receipt JSONs, both 704-stage NPZ files, test prediction arrays, full numerical audit and SHA256SUMS must be preserved outside ephemeral Actions; GitHub success alone is not a source-verification proof. No merge into main or publication of cryptographic strength claims.
