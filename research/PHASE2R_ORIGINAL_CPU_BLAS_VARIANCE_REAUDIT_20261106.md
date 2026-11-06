# Phase 2R — actual two-runner CPU / OpenBLAS provenance difference confirmed (2026-11-06)

**Read-only audit of ORIGINAL independent CI source artifacts** from [GitHub run 42126427525](https://github.com/Chatnoir01/ml/actions/runs/42126427525), commit `017704f6ec1c88a70fc59c9ac8c03cfa6e265152`. This is an observational finding on a synthetic fixture, **not** an explanation for the original Phase 2G historical 64/144 trained-model hash differences.

## Original downloaded evidence

| Source job | GitHub artifact ID | ZIP verified | Normalized runtime SHA-256 |
|---|---:|---|---|
| A | **13460739975** | CRC and canonical JSON receipt/hash match | `eb76c2d0fa03480321c9ac113e3fbccc3c585dd2572eb2f89ee57e7cf9186aa8` |
| F | **13461936720** | CRC and canonical JSON receipt/hash match | `a6c529a5d2d4a684e9894ee6b3f306a98b5ae3b6726c05572b8e425fac91304f` |

Both original source files were fetched from the official source run, opened and independently recalculated against their self-reported receipt digests and the normalized runtime profile JSON SHA-256. All 16 declared cell identities match the frozen prospective two-runner geometry.

## Actual controlled observation

- All **16/16** per-cell train dataset SHA-256 equal, and likewise **16/16 validation, 16/16 test** SHA-256.
- All **16/16** initialized model state SHA-256 identical; all **16/16** NumPy state SHA-256 identical.
- Shared operating system **Linux**, `x86_64`, Python **3.12.14**, NumPy **2.5.3**, OpenBLAS **0.3.34.106.0**, `pthreads`, and **one observed BLAS thread**.
- **Not the same normalized numerical runtime**:
  - **A** reports OpenBLAS `architecture=SkylakeX` and **42** available CPU SIMD feature names, including AVX-512 families.
  - **F** reports `architecture=Haswell` and **22** available CPU SIMD feature names, without AVX-512.
- All five numerical thread variables were set to `1`.

**Interpretation:** the sampled pretraining input bytes and weight/RNG initialization are stable even when the numerical backend has different effective CPU capabilities. Under the strict prospective reproducibility standard, **the workers are INCOMPARABLE for subsequent bytewise floating-point training tests**. We now have direct evidence of a relevant environmental difference, not just an accidental hostname difference in `numpy.show_runtime()`.

**No causation established:** This finding does not prove the CPU architecture caused *any* original Phase 2G trained-model differences. The historical 2026-09 runner CPU/BLAS profiles were not captured, so they cannot be recovered from these 2026-11 new machines.

## Evidence retention

New extracted JSON audit `phase2r_cpu_blas_profile_reaudit_20261106.json` contains all 16 matched-cell controls, exact original ZIP SHA and receipt identities, plus the normalized runtime differences.

Self-contained local conversation evidence archive `phase2r_cpu_blas_profile_original_evidence_20261106.zip` includes **both original ZIP streams**, the complete JSON and Markdown report, and a SHA256SUMS list; outer archive SHA-256 `e13e9c7a9e57becff45339ce7db4475ba5652d0c015bcc2c6960e408fc78e8c3`. This is **not independently durable** until copied and verified outside the conversation, and the original source artifacts expire approximately 2026-12-05.

## Next zero-training gate

A separately preregistered forward-only, no-gradient numerical probe ([protocol](PHASE2R_FORWARD_CPU_PROBE_PROTOCOL_20261106.md)) runs exact float32 first-batch matrix products, tanh, logits and sigmoid on two independent CPU/BLAS configurations, recording seven staged SHA-256 fingerprints and the first divergence if any. The probe **never trains a neural model**. Its CI must be observed; no claim of a new result is made before actual original receipts are inspected.

The original Phase 2G verdict remains `phase2g_adaptive_coevolution_not_supported`. No Phase 2R neural training, Phase 2U execution or changes to main are authorized.
