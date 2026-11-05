# Phase 2R — independent re-audit of original Phase 2G checkpoint-zero A/F artifacts (2026-11-05)

**Status: read-only analysis of ORIGINAL frozen artifacts; no training, no change to Phase 2G, and no authorization of future Phase 2R/2U experiments.**

## Sources and integrity

- [Official Phase 2G run 35572084785](https://github.com/Chatnoir01/ml/actions/runs/35572084785).
- **18 actual GitHub Actions artifact ZIPs**: all original paired A/F arm/seed outputs, nine evolution seeds × two arms. All 18 ZIP CRC checks passed. All 18 original `arm.json` scientific payload SHA-256 digests were independently recomputed using the original canonical sorted compact JSON (excluding the `scientific_payload_sha256` field). All matched.
- Audit script preserved the 144 explicit model-state receipt pairs, original artifact IDs, ZIP SHA-256s, and declared T/M seed grids in the standalone downloadable conversation artifact `phase2g_checkpoint0_af_reaudit_20261105.json`.
- Separate evidence package `phase2g_checkpoint0_af_source_evidence_20261105.zip` includes **the unchanged 18 original ZIPs**, full JSON audit, readable summary and SHA256SUMS, package SHA256 **`5b702a495c3fe956fcf81a132c47e9c5583f6e18838c055480b1793788652ad4`**. This package is **not** an independently durable external backup; the user must save a copy outside this conversation. Original GitHub Actions artifacts currently advertised expiry 2026-12-20.

## Result: all-or-none across the 16 per-seed checkpoints

| Evolution seed | A/F state hashes matching / 16 | Differing / 16 |
| ---: | ---: | ---: |
| 726011 | 16 | 0 |
| 726023 | 16 | 0 |
| 726037 | 16 | 0 |
| 726049 | 0 | 16 |
| 726061 | 0 | 16 |
| 726073 | 0 | 16 |
| 726087 | 16 | 0 |
| 726099 | 16 | 0 |
| 726113 | 0 | 16 |
| **TOTAL** | **80 / 144** | **64 / 144** |

For **all nine** paired seeds the initial 20-S-Box curricula, their canonical fingerprint order and digest, and every declared training dataset/model seed matched between A and F. The 16 receipts contain two input differences (1 and 256), each with eight replicates. Among the four mismatched seeds, **all eight per difference mismatched**. Even after discarding replicate/difference order, the sets of 16 A/F final-model SHA-256s have **zero intersection**, so swapped receipt order cannot explain the anomaly.

Do not conflate a model-state SHA-256 with an arm-tagged training-receipt SHA-256: the latter is naturally different even when actual model-state bytes match.

## Original job logs constrain the environment hypothesis

The official workflow uses `ubuntu-24.04`, Python 3.12, and pinned `numpy==2.5.3`. Sampled **actual original A/F job logs** show Ubuntu image `20260907.300.1`, CPython `3.12.14` and NumPy `2.5.3`, including both matching and mismatching pairs. The effective numerical thread count, CPU ISA, exact BLAS runtime configuration, and input bytes were not recorded in the saved JSON receipts.

Examples that disprove a simple Azure-region rule:
- **726061**, 16/16 mismatched: both A and F ran in Azure **westus2**, on distinct workers.
- **726037**, 16/16 matched: A ran in **eastus2** while F ran in **westus**.

Other original sampled mismatched pairs: seed 726049 (westcentralus/westus), seed 726073 (westcentralus/westus3), seed 726113 (eastus/eastus2). A pair can match despite cross-region execution or differ inside a single Azure region. **This does not rule out per-worker CPU, BLAS or threading variability.**

The original `phase2g_shared_model.py` blob is the same in original Phase 2G and the later Phase 2R investigation branch: Git blob SHA-1 `61ea65be472c8ea3b9d31e8394274aea64e4098d`. It explicitly uses a local seeded NumPy generator for weights and shuffles, and seeded `random.Random` for each training split. The code suggests deterministic intent; **without actual original input bytes or initialization snapshots, exact numerical identity is not established**.

## Interpretation and next controlled evidence gate

**Verified:** the stored final serialized model outputs differ in 64 of 144 identical-declared checkpoint-zero paired cells, concentrated in four of nine seeds, with no cross-arm hash overlap on those seeds. This is a serious reproducibility/comparability anomaly at the execution level.

**Not proven:** which stage first diverged or what caused it; whether this numerical variation materially affected the Phase 2G held-out effect; any adaptive learning benefit; any novel secure cipher.

Prospective experiment prerequisites remain:
1. For each exact sample, record and independently recompute canonical train/validation/test bytes and SHA-256; test original input invariance across fresh processes.
2. Capture model initialization bytes, local RNG state before shuffling and after, and final serialized model bytes without consuming RNG or changing trainer math.
3. Pin Python, NumPy, backend/BLAS and CPU/ISA/thread settings; explicitly compare same-runner repeated results **before** cross-runner tests.
4. Keep A1/A2/F1/F2 synthetic fixture controls strictly separate from the original Phase 2G frozen science. Never overwrite the 2G negative verdict or invent missing historical weights.

**Original frozen Phase 2G result remains** `phase2g_adaptive_coevolution_not_supported`. This new report strengthens the provenance investigation, not a cryptographic security claim.
