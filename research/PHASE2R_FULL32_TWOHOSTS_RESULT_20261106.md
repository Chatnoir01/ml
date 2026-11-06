# Phase 2R-F32H2 — two original 32-epoch host runs, independent source re-audit (2026-11-06)

**Status: original two 32-epoch host jobs SUCCESS, all original source byte receipts independently checked.** This is a SYNTHETIC numerical-reproducibility result, NOT a new cryptographic security property, historical Phase 2G causality finding or any Phase 2U 96-run neural outcome.

## Preregistered protocol and original GitHub evidence

The [32-epoch, two-new-seed, two-host protocol](PHASE2R_FULL32_TWOHOSTS_PROTOCOL_20261106.md) was fixed **before the experiment**, commit `0640dd34ffe4cc7a49edbb9a56c22316a4dec860`. The actual tested experiment source was **`1dc69d438805ecb5759932486e559178f78fcd0d`**. Original GitHub [Actions run 42229688026](https://github.com/Chatnoir01/ml/actions/runs/42229688026):

- Original **host 1** artifact ID **13507985660**, original unmodified ZIP `phase2r_full32_host1_original_20261106.zip`, SHA-256 `a30eab049fe19c8d802bcf3decc204dddc681d96b2e5c7d011730b0b0279687a`.
- Original **host 2** artifact ID **13508890510**, original unmodified ZIP `phase2r_full32_host2_original_20261106.zip`, SHA-256 `b73e01613ee7addcd33ba88199acc03d2ae19dc9d01a03e8f31d9e86580dd18d`.
- Both original paired model jobs **succeeded**. A third CI cross-host report job was **queued** at initial independent verification, so its success is not asserted here.
- The source used **CPython 3.12.14, NumPy 2.5.3, OpenBLAS 0.3.34.106.0, one BLAS thread**. In each job two sequential same-host processes forced **Haswell** vs **Nehalem**. The two jobs report DIFFERENT CPU SIMD feature sets: **22 features** in host 1 (no AVX-512), **40** in host 2 (AVX-512 included). This is observed runtime metadata, NOT physical-chip or cloud-host independence attestation.

The only fresh-to-Phase2R original seeds were **r6 (T=776083/M=786087)** and **r7 (T=776097/M=786101)**. The frozen synthetic 20 S-Box fixture, original 5,600/1,200/1,200 split and float32 12→48→24→1 network were unchanged. Original optimizer code performed **32 complete epochs, 704 updates per model (21×256 + final 224 training examples per epoch)**, retaining the Adam moments/variances and consuming a fresh original seeded 5600-index permutation for each epoch.

**Work accounting:** 2 seeds × 2 actual same-host kernel runs × 2 independently scheduled GitHub jobs = 8 complete **synthetic** 32-epoch model fits (**5,632** Adam updates). Exactly **zero** sealed prospective Phase 2U neural model fits. The original historical Phase 2G data were **not** replayed.

## Independent audit (outside the GitHub workflow)

Two original GitHub ZIPs were downloaded and a **separate read-only** Python verifier recalculated their integrity and core scientific records:

- Both GitHub ZIP CRC valid; each original five-entry SOURCE_SHA256SUMS list matches.
- All **six canonical source JSON self-hashes** (two original receipts and one comparison report per host) match.
- **4,704 / 4,704** original versioned, domain-separated, shape-bound float32 SHA256 stage digests match saved NPZ bytes (2,352 per host). Explicit scalar b3 shapes verified.
- Every original **5,600-index permutation** and all 22 sampled minibatch slices were verified per epoch, across both new seeds, both kernels and both jobs. Exact source dataset, initialized-model and RNG-state fingerprints match within each paired job.
- All original **24 fixed-checkpoint tie-aware AUCs** (2 seeds × 2 kernels × 6 checkpoint epochs × 2 hosts) independently recomputed exactly from original 1,200-item float32 test probabilities and binary labels. All 32 epoch-end model-state relative L2 distances, bitwise-different weight counts and positive-negative rank/tie changes recomputed.
- **NEW POST-OUTCOME descriptive cross-host source audit**: despite different reported CPU SIMD features, the original 1,176 NPZ arrays saved by host 1 using the forced Haswell core are **bitwise identical** to the 1,176 arrays saved by host 2 using the same forced Haswell core. Likewise **1,176/1,176** for Nehalem. **2,352/2,352 original source arrays match across hosts at the same core**. This observation was not a preregistered strict cross-hardware identity gate and is NOT hardware identity attestation.

Independent verifier: `phase2r_full32_twohosts_independent_verifier_20261106.py` SHA-256 `1a3ca496d95d7b46cede861f87d9134ffd7d83af0b004d0aaa0c365982737683`. Independent JSON audit: `phase2r_full32_twohosts_independent_audit_20261106.json` SHA-256 `47ff58a412b0ed7ab08684f7822d242d5bd5a88911a2a02fa20fe7979b79a902`.

## Preregistered primary outcome: after epoch 32

The two GitHub jobs produced the **same exact numerical results** in each corresponding forced-core condition:

| New-to-Phase2R model seed | Host | Bitwise-different model parameters / 1,825 | Relative model-weight vector L2 distance | Haswell test AUC | Nehalem test AUC | Changed positive-negative test score relations |
|---:|---:|---:|---:|---:|---:|---:|
| **786087** | 1 | **1,701 (93.2%)** | **4.2691616623287226e-7** | **0.6593973214285714** | **0.6593973214285714** | **0** |
| 786087 | 2 | 1,701 (93.2%) | 4.2691616623287226e-7 | 0.6593973214285714 | 0.6593973214285714 | 0 |
| **786101** | 1 | **1,660 (91.0%)** | **3.377278998159002e-7** | **0.666010101010101** | **0.666010101010101** | **0** |
| 786101 | 2 | 1,660 (91.0%) | 3.377278998159002e-7 | 0.666010101010101 | 0.666010101010101 | 0 |

Although the number of bitwise-different weights **generally increases**, it is **NOT strictly monotonic** across all 32 original epoch boundaries (six count decreases for r6, eight for r7 in the audited host-1 series). Relative L2 and absolute weight magnitudes remain **extremely small** (`10^-7` relative after 32 epochs). **Many changed float32 bits do NOT imply large different neural functions, crypto strength or model failure.**

At epoch 32, the same fixed test set includes **725/1,200 differing probability float32 bit patterns** for r6 and **596/1,200** for r7, but no positive/negative test rank or tie relation changes and no exact AUC change.

## Six preregistered synthetic test checkpoints

| Model seed | Epoch 1 AUC delta H-N | Epoch 2 AUC delta H-N | Epoch 4 | Epoch 8 | Epoch 16 | Epoch 32 |
|---:|---:|---:|---:|---:|---:|---:|
| 786087 | 0 | **-0.0000013950892857605979** | 0 | 0 | 0 | **0** |
| 786101 | 0 | 0 | 0 | 0 | 0 | **0** |

**Mechanism:** the epoch-2 difference in r6 corresponds to exactly **one** positive-negative class ranking/tie relation difference, not a persistent functional advantage. Across all other preregistered checkpoints the exact test AUCs are equal, with zero changed positive-negative relations. The test was repeated across two jobs; **those are the same two seeds, NOT four independent seed samples**.

## Limitations, scientific verdict, and retention

- Actual first two-epoch mathematical parity was checked against frozen #165/#167 source. That does not make the original 2026-09 Phase 2G raw data or source hardware available; **64/144 historical trained-state SHA mismatch root cause STILL NOT ESTABLISHED**.
- These are only **N=2** new-to-Phase2R synthetic seeds, not population inference. The two independently scheduled CI jobs are not independent physical-CPU attestations. Different available SIMD instruction sets may coexist with the same forced BLAS instructions; no architectural universality established.
- A difference in a `float32` weight bit or an AUC tie event is not cryptanalysis, an attack, a newly secure cipher, or evidence of adaptive evolutionary improvement.
- Frozen Phase 2G verdict remains **`phase2g_adaptive_coevolution_not_supported`**. No original frozen scientific source modified; zero Phase2U 96-run neural trainings; PR #168 DRAFT, no merge to `main`.
- An independently audited conversation evidence package `phase2r_full32_twohosts_verified_evidence_20261106.zip`, **9,971,937 bytes**, SHA-256 **`94ccff4f0ca73ba536694ccab4f784c9dbd1a7f636646926516fc5d5e77323e4`**, contains both **unchanged original GitHub ZIPs**, the independent verifier, independent JSON audit, README, and SHA256SUMS. It is **NOT proven durably backed up outside ChatGPT/GitHub**. Original source Actions artifacts expire around **2026-12-06**.

**Initial CI status check:** original two synthetic 32-epoch jobs and Phase1 benchmark succeeded. Third cross-job report and three general Phase0 Python matrix jobs still queued/in progress. The final status must be checked separately; do not call all CI green yet.
