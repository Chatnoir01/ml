# Phase 2R-E8 — eight historical Adam minibatches, independent original-artifact re-audit
**Observed 2026-11-06; original CI artifact, exact SHA-256 and numerical differences independently checked. This is one synthetic computational contrast, NOT original historical Phase 2G evidence or new crypto security.**

## Frozen protocol and exact original source

- **Protocol fixed BEFORE first new observation:** [PHASE2R_EIGHT_ADAM_STEPS_PROTOCOL_20261106.md](PHASE2R_EIGHT_ADAM_STEPS_PROTOCOL_20261106.md), original registration commit `436d03a617cd52e11b3165cc7448ec76c53cbef1`.
- Original GitHub CI: [42152429517](https://github.com/Chatnoir01/ml/actions/runs/42152429517), **success**, independent 10-test synthetic lane and exactly one single-host two-process experiment; original checked-out source commit `befebc840f76ec293ee85ed239305fe2979a83e7`.
- GitHub evidence artifact ID **13472519459**. Original artifact ZIP file **`phase2r_eight_adam_steps_original_github_20261106.zip`** SHA-256 **`d269c0a9fe83eeabda1b3dcddd51cdd9e6b56bd0731cd35b1f7b41f91929b7c5`**.
- The original ZIP contains both original exact `float32` NPZ tensor captures, the two source JSON receipts, independent original per-step CI audit JSON and `SOURCE_SHA256SUMS.txt`.
- A **separate, independent read-only re-audit** checked original ZIP CRC, **5/5** embedded file SHA-256 values, **3/3** canonical JSON receipt/report digests, and **512/512** exact original shape-bound float32 stage SHA-256s (256 per kernel), then independently recalculated **32/32** per-step gradient/parameter/moment/variance statistical summaries and compared them exactly to the original saved output. Standalone evidence: `phase2r_eight_adam_steps_independent_audit_20261106.json` and `phase2r_eight_adam_independent_audit_script_20261106.py`, attached to conversation. Source and audit package are **not independently saved in durable user-owned storage**.
- Run conditions: one hosted x86_64 CPU, Python **3.12.14**, NumPy **2.5.3**, one OpenBLAS thread, all normalized runtime fields identical except forced selected OpenBLAS core **Haswell versus Nehalem**; same exact source, synthetic 20-S-Box fixture, 5600 original training sample permutation, T seed **776003**, M seed **786009** and initial weights/RNG.
- **8 of the original consecutive first-epoch 256-row minibatches (2,048 distinct indices)**, six original gradients and 6 Adam updates per minibatch, with moments/variances carried forward (not reinitialized). The original first microstep's **all 32 original stages** were checked for exact mathematical parity by the new runner. No held-out scoring, no second epoch and no full model fit.

## Verified model parameter divergence, step by step

A model has **1,825** scalar float32 parameters: w1 576; b1 48; w2 1,152; b2 24; w3 24; b3 1. The recorded differences count **bitwise unequal float32 elements**, not changes in cryptographic strength.

| Original Adam step | Updated parameter tensors bitwise different /6 | Updated parameter elements different /1,825 | Maximum absolute parameter delta | Weighted mean absolute parameter delta |
|---:|---:|---:|---:|---:|
| 1 | 4 | 73 | 7.450580596923828e-9 | 4.5162765947106766e-11 |
| 2 | 5 | 198 | 2.9802322387695312e-8 | 3.4918217626336505e-10 |
| 3 | 5 | 273 | 5.960464477539063e-8 | 6.71700459637054e-10 |
| 4 | 5 | 330 | 5.960464477539063e-8 | 9.423900038412172e-10 |
| 5 | 5 | 365 | 5.960464477539063e-8 | 1.1158966752764297e-9 |
| 6 | 5 | 401 | 5.960464477539063e-8 | 1.2896903981901196e-9 |
| 7 | 5 | 425 | 5.960464477539063e-8 | 1.4862568717296809e-9 |
| **8** | **5** | **469** | **5.960464477539063e-8** | **1.7196616183405053e-9** |

The changed *parameter element count* rises monotonically from **73 to 469** (4.0% to 25.7%) in this sample. The *weighted mean absolute numerical delta* also rises at all eight recorded steps. The maximum absolute value rises until step 3 then is constant at about 5.96e-8 through step 8. Therefore: **bitwise difference propagation through eight original sequential Adam updates is observed**, but any assertion of exponential numerical amplification, increasing maximum error at every step, or general 32-epoch instability is unsupported.

## Scientific interpretation and stop gates

**Demonstrated in this single synthetic controlled execution:** choosing only the actual OpenBLAS dynamic-dispatch kernel can affect trained parameter bytes after several successive original Adam microsteps. It explains *how a potential numerical backend mechanism could propagate*, not whether it caused historical Phase 2G divergences.

**Not established:** CPU/BLAS characteristics of the historical Phase 2G original 2026-09 workers; exact original hidden input bytes/initial weights; full 32-epoch weight divergence, AUC, changed candidate ranks, or any benefit of adaptive coevolution or novel secure cipher. The true Phase 2G verdict remains `phase2g_adaptive_coevolution_not_supported`; its original 64/144 trained-model hash differences have not been causally attributed to OpenBLAS.

Only a **separately preregistered** next experiment, with explicit approval and locked unchanged dataset and source provenance, could investigate a full epoch or full training model. This report does **not** authorize those operations, nor any Phase 2U neural training.

**CI qualifier:** exact numerical microexperiment and benchmark were successful when audited; at the moment this report was prepared, the general Phase 0 matrix for the source head was still running. Do not silently reclassify it as passed without checking.

The work stays on a distinct DRAFT [PR #164](https://github.com/Chatnoir01/ml/pull/164), stacked on #163. No changes to `main`, #161 frozen observation-only work, or original Phase 2G/Phase 2U scientific receipts.
