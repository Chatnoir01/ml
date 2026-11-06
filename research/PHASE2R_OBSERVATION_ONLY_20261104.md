# Phase 2R — observation-only checkpoint-zero instrumentation (2026-11-04)

**Status: ENGINEERING DRAFT, synthetic unit tests only. No Phase 2R experiment, neural training, scientific authorization, merge, deployment, or Phase 2U unblinding.**

## Purpose
Record the actual six `float32` initialized tensors and the NumPy Generator state, immediately after model initialization and **before** any training step or permutation. Return SHA-256 digests only. The code calls the original Phase-2G final-state serializer to ensure identical model-state encoding without changing that code or the historic frozen result.

## New work
- `src/adversarial_sbox/phase2r_observation.py`: explicit six-tensor input validation; finite float32-only values; original serializer reuse; JSON-canonical RNG state read without drawing random numbers; before/after RNG-state equality; hash-only record.
- `tests/test_phase2r_observation.py`: repeated digest equality, RNG not consumed, original arrays unchanged, single-weight mutation, RNG-only mutation, missing tensor, float64 coercion rejection and NaN rejection.
- `.github/workflows/phase2r-observation-only.yml`: isolated Python 3.10–3.12 synthetic tests without running model training.

## Scientific boundaries
1. The instrumentation is **not yet inserted into the actual Phase 2G trainer**; nothing in the historical execution is modified.
2. No actual model initialization, final-weight or dataset comparisons have been executed by this PR; green CI proves only helper behavior on fixtures.
3. The observed RNG state is a hash of `bit_generator.state`, not a proof of full process-wide randomness or hardware/runtime determinism.
4. This is not an attested environment manifest and does not establish the true cause of the 4/9 Phase-2G A/F differences.
5. Full Phase 2R still needs reviewed, frozen model initialization capture, exact dependency/BLAS/thread manifest, complete 16-cell two-process input controls, authorized A1/A2/F1/F2 runs and external raw-evidence retention.
6. Never alter Phase 2G's preregistered seeds, verdict, artifacts, terminal selection, or Phase 2U's frozen ranking.

## Future non-mutating integration proposal
Once independently reviewed, an *additional Phase 2R-only trainer wrapper* may capture these digests at initialization. The helper must not introduce a new RNG draw or change training order. Compare golden final-state SHA-256 with and without instrumentation **before** allowing any scientific run. No such integration is authorized or included in this PR.

**Merge disposition: keep DRAFT, no automatic promotion; this workstream is stacked on Phase 2R #152 and earlier Phase 2H/2G dependencies.**
