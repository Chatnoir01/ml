# Phase 2R-M — preregistered first-gradient / first-Adam-step kernel intervention
**Registered 2026-11-06, before the first execution of this separately versioned experiment. Status: small exploratory training-microstep, NOT the authorized historical study or the 96-run prospective Phase 2U experiment.**

## Motivating original evidence, kept immutable

The exact-version [controlled first-forward CI experiment, run 42141362148](https://github.com/Chatnoir01/ml/actions/runs/42141362148), used one hosted machine, Python **3.12.14**, NumPy **2.5.3**, the canonical synthetic Phase 2R fixture, and independently forced OpenBLAS **Haswell** and **Nehalem** kernels. It found input features equal, **six of seven subsequent forward stages bitwise different**, with the first difference at the initial matrix multiplication. The max absolute stage differences were on the order of 10^-7. The prior local experiment used different software, so this is the first exact-version controlled forward observation. Source outcome artifact ID **13467469373**.

The old Phase 2G trained checkpoint-zero A/F SHA differences were **64/144** in four seed pairs; the original 2G negative verdict remains `phase2g_adaptive_coevolution_not_supported`. Original historical **initialized weights** and **runtime CPU/BLAS features** were not captured, and none of this demonstrates their cause.

## Separate new, bounded scientific question

Under **one** controlled GitHub host and fixed input bytes/initialized weights, can choosing the OpenBLAS **Haswell** versus **Nehalem** kernel change (a) the first backpropagation gradient, and/or (b) any parameter, momentum or variance after **exactly one Adam update** of the original Phase 2G byte_tanh_mlp?

This is *one* deliberately isolated training microstep, **not** a complete neural training run. It is not the older PR #161 observation-only experiment; the code lives on a separate new branch/PR stacked on #161.

## Frozen source and numeric design

- Exact synthetic Phase 2R 20-S-Box fixture `phase2r-synthetic-v1` and historical `phase2g_shared_model.build_shared_training_splits`, difference **1**, replicate **0**, first checkpoint (20 S-Boxes; 5600/1200/1200 train/validation/test).
- Original model seed **786009**, dataset seed **776003**. Convert training samples with the original `_samples_to_byte_arrays`, 12-dimensional byte feature vector.
- Initialize `w1/b1/w2/b2/w3/b3` using the exact NumPy seeded initialization recipe mirrored by `checkpoint_zero_seeded_initialization`. Record the original initialized-state SHA and pre-permutation NumPy RNG-state SHA.
- **Unlike the earlier forward-only probe**, consume the original historical `rng.permutation(len(x_train))` **once**, select the actual first **256 indices**, `xb=x_train[order[:256]]` and `yb=y_train[order[:256]]`. Record the indices and post-permutation RNG state (no subsequent draws).
- Forward: `h1=tanh(xb@w1+b1)`, `h2=tanh(h1@w2+b2)`, logits `h2@w3+b3`, original `_sigmoid`.
- Compute **exactly the original first-step six gradients** from `phase2g_shared_model._fit_shared_model_state_bytes`, using original `WEIGHT_DECAY`, `BATCH_SIZE` and float32 NumPy behavior.
- Initialize Adam first and second moments with original zero arrays/scalars; perform **one and only one** `_adam_update(..., step=1, learning_rate=BYTE_LEARNING_RATE)` for each of six original parameter tensors. No second minibatch, no second step, no epoch or validation/test scoring. No full training and **zero Phase 2U neural labels**.
- Record exact float32 tensors for input/labels, seven forward intermediate stages (where meaningful), six gradient arrays and 18 post-step parameter/moment/variance arrays, with strict original stage SHAs and separately stored NPZ bytes. Raw initial weights are local test data and not included in receipts; they are deterministic fixture-only.
- New two-process, **same-host** GitHub Actions: Python **3.12.14**, NumPy **2.5.3**, `threadpoolctl==3.6.0`, five numeric thread environment variables `=1`, sequential `OPENBLAS_CORETYPE=HASWELL` and `OPENBLAS_CORETYPE=NEHALEM`. Both kernels must be confirmed using `threadpoolctl`, not assumed from requested environment variables. The only intentional change is OpenBLAS kernel dispatch.
- Same fixed source Git commit, actual CPU SIMD feature list, OpenBLAS version, number of threads, core-agnostic runtime attributes, fixture identity, dataset/model seed, batch selection indices, initialized state and RNG fingerprint must match. Any unrelated runtime drift is a **failed comparability gate**.
- Single workflow job only, with two processes; no seed sweep or post-outcome parameter tuning. Save both original JSON/NPZ receipts, SHA256SUMS and independent per-stage numeric audit. Unit tests must cover corrupted or altered receipts and original historical stage math fidelity.

## Predeclared endpoints and interpretations

**Primary engineering observations (not statistical hypotheses):** first bitwise-different stage among **six gradient tensors**, and first bitwise-different parameter after the **one** Adam update, together with number of changed float32 elements and maximum/mean absolute difference. Raw forward-stage differences are a control to compare to the previous study.

- If the source gradient bits differ, the single-step backprop path is numerically sensitive to this specific controlled kernel intervention on this exact synthetic sample.
- If any post-step parameter, first moment or second moment differs, the original Adam update carries a difference into the state after one update. This is NOT proof that a full 32-epoch model would diverge or that the old 2G A/F cause has been established.
- If all gradients and post-update tensors match, this single batch did not show numerical downstream sensitivity despite the forward-only findings. Do not declare global reproducibility.
- If initial data, minibatch permutation, initialization, software/CPU profile except kernel, selected actual kernel or receipt integrity differs, declare the comparison **invalid**, never fill in missing outputs or silently relabel an experiment.

**No claimed p-value or security outcome.** This single synthetic computational contrast has no population sample size and is not an empirical proof of a cryptographic property. It does not alter the frozen Phase 2G verdict, may not be used to claim a cryptanalysis breakthrough, and cannot authorize the 96-training Phase 2U campaign.

## Storage and protection

The file is a pre-execution methodological record. A green CI is insufficient without source ZIP and independently checked JSON/NPZ hashes. Save original outputs outside ephemeral GitHub Actions before expiry. Do not merge into main, change previous frozen results, release production cryptography, or rewrite this protocol based on results.
