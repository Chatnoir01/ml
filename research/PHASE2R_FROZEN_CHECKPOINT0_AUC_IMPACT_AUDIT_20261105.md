# Phase 2H/2R — frozen Phase 2G checkpoint-zero model-hash differences versus inference metrics (2026-11-05)

**New evidence, read-only audit of ORIGINAL original Phase 2G arm artifacts. No new network training, key disclosure, cryptographic security claim, revised 2G verdict, or Phase 2U execution.**

## Background and precise terminology

The historic Phase 2G experiments started adaptive A and fixed F from the same declared 20-S-Box curriculum and dataset/model seed grids. Earlier frozen receipt audits found **64 of 144 distinct trained checkpoint-zero model-state SHA-256 hashes**, concentrated in four of nine paired evolution seeds (16/16 disagree in each of four seeds). These are hashes of the **trained weights at the first checkpoint**, NOT measured checkpoint-zero *initial* weights before training. The old artifacts do not store the raw initial weights.

[Original Phase 2G GitHub Actions run 35572084785](https://github.com/Chatnoir01/ml/actions/runs/35572084785) is the only source. All 18 original A/F ZIPs were re-opened from the already preserved 39-artifact package, their ZIP CRC and original canonical `scientific_payload_sha256` were checked again, and checkpoint-zero score-receipt model SHA-256 values were cross-checked against the corresponding arm's original model receipts.

## Previously unquantified functional impact

For **every one of the 9 A/F seed pairs**, the checkpoint-zero scored candidate fingerprint sets were identical between A and F. Across these pairs there were exactly:

- **794 matched candidate-level score pairs**.
- **715/794** had exactly the same recorded `neural_advantage` value; **79/794** differed (maximum absolute deviation **0.00000625**).
- **12,602/12,704** per-candidate, per-model AUC comparisons were exactly equal as serialized in the original receipts; **102/12,704** differed, with **largest absolute deviation 0.00005**.
- **All nine total candidate score orderings were identical**, using ascending `neural_advantage` and candidate SHA3-256 fingerprint as deterministic tie break. This also means the corresponding top-10 and top-20 fingerprint sets were unchanged at checkpoint zero.

| Evolution seed | Equal trained state SHA /16 | Equal candidate score /total | Equal individual AUC /total | Highest AUC abs difference |
|---|---:|---:|---:|---:|
| 726011 | 16 | 91/91 | 1456/1456 | 0 |
| 726023 | 16 | 89/89 | 1424/1424 | 0 |
| 726037 | 16 | 85/85 | 1360/1360 | 0 |
| 726049 | 0 | 89/93 | 1484/1488 | 0.000025 |
| 726061 | 0 | 54/89 | 1371/1424 | 0.000050 |
| 726073 | 0 | 54/87 | 1355/1392 | 0.0000125 |
| 726087 | 16 | 91/91 | 1456/1456 | 0 |
| 726099 | 16 | 79/79 | 1264/1264 | 0 |
| 726113 | 0 | 83/90 | 1432/1440 | 0.000025 |
| **TOTAL** | **80/144** | **715/794** | **12602/12704** | **0.00005** |

Original per-seed scientific SHA-256s, source filenames, and calculated per-seed metrics are preserved in the standalone dated file `phase2g_checkpoint0_functional_impact_audit_20261105.json` attached to the ChatGPT conversation. The original 39 artifact bytes are preserved separately with SHA256SUMS, as recorded in [portfolio backup receipt](https://github.com/Chatnoir01/ml/blob/research/portfolio-closure-register-20261102/research/PHASE2G_39_ARTIFACT_PRESERVATION_RECEIPT_20261105.md). The generated JSON is read-only research output, not a new scientific training run.

## Scientific interpretation and limits

**Verified:** the first checkpoint's final serialized weights do not always agree at a bit level, but their **measured AUC and candidate-level advantage outputs are overwhelmingly identical or very close**, and **no candidate score order changes** in any of the nine initial A/F paired checkpoint-scoring panels. This is an observation of **functional metric stability at this specific checkpoint**, not full functional identity.

**Not established:**
- Whether the *raw score probabilities*, gradients, weights or optimizer states are close: the original JSON contains **SHA-256 hashes rather than the full weight bytes**. A changed SHA could represent a one-bit float change or a large numerical difference.
- Why **four of nine** original job pairs diverged at the weight-hash level: no original data byte hashes, initial-weight bytes, CPU-specific BLAS/SIMD profiles or full scheduler provenance were preserved.
- Whether small AUC differences propagate to selection boundaries at later generations. This audit compares only checkpoint **zero** and cannot rescue any subsequent Phase 2G causal claim.
- Whether the original `phase2g_adaptive_coevolution_not_supported` negative verdict would persist under a newly rerun full study (never post-hoc overwrite its frozen conclusion).

The AUC metric is ordinal/rank-based and can be robust to tiny floating point perturbations, so a mismatch of exact trained-weight SHA does **not automatically mean a materially different distinguisher**. Conversely similar AUC is **not** proof of numerical equivalence. This result suggests investigating hardware/BLAS floating point variability and its effect on hidden weights, but names **no confirmed cause**.

## Preregistered future gates, still locked

1. The already implemented 16-cell *pretraining-only* two-runner preflight observed 16/16 train/validation/test and initial RNG/weight matches with a separate synthetic fixture. This proves no numerical training equivalence. See [runtime-normalization audit](PHASE2R_RUNTIME_NORMALIZATION_AUDIT_20261105.md).
2. Future actual-model tests must collect initialized tensor bytes, deterministic input bytes, fixed optimizer microsteps, full final weight bytes and the normalized CPU/BLAS profile, under a separately frozen protocol. No training is authorized by this report.
3. Preserve original artifacts before their advertised **2026-12-20** expiry in user-owned durable storage.

**Frozen Phase 2G scientific verdict remains** `phase2g_adaptive_coevolution_not_supported`. No security claims are warranted.
