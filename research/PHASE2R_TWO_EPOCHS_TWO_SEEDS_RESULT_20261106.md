# Phase 2R-E2S2 — two epochs × two seed-pairs: source-audited results (2026-11-06)

**Status: bounded numerical research on synthetic data. NOT a historical Phase 2G reproduction, new cryptographic discovery, production protection, or any Phase 2U neural training. DRAFT branch; no merge into main.**

## Evidence provenance and pre-registered scope

- Protocol committed *before* scientific execution: [PHASE2R_TWO_EPOCHS_TWO_SEEDS_PROTOCOL_20261106.md](PHASE2R_TWO_EPOCHS_TWO_SEEDS_PROTOCOL_20261106.md). Original protocol registration commit `0b91b104f1b1c9308f2e9f89adfbb0474e7a8a79`; exact source-index evidence requirement was explicitly added prior to the first CI outcome.
- Official [GitHub Actions run 42222935401](https://github.com/Chatnoir01/ml/actions/runs/42222935401), specialized experiment **SUCCESS**, including eight regression/unit/tamper tests. Original source artifact ID `13504632118`, reported expiry **2026-12-06T13:10:16Z**.
- Tested GitHub Actions checkout source commit `d0e38a5abebfcd9a4da161e17681980415f84299` (the PR checkout/merge revision, not an original September 2G worker revision).
- Original GitHub ZIP: `phase2r_two_epochs_two_seeds_original_github_20261106.zip` SHA-256 **`0f5cca79e7dc0395b672653fcd0b355a35ea1c52e8169232842f26596bd534be`**.
- Independent *external-to-repository* verifier (Python + NumPy) downloaded the actual original ZIP and verified original ZIP CRC, five SHA256SUMS source member digests, three original canonical JSON receipt/audit SHA-256s, both exact 5,600-index epoch permutation lists and 22 original batch-index SHA receipts per epoch, all **1,168/1,168** original shape-bound float32 tensor SHA-256s, original 44-step weight numerical summaries for both replicates, and all **eight** tie-aware AUC receipts (two seeds × two epochs × two cores). Verdict: **`PASS_ORIGINAL_SOURCE_TENSOR_AND_AUC_INTEGRITY`**. Report `phase2r_two_epochs_independent_audit_20261106.json`; standalone verifier `phase2r_two_epochs_independent_verifier_20261106.py`, SHA-256 `e612d9fcdcc1ba62ef4582984b75d202a5b9595b7af3b4d6867635429d9d440a`.
- Experimental environment: one GitHub-hosted machine, two sequential independent processes with actual OpenBLAS **Haswell** vs **Nehalem**, original Python **3.12.14** and NumPy **2.5.3**, one BLAS thread, otherwise matching self-reported normalized runtime; frozen synthetic `phase2r-synthetic-v1` 20-S-Box input fixture, difference **1**; two registered pairs `T/M=776003/786009`, `T/M=776017/786021`. Each model sees exactly 2 full 5,600-row synthetic training epochs, or **44 Adam updates**, not the historical 32-epoch training. It scores the same 1,200-row synthetic test set after each epoch without training on it.

## Verified numerical results

The model contains **1,825 float32 scalar parameters**. A 'different parameter' here means unequal bit patterns, **not** large absolute distance.

| Replicate (M seed) | Epoch | Bitwise-different weights / 1,825 | Relative L2 distance | Haswell AUC | Nehalem AUC | Changed test probability floats /1,200 |
|---|---:|---:|---:|---:|---:|---:|
| 0 (786009) | 1 | 771 | 4.416324867426168e-8 | 0.6318184389140271 | 0.6318184389140271 | 259 |
| 0 (786009) | 2 | 997 | 6.158683012235146e-8 | 0.6363829185520362 | 0.6363829185520362 | 270 |
| 1 (786021) | 1 | 840 | 2.8738232155891683e-7 | 0.626003893214683 | 0.6260052836484983 | 283 |
| 1 (786021) | 2 | 1,056 | 2.9264346782548626e-7 | 0.6293103448275862 | 0.6293103448275862 | 305 |

**First conclusion:** under the specifically manipulated same-host OpenBLAS backend, the count of bitwise-different model parameters increases from epoch 1 to epoch 2 **in both registered seeds**, while the relative L2 weight differences remain extremely small (about 10^-8 to 10^-7).

**Second conclusion:** measured AUCs are identical in **3 of 4 seed/epoch pairs**, but on replicate **1 / epoch 1** they differ by **Haswell minus Nehalem = −1.3904338153070128e-6**. On the same seed, the measured difference disappears at epoch 2 even as 216 additional weight values become bitwise different. Thus AUC behavior is **not monotonic with the count of unequal float32 weight elements**.

## Post-hoc mechanism of the tiny AUC difference (not preregistered)

A separate exploratory comparator inspected all *cross-class* positive–negative prediction pairs in the original saved NPZ, without modifying any original outcome:

- Replicate 0: **520 positive and 680 negative labels**; **zero** changed cross-class order or tie relations at either epoch.
- Replicate 1: **620 positive and 580 negative labels**; exactly **one** positive/negative pair changed at epoch 1, and **zero** at epoch 2. Positive sample index **805** vs negative sample index **1149**: under Haswell, positive score `0.33145493268966675` is slightly lower than negative `0.33145496249198914`; under Nehalem the positive score rises to `0.33145496249198914`, creating an exact **tie**.
- A tied cross-class pair contributes half a concordance instead of zero; its AUC change is exactly **`0.5 / (620 × 580) = 1.3904338153070128e-6`**, explaining all of the observed signed AUC difference in that cell.
- **Zero classification flips** under the fixed threshold of 0.5 in any of the four seed/epoch cells.
- The post-hoc rank/tie analysis is **descriptive only**. The tie event was not a primary preregistered hypothesis, and there was no statistical population claim or correction/p-value calculation.

## Evidence archive

Conversation-generated `phase2r_two_epochs_two_seeds_verified_evidence_20261106.zip`, **1,575,806 bytes**, outer SHA-256:

`2c287c0fec09e14748e4a55542fc75f5042b2b2ddb7c82b4f31cfd901e61649b`

Contains **unmodified** original GitHub artifact ZIP, independent audit Python code, complete independent JSON report, post-hoc pair analysis JSON, README and SHA256SUMS. ZIP CRC checked, source SHA-256s and all original stage receipts passed. **No independently durable user-owned external backup has been confirmed**, and this does not authenticate the GitHub-runner CPU through a third party. Preserve before original Actions artifact expiry.

## What this does NOT show

- It does **not** establish that historical Phase 2G's **64/144** trained-state A/F hash mismatches were caused by OpenBLAS: the September historical CPU and original initial/dataset bytes were never recorded. The historical frozen verdict remains **`phase2g_adaptive_coevolution_not_supported`**.
- N=2 synthetic seed-pairs provide no reliable broad statistical power, external replication, benchmark significance or general 32-epoch instability evidence.
- AUC changes from a **single tie** are not cryptographically meaningful proof of security change, better S-Box nonlinearity, or practical attack improvement. The effect-size magnitudes are tiny; numerical reproducibility is the actual subject.
- This protocol executes exactly **176 bounded original Adam updates** across two kernels and two seed-pairs, not any of the 96 Phase 2U prospective neural fits. No Phase 2U source candidate panel or frozen classical prediction was modified.
- PR #166 remains **DRAFT**. The specialized GitHub Actions workflow succeeded; as of the first evidence audit, general Phase 0 Python 3.10/3.11/3.12 jobs and Phase 1 benchmark were still queued/in progress. Never extrapolate the specialized success to those workflows without a later status check.
