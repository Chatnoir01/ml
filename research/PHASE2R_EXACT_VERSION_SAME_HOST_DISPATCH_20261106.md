# Phase 2R — exact-version, same-host Haswell-vs-Nehalem forward-only control
**Prospective engineering protocol, registered 2026-11-06 BEFORE this new workflow's first observation. No training.**

## Separate scientific question

The actual original Phase 2G scientific model was implemented in Python 3.12.14 and NumPy 2.5.3, with a NumPy wheel linked to OpenBLAS 0.3.34.106.0 in the archived CI. The historical 64/144 SHA-256 mismatches were measured **after the first checkpoint's model training**, not at raw model initialization. Their cause remains unknown. A previous *shape-matched local proxy*, Python 3.13 / NumPy 2.3.5, observed small floating-point differences when forcing OpenBLAS SkylakeX versus Haswell. That local result is **not exact software/fixture replication**.

The two earlier [native vs forced Haswell same-host CI replicas](https://github.com/Chatnoir01/ml/actions/runs/42138748840) both drew Haswell-native machines and were correctly classified `INCONCLUSIVE_NO_DISPATCH_CHANGE`. Rather than spending additional CI to draw SkylakeX at random, this NEW protocol performs a **deterministic, separate comparison** of **Haswell versus Nehalem** on one eligible GitHub runner, using the original Python/NumPy software version and the actual pinned synthetic Phase 2R S-Box fixture.

**This is NOT an after-the-fact replacement of the earlier SkylakeX/Haswell study** and it cannot answer whether the historic runners were Haswell/SkylakeX. It asks only whether changing numerical kernel dispatch on a single host can affect the exact Phase 2R first forward batch under historical package versions.

## Fixed design (one GitHub job, two subprocesses, no retry lottery)

- Source: current dated draft `research/phase2r-observation-only-instrumentation-20261104`, 20-S-Box pinned `phase2r-synthetic-v1` fixture and existing `phase2g_shared_model.build_shared_training_splits`.
- One fresh GitHub-hosted Ubuntu 24.04 **x86_64** job, CPython **3.12.14**, NumPy **2.5.3**, `threadpoolctl==3.6.0` and five thread-limit variables `=1` **before Python import**. The runtime profile records actual Python/NumPy version, BLAS provider/version, 1 actual BLAS thread and CPU SIMD features. If actual BLAS version/provider differs, report honestly: this is the pinned `numpy==2.5.3` wheel, not a reconstructed historic VM.
- **Two sequential independent Python subprocesses on the SAME host:** (1) `OPENBLAS_CORETYPE=HASWELL`, (2) `OPENBLAS_CORETYPE=NEHALEM`. Runtime inspection must confirm exactly **Haswell** and **Nehalem**, not merely the environment variable. Haswell-to-Nehalem reduces ISA and does not require a SkylakeX-capable runner. This method relies on OpenBLAS's documented DYNAMIC_ARCH `OPENBLAS_CORETYPE` interface (https://www.openmathlib.org/OpenBLAS/docs/usage/).
- Same existing `phase2r_forward_only_probe`: difference=1, replicate=0, original registered first T/M seeds, exact synthetic 20-S-Box fixture. Generate 5600/1200/1200 train/validation/test samples with original shared generator. Use **first 256 train pairs in source order**, not the shuffled first epoch batch. Construct 12→48→24→1 seeded float32 weights with no training; only evaluate the seven staged forward operations.
- **New optional read-only tensor evidence dump:** `forward_only_probe --tensor-output` saves exactly the seven original `np.float32` stage arrays to NPZ **from the same computation**, without regenerating their values. It retains the previous canonical SHA-256 receipt for all seven stage tensors, unchanged.
- Independent `phase2r_dispatch_numeric_audit.py` first verifies the exact version, fixed seed/difference/replicate, same source commit, expected 256-row tensor shapes, identical initial model SHA and RNG SHA, receipt self-hashes, and NPZ stage-by-stage byte hashes. It compares the normalized CPU/BLAS profiles after removing **only** the selected OpenBLAS core name, rejecting any other change.
- Then report per stage: number of float32 bit patterns that differ, max and mean absolute numeric delta, first unequal stage. Require input-feature bytes to be identical. Save both original receipt JSONs, both tensor NPZs and independent derived report JSON even if the investigation is negative. A single CI job is the budget limit for this stage.
- Unit tests (new synthetic-only) must cover hash integrity, exact dimensions, runtime feature/seed rejection, wrong selected core and detected first stage. No held-out historical Phase 2G samples, Phase 2U neural outcomes, actual epochs, backward propagation, gradient or Adam update.

## Predefined interpretation

1. **Haswell vs Nehalem selected, stages differ:** evidence that OpenBLAS kernel dispatch is sufficient to change at least one tensor's bits in this *synthetic, first-forward* workload using original-version numerical software. Even if subsequent differences are tiny, they are measurable; quantify rather than reinterpret them as a cryptographic break.
2. **Haswell vs Nehalem selected, all 7 stages identical:** no evidence of numerical kernel sensitivity in this exact sampled forward pass. It **does not** rule out sensitivity during gradients/Adam or other data shapes.
3. **Forced core not actually selected, runtime differs beyond kernel, or data/init mismatch:** mark invalid/inconclusive; never fabricate comparable results.
4. **Any wrong artifact bytes/receipt SHA, unregistered seed, missing stage or tensor shape:** fail closed and preserve original CI logs and recoverable outputs.

There is **no predeclared statistical significance threshold** for this engineering check. It is a deterministic single-sample numerical contrast, not a population claim. It does not establish the prior Phase 2G historical cause, the adaptive-vs-fixed mechanism or the security of a cipher.

## Permanent research limits

No training is invoked, no scientific frozen artifacts modified, no Phase 2U 96-run experiment authorized, and no changes merged to `main`. This remains a draft contribution to [PR #161](https://github.com/Chatnoir01/ml/pull/161), stacked on earlier research branches. The official Phase 2G verdict remains `phase2g_adaptive_coevolution_not_supported`.

**Retention:** export the complete original GitHub Actions JSON and NPZ before artifact expiry; GitHub green checks alone are not original-source proof.
