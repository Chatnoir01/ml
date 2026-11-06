# Phase 2R-M — first historical gradient / Adam update under controlled BLAS dispatch
**Original CI result and independent artifact re-audit, 2026-11-06. Exploratory synthetic observation, not an explanation of the old Phase 2G effect.**

## Source provenance

- Prospectively frozen separate [microstep protocol](PHASE2R_FIRST_ADAM_STEP_PROTOCOL_20261106.md) created **before execution**. This is on [DRAFT PR #163](https://github.com/Chatnoir01/ml/pull/163), separately stacked on #161 (which remains no-training-only).
- **Original source run:** [GitHub Actions 42143565464](https://github.com/Chatnoir01/ml/actions/runs/42143565464), single hosted CI job, successful specialized 8-test lane and full planned two-process numeric experiment.
- **Exact source checkout SHA:** `8b6a3bfdcca68211599237a38b6ebd9988d88ea6`; source artifact **13469695857**, complete original GitHub ZIP **358,254 bytes**, SHA-256 `c29be0f3a4b8f8a0ca4917246999999c49982ceed00cdf160756ef775a1dd15c`. Original artifact preserves the source Haswell/Nehalem JSON and exact float32 NPZ, independent result JSON and SOURCE_SHA256SUMS.
- **Independent re-audit:** all original ZIP CRC checks, **5/5** embedded SHA256SUMS references, original **3/3** JSON content digests, **64/64** original per-stage SHA256 checks (32 stages × 2 actual kernels) and **32/32** independently calculated numeric summaries were verified. The separate audit JSON file is preserved as `phase2r_first_adam_step_independent_reaudit_20261106.json` in the current conversation. The GitHub Actions artifact and the conversation copy are NOT a user-owned durable external archive.
- Actual versions **Python 3.12.14 / NumPy 2.5.3**, identical per-host normalized CPU/BLAS profile except the deliberately selected **Haswell** and **Nehalem** OpenBLAS dynamic kernels, one numerical BLAS thread.

## Scope and exact input identity

The original historical Phase 2G `byte_tanh_mlp` source was transcribed **only through its first gradient and Adam update**. The earlier study's first 256 samples in static source order are NOT reused. The new protocol consumes the original seeded **first training permutation** over the frozen synthetic 20-S-Box Phase 2R fixture, difference=1, replicate=0, dataset seed `776003`, model seed `786009`, original 5600 train rows, and identical initial 12→48→24→1 float32 network weights.

- The **source sample indices**, batch features, batch labels, initial-state fingerprint, pre-permutation RNG fingerprint and post-permutation RNG fingerprint are identical between the two kernel subprocesses.
- **Exactly one** first 256-item batch, **six original gradients** and **one first Adam update of each of six model parameter arrays**. There is no second minibatch, epoch or complete fit. Zero Phase 2U neural experiments.
- No original historical Phase 2G trained-state bytes, original 2026-09 CPU hardware identities or prospective 2U held-out labels are available to this protocol.

## Independently confirmed result

| Parameter | Gradient float32 elements differing | Largest absolute gradient delta | Parameter float32 elements differing **after first Adam update** | Largest absolute updated-parameter delta |
|---|---:|---:|---:|---:|
| w1 | 509/576 | 2.7939677238464355e-9 | 6/576 | 1.862645149230957e-9 |
| b1 | 33/48 | 2.7939677238464355e-9 | 15/48 | 4.656612873077393e-10 |
| w2 | 1007/1152 | 7.450580596923828e-9 | 49/1152 | 7.450580596923828e-9 |
| b2 | 14/24 | 5.587935447692871e-9 | 3/24 | 4.656612873077393e-10 |
| w3 | 23/24 | 9.313225746154785e-9 | **0/24** | 0 |
| b3 | **0/1** | 0 | **0/1** | 0 |
| **Tensor-level totals** | **5 of 6 gradients differ** | max **9.313225746154785e-9** | **4 of 6 parameter tensors differ** | max **7.450580596923828e-9** |

First observed different gradient: **`grad_w1`**. First updated state difference: **`updated_w1`**.

The Adam first-moment and second-moment receipts also exhibit differences in **5 of 6** corresponding tensors each. This is a direct measured **one-microstep propagation** of floating point kernel sensitivity into the optimizer and some model weights. Original data, batch identity and initial model were identical.

**Nuance:** some gradients change without a corresponding bitwise change in the updated parameter after just one step (e.g. w3). This is consistent with the numerical rounding and the nonlinear Adam normalization in this tested implementation; it is not proof that those parameters will remain identical after later steps.

## Methodological correction and CI limitation

The specialized one-job experiment succeeded. The ordinary general `Phase 0 CI` on the first head failed test collection under Python 3.11 because **NumPy is an optional dependency** absent from that lane, while two new synthetic test files imported NumPy unconditionally. That is a test packaging defect, **not a failure of the original numerical microstep**.

The affected tests were subsequently changed to use `pytest.importorskip("numpy")`, in both the parent observation-only branch and the microstep branch. Their replacement general CI results require independent confirmation; do not call the full CI green until its latest run completes.

## Interpretation boundary

**We can now state narrowly:** with one controlled CPU host, fixed synthetic Phase 2R data/weights, historical Python/NumPy versions and only OpenBLAS dispatch altered, at least one gradient and at least one updated weight tensor differ in their original float32 byte representation after a single first training step.

**We cannot state:** that the historical **64/144** trained checkpoint-zero hash discrepancies were caused by OpenBLAS; that this behavior persists or amplifies under the full 32-epoch historical training, has any specific effect on AUC, explains the negative adaptive coevolution result, qualifies as world-first mathematical discovery, or improves real cryptographic security.

The original frozen Phase 2G verdict remains `phase2g_adaptive_coevolution_not_supported`. PR #163 remains DRAFT and unmerged. Main and Phase 2U are unchanged.
