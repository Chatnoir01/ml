# Phase 2R — prospective inference-only CPU/BLAS numerical probe (2026-11-06)

**Scope: exploratory, TRAINING-FREE first-batch numerical instrumentation. No gradient, no Adam update, no epoch, no model training, no held-out Phase 2G result opening, no Phase 2U neural outcome. This study does not authorize any of those operations.**

## The observed gap motivating this experiment

The [strictly sourced original independent runner audit](PHASE2R_RUNTIME_NORMALIZATION_AUDIT_20261105.md) found the **same 16/16 split-data SHA, seeded initial weight SHA and pre-shuffle NumPy RNG state SHA** on two independent runners under Ubuntu 24.04, Python 3.12.14, NumPy 2.5.3 and 1 BLAS thread.

However, the original normalized numerical profiles were **not comparable**:
- worker A OpenBLAS **SkylakeX**, exposing AVX-512 features;
- worker F OpenBLAS **Haswell**, without AVX-512 features;
- same OpenBLAS version **0.3.34.106.0**, and same configured thread count **1**.

This difference was proved by reading BOTH original source artifact ZIP receipts and verifying their canonical receipt/profiles SHA-256. Its independent compact evidence package SHA-256 is `e13e9c7a9e57becff45339ce7db4475ba5652d0c015bcc2c6960e408fc78e8c3`, stored as an attached conversation file `phase2r_cpu_blas_profile_original_evidence_20261106.zip`; not yet confirmed in a user-controlled durable storage system.

The original Phase 2G historic phenomenon was **64 of 144 different trained-state SHAs** (not the raw untrained weights), across four of nine initial seeds. **12,602 of 12,704 scored AUCs** were equal, and all nine initial candidate rankings identical. Historical CPU/BLAS profiles weren't archived; attributing those historic differences to CPU instruction sets would be unwarranted.

## Test question — a new synthetic control, not historical inference

Can the **specific first forward-pass floating-point tensor stages** from the existing Phase 2G network differ at a bit level when evaluated on separate hosted runners with identical synthetic inputs/seeded weights but different NUMA/CPU SIMD/BLAS profiles?

This probes a *plausible* source of numerical variation without computing a gradient or training, not an explanation of the old frozen effect.

## Fixed method

The source-of-truth is the new [forward-only probe module](../src/adversarial_sbox/phase2r_forward_only_probe.py) and [CI workflow](../.github/workflows/phase2r-forward-cpu-probe.yml).

- Use previously frozen synthetic **20 × 256** S-Box fixture `phase2r-synthetic-v1` and existing Phase 2G dataset generator. No historical 2G initial candidate panel is used.
- Fix `difference = 1`, `replicate = 0`, historical first checkpoint T/M seeds and the first **256 sample rows**, *not* a shuffled epoch batch. Train/validation/test geometry is 5,600/1,200/1,200 but only this **first forward batch** is evaluated.
- Use the same original 2G model-seeded float32 initializer, verify its initial byte digest and RNG-state digest without consuming epoch permutation draws.
- Execute **exactly** the forward operations from `_fit_shared_model_state_bytes`: `xb @ w1 + b1`; `tanh`; `h1 @ w2 + b2`; `tanh`; `h2 @ w3 + b3`; historical sigmoid. No gradient call, no loss, no optimizer update.
- Hash seven staged float32 tensor byte arrays using a domain-separated, versioned length + shape + C-order little-endian serializer. Do not use string `repr` or auto-convert float64.
- Pin separate job Python **3.12.14**, NumPy **2.5.3**, `threadpoolctl==3.6.0`, five thread-limit variables `=1`. Record normalized CPU SIMD and BLAS provider/version/core/thread profile from `threadpoolctl` before comparing.
- The third job checks canonical receipt integrity, the same source commit, exact initial-state/RNG values and the seven stage digests. Records the earliest differing stage, and **always preserves observational output**, even when runner profiles differ.
- Tests: seven synthetic-only unit tests for float32/row-order/shape digest, preregistered seed and CPU/BLAS pinning, omitted/tampered metadata, CPU drift classification, first stage localization, fixed synthetic-batch inference and no-training attestations.

**The CI workflow does not try to make the host CPU profiles equal**. It must report whether they actually match. Distinct host architectures are a source of comparison uncertainty rather than proof of a causal hardware effect.

## Interpretation rules fixed before outcome

1. **Identical stage hashes, different hardware profiles:** report `IDENTICAL_FORWARD_BYTES_UNDER_INCOMPARABLE_RUNNERS`. The sampled forward calculation was byte-stable even on those two different CPU profiles; later-gradient or optimizer steps are still untested.
2. **Different stage hashes, different hardware profiles:** report `DIFFERENT_FORWARD_BYTES_UNDER_INCOMPARABLE_RUNNERS` and earliest different stage. This proves a numerical output difference in the sampled calculation, **not** that CPU or BLAS architecture alone caused it.
3. **Identical stage hashes, same normalized profile:** report `IDENTICAL_FORWARD_BYTES_SAMPLED`; scoped to this sample, no full training claim.
4. **Different stage hashes, same normalized profile:** report `DIFFERENT_FORWARD_BYTES_SAMPLED`; investigate missing runtime provenance and undefined numerical nondeterminism.
5. Source-state or digest tampering must raise a validation exception; never label a malformed receipt PASS or fill in missing stages.

No output will establish a newly secure cipher, original theoretical result, global reproducibility or the cause of the historic Phase 2G finding.

## Next gated questions (NOT authorized by this test)

A later controlled Phase 2R *microstep* experiment could check first gradient, Adam update and full end-of-training state — but unlike this inference-only probe it would perform training arithmetic. It requires an explicit separately versioned scientific protocol and permission, and must not silently use the old 2G held-out evaluation. The 96 Phase 2U prospective neural runs remain unexecuted and locked.

**Reference studies and prior findings remain immutable.** The frozen Phase 2G verdict is `phase2g_adaptive_coevolution_not_supported`.
