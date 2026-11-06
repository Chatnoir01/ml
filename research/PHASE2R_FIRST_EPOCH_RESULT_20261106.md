# Phase 2R-EP1 — original one-epoch evidence verified; predicted ranks unchanged (2026-11-06)

**Frozen design executed once, source artifacts independently re-audited. A synthetic first-epoch computational result, NOT original Phase 2G historical science, a Phase 2U run, or a new cryptographic security claim.**

## Preregistered source and exact original evidence

- Protocol fixed before any run: [PHASE2R_FIRST_EPOCH_NUMERICAL_PROTOCOL_20261106.md](PHASE2R_FIRST_EPOCH_NUMERICAL_PROTOCOL_20261106.md).
- **Original successful CI:** [GitHub Actions run 42156027912](https://github.com/Chatnoir01/ml/actions/runs/42156027912); all specialized unit controls passed. Concurrent Phase 0 general CI **all three Python versions successful** and Phase 1 benchmark successful at the time of independent examination.
- Actual checked-out source revision **`78969d76d77d9545867795dde0d507b8d957e80c`**; source GitHub artifact **`13475002659`**. Its six unchanged source files (two original receipt JSONs, two original full float32 NPZ arrays, an original 22-step comparison report and original SHA256SUMS) were downloaded together as `phase2r_first_epoch_original_github_20261106.zip`.
- **Original ZIP SHA-256 `46f7f9274f86ca7c61d09e3c212b48d8da784b12f55aa5fa18d38cd007f1f9f4`**. ZIP CRC passes.
- Independent read-only auditor verified **5/5** original SOURCE_SHA256SUMS references, **3/3** canonical receipt/report SHA-256 values, and all **1,412/1,412** shape-and-dtype-bound float32 source stage digests including zero-dimensional `b3` tensors. Independently recalculated all **22** per-step gradient, updated weight, moment and variance summaries; recomputed both tie-aware synthetic test AUC values from the saved original 1,200-row probability arrays.
- **Auditor implementation note:** first audit pass correctly rejected a bug in the *external verifier's* serializer: `np.ascontiguousarray` promotes zero-dimensional `float32` arrays to shape `(1,)`, affecting a versioned shape header. The verifier was corrected to preserve the original shape **before** making bytes contiguous. Re-running independently then verified **1,412/1,412** original digests. No original experiment/source artifact was modified to make this pass. Corrected external script SHA-256 `8b86eae0e02ceca67083bc63ec85b9a7f6ce33b04de5c8a878b723ef47679c1d`.

## Controlled environment and exact operation scope

Two sequential Python processes on the **same GitHub-hosted machine**, identical normalized CPU/SIMD and BLAS properties except deliberate OpenBLAS core **Haswell** versus **Nehalem**. CPython **3.12.14**, NumPy **2.5.3**, one OpenBLAS thread. Same frozen synthetic 20-S-Box Phase 2R fixture, exact split byte fingerprints, model seed **786009**, dataset seed **776003**, initialized weights and original 5600-index first-epoch permutation. The first eight step results were automatically checked against the earlier frozen eight-step numerical implementation.

**22/22 original first-epoch Adam minibatches** were performed **per kernel** (21×256, then 224 examples), **5,600 synthetic training examples** per model. Historical Phase 2G uses 32 epochs; no second epoch or historic full fit was executed. **Zero Phase 2U neural trainings**.

## Exact observed parameter divergence

| Adam step | Bitwise-different updated weight elements / 1,825 | Maximum abs weight difference | Mean abs weight difference |
|---:|---:|---:|---:|
| 1 | 73 | 7.450580596923828e-9 | 4.5162765947106766e-11 |
| 4 | 330 | 5.960464477539063e-8 | 9.423900038412172e-10 |
| 8 | 469 | 5.960464477539063e-8 | 1.7196616183405053e-9 |
| 12 | 576 | 5.960464477539063e-8 | 2.5284132116461452e-9 |
| 16 | 674 | 1.1920928955078125e-7 | 3.3971426166491966e-9 |
| 20 | 747 | 1.1920928955078125e-7 | 4.082860756818563e-9 |
| **22** | **771** | **1.1920928955078125e-7** | **4.316233608820667e-9** |

Across all 22 steps the bitwise-different parameter count rises **strictly at each measured checkpoint**, from 73/1825 (**4.0%**) to 771/1825 (**42.25%**). The weighted mean absolute parameter difference rises strictly over all 22 checkpoints. The maximum absolute difference is not strictly monotonic, and remains at an extremely small floating-point scale. **No exponential or indefinitely growing instability is established.**

## Preregistered fixed synthetic test outcome (1,200 examples)

- Both original receipts' tie-aware AUC **`0.6318184389140271`**; absolute signed AUC difference **0.0**, identical neural advantage **`0.26363687782805423`**.
- Exactly **259 of 1,200** probability `float32` bit patterns differ, max absolute probability difference **`1.1920928955078125e-7`**, mean absolute probability difference **`1.1300047238667806e-8`**.
- **Additional post-hoc exploratory rank analysis, not a preregistered endpoint:** the changed probabilities differ by **1–4 ULP** (units in last place) and among all **719,400 unordered pairs** of test examples there are **zero** rank-order reversals **and zero changes of tie relations**. At threshold 0.5, **zero** classification flips (both mark 713 positive, same test accuracy 0.5608333333333333). This stronger result was derived from original unchanged source NPZ and *must be labeled post-hoc*, not silently promoted to the original primary test.
- Both source AUC values were independently recomputed from exact original saved probabilities and labels. No historic Phase 2G score, original candidate ranking, or any Phase 2U neural outcome was accessed.

## Interpretation and remaining blockers

**Observed:** the controlled dynamic BLAS kernel change is sufficient for 771/1825 updated weight elements to differ bitwise after one synthetic first epoch, while these particular two models preserve test-prediction order and AUC exactly. Their parameter bytes differ more widely than their output ordering. This is an engineering reproducibility / finite-precision sensitivity result, not proof of any new cryptographic primitive.

**Not established:** that OpenBLAS explains the original historical 64/144 trained checkpoint-zero hashes, since original 2026-09 CPU/BLAS profiles, actual untrained model bytes and input-array hashes were not preserved. Nor has an entire 32-epoch training run, an S-Box fitness ranking experiment, a blind Phase 2U evaluation, or broad replicability across seeds been performed.

The original frozen scientific verdict remains **`phase2g_adaptive_coevolution_not_supported`**. This PR #165 stays **DRAFT**, stacked on #164; no merge to `main`, no 96-run prospective Phase 2U experiment.

## Original artifact and external checksums

- `phase2r_first_epoch_original_github_20261106.zip`: SHA256 `46f7f9274f86ca7c61d09e3c212b48d8da784b12f55aa5fa18d38cd007f1f9f4`.
- `phase2r_first_epoch_independent_verifier_20261106.py` (fixed scalar serializer): SHA256 `8b86eae0e02ceca67083bc63ec85b9a7f6ce33b04de5c8a878b723ef47679c1d`.
- `phase2r_first_epoch_independent_audit_20261106.json`: SHA256 `10e3b9ce69eddd27ccb63952ef34e70e4adb1de32015d466267b3a52bad26930`.
- Separate post-hoc analysis script and report are packed with the downloadable evidence bundle. The user must preserve that bundle in independently durable storage; conversation files and Actions artifacts are not a verified independent archive.


## Complete exported conversation evidence package

- Package: `phase2r_first_epoch_complete_verified_evidence_20261106.zip`
- Exact archive size **7,739,268 bytes**; SHA-256 **`9af82bdaa0474af1cfc4cd64ca38312c61a080290518c5fbc9fed5de797488c7`**.
- Inside are the unchanged original GitHub source ZIP, corrected independent full verifier, its machine-readable 22-step audit, separate post-hoc prediction-rank auditor and JSON, `SHA256SUMS.txt` and `README.txt`.
- All nested source checksums and ZIP CRC have been rechecked. It is **not** established that any user-owned offline/cloud backup or independently authenticated scientific escrow already holds these bytes.

The separate post-hoc rank-auditor source SHA256 is `9c18725f0e678597cc4ea9208165fd88cf132fab5b6c9384a469d7975405b306`; its JSON SHA256 is `ff11dd312a6c26a0910eb35a60be84fac3aab922cc6f3920089bb6f5fb4d9ba3`.
