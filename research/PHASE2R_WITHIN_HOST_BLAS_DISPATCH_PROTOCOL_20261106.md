# Phase 2R — controlled within-host OpenBLAS dispatch probe (preregistered 2026-11-06)

**Scope: forward-pass only. No epochs, gradients, optimizer updates, model fit, Phase 2U outcomes, unblinding, or change to frozen Phase 2G.**

## Evidence motivating this control

The read-only official original GitHub [forward-only CI 42129744689](https://github.com/Chatnoir01/ml/actions/runs/42129744689) produced seven of seven identical float32 forward tensor SHA-256s across independent source jobs. **Both jobs actually used OpenBLAS Haswell, with identical normalized runtime profiles.** This is a two-worker Haswell/Haswell reproducibility observation, **not** a cross-kernel experiment.

The separate strict [pretraining CI 42129744792](https://github.com/Chatnoir01/ml/actions/runs/42129744792) produced **16/16 identical** data, model initialization and RNG receipts, but its workers used **Haswell vs SkylakeX**. Its strict auditor correctly marked the observed environments `INCOMPARABLE_NUMERICAL_RUNTIME_PROFILE_MISMATCH` and CI failed *by design*. A failed comparability gate does not mean the observed inputs differ.

All six original source ZIPs and their JSON receipt digests were checked, independently compared and preserved in the conversation artifact `phase2r_20261106_six_original_ci_artifacts.zip`, outer SHA-256 **`45f59fbcbcf91e69f67ccdf00da47b4b59cb95156d420ac1ae369505cc1c79d8`**. The archive is **not proven to be in user-controlled durable storage**.

## New question, narrow observational scope

On a *single GitHub Actions host* with pinned software, fixed synthetic S-Box data and identical initialized model state, does switching **only OpenBLAS dynamic-dispatch kernel** from native `SkylakeX` to forced `Haswell` affect any of the seven fixed first-batch float32 forward tensor digests?

OpenBLAS `DYNAMIC_ARCH` supports choosing a kernel through `OPENBLAS_CORETYPE=HASWELL`. Reference: https://www.openmathlib.org/OpenBLAS/docs/usage/ and https://github.com/OpenMathLib/OpenBLAS/wiki/Faq . Forcing a *lower*-feature Haswell kernel on a SkylakeX-capable host avoids the unsafe opposite direction (running AVX-512 instructions on a host without that support).

## Frozen no-training method

[Within-host CI workflow](../.github/workflows/phase2r-within-host-blas-dispatch.yml) creates **two separately scheduled jobs** (replicate identifiers `1` and `2`) to increase the chance of selecting different physical host CPU configurations. **Within each individual job**, two separate Python processes run sequentially on the *same GitHub-hosted machine*, rather than comparing jobs with different CPU/VM environments:

1. Pin Ubuntu 24.04, CPython **3.12.14**, NumPy **2.5.3**, `threadpoolctl==3.6.0`, and all five numerical thread-limit environment variables `=1`.
2. **Native probe:** run `phase2r_forward_only_probe` with `OPENBLAS_CORETYPE` explicitly **unset** (auto-detection).
3. **Forced probe:** a fresh Python process with `OPENBLAS_CORETYPE=HASWELL`. Verify its actual `threadpoolctl` architecture reads `Haswell`, not merely the requested environment setting.
4. Reuse exact previously registered synthetic Phase 2R 20-S-Box fixture and first **256 rows** of difference=1 / replicate=0, frozen historical T/M seeds and float32 network initialization.
5. Run **only** `xb @ w1 + b1`, `tanh`, second matrix multiply, second `tanh`, logits and sigmoid. Compute and record SHA-256 of seven stage arrays using the existing versioned little-endian shape-preserving serializer. No training operation is ever invoked.
6. Compare the two signed-by-content JSON receipts with the existing `compare_forward_probes` validator; both executions must use the same GitHub commit, identical initialization and RNG receipts and pinned setup.
7. Store the original native/forced JSON and independently generated comparative JSON as artifact even for a negative/inconclusive result. No parameter tuning after inspection.

## Decision rules (set BEFORE any observations)

- **Native `SkylakeX`, forced `Haswell`**: eligible *within-host kernel contrast*. If any tensor differs, record the earliest stage. If no tensor differs, record all-seven-stage byte equality. Neither supports any claim about the later gradient/Adam training path.
- **Native `Haswell`, forced `Haswell`**: **INCONCLUSIVE_NO_DISPATCH_CHANGE** even if the two outputs match; do not present as a SkylakeX/Haswell contrast.
- **Any other native kernel**: **OUT_OF_TARGET_KERNEL_PAIR**, with full provenance retained. Do not convert results into support for the SkylakeX/Haswell hypothesis.
- **Forced kernel not actually `Haswell`, changed training seed, missing or corrupted receipt or unauthorized training**: fail closed.
- The matrix of two hosted runner replicates is opportunistic; if neither samples a SkylakeX-capable host, the experiment remains inconclusive, not failed science.

The only intended manipulated factor **within one host** is OpenBLAS's dynamic kernel dispatch. NumPy's SIMD path and other host behavior remain subject to software/environment checks and may confound wider interpretations; a changed output under this controlled dispatch would **support a narrow OpenBLAS dispatch-related mechanism in this one test**, not conclusively explain the original Phase 2G anomaly.

## Research firewall

No claim of a newly secure cipher, universal neural cryptography effect, causal interpretation of the frozen 64/144 different trained weights, or validation of the prospective 96-run Phase 2U study. The fixed scientific verdict remains `phase2g_adaptive_coevolution_not_supported`.

**Archival note:** the GitHub Actions CI artifact retention for the previous 2026-11-06 runs is 30 days, so source archives must be exported to durable user storage before 2026-12-06.
