# Phase 2U — original 12-S-Box sealed predictor / prospective neural receipt contract
**Dated 2026-11-05 — ENGINEERING-ONLY DRAFT. NO scientific execution authorized.**

This is a NEW protocol version after the 2T-v1 *classical source-generation failure*. Its evaluator MUST NOT be used as a relabelled Phase 2T-v1 experiment. The previous 2T design and negative source outcome remain frozen and unchanged. This branch creates **no new neural results, no classical source changes, no new candidate selection, and no claims of novelty**.

## Hard factual anchors (do not rewrite)
- The canonical Phase 2U 19-source-seed panel was established on 2026-11-02 with 12 selected exact-classical-metric S-Boxes and 6,460 classical evaluations, **0 neural labels**.
- Original source panel canonical SHA-256: `512dd21d01617944047fd4e6f6ec2ae09daa68bc76d808837527a384148914ef`.
- Original classical-prediction SHA-256: `cd4bfbc9736ced13bdcf95c06f156d4244fbbdde65b05c51fb4e7958a21a30f4`.
- [Original immutable-before-neural prediction run 41539098859](https://github.com/Chatnoir01/ml/actions/runs/41539098859); [precommitted ranking](PHASE2U_CLASSICAL_PREDICTION_FROZEN_20261102.md). This implementation **only reads** the original `phase2u_predict.verify_prediction_receipt` schema.
- The 12 new candidates have distinct global DDT spectra from one another and from 8 earlier observed S-Boxes, sufficient to rule out pairwise extended-affine equivalence in this set. This does NOT prove independent generation, general security or statistical sample independence; see [EA-spectrum report](PHASE2U_EA_INEQUIVALENCE_AUDIT.md).
- Phase 2R's historic checkpoint-zero A/F hash discrepancy (four of nine original paired seeds) is unresolved despite the new observation-only helper tests [PR #161](https://github.com/Chatnoir01/ml/pull/161).

## 1. Identified format blocker
The old `phase2t_evaluate.py` requires a `phase2t_fresh_12_neural_only` outcome and a `phase2t_predict` receipt with `receipt_sha256`. Phase 2U's actual source-bound frozen receipt instead exposes `prediction_receipt_sha256` and distinct source-panel provenance. Relabelling the old evaluator would silently lose or distort that binding.

The new `phase2u_neural_contract.py` separately checks the original exact frozen Phase 2U digest, original source-panel canonical digest, and all 96 candidate × delta × replicate outcome identities. A passing validator proves only supplied **metadata consistency**, not honesty or provenance authenticity of its claimed values.

**Engineering strengthening (2026-11-05, before real 2U labels):** the same runner commit, dependency-lock SHA and runtime-manifest SHA are now required for all 96 rows, rather than merely requiring each field to look like a hash. The original `byte_tanh_mlp` initializes weights exclusively from a registered `model_seed`; the initial model tensor SHA must therefore match for all 24 candidate/difference cells sharing one of the four replicate model seeds. Each cell must have three distinct train/validation/test split hashes. The new constraints form part of this draft **future** protocol fingerprint, not any historical frozen Phase 2U prediction or Phase 2G execution.

Cross-run hash equality is a necessary comparability condition, **not proof** that the bytes accurately describe the execution. Genuine runtime attestation, record-level sample split inspection, original model serialization and an independent recomputation remain open gates.

## 2. Proposed prospective confirmatory geometry (inherited, requires review)

These inputs were preregistered **before any Phase 2T/2U neural outcomes** in `PHASE2T_PROSPECTIVE_PREDICTION_PROTOCOL.md`. The Phase 2U source population is a separate version, so they require distinct owner/scientific approval rather than automatic transplantation:

- 12 fixed candidate S-Boxes; input differences `1` and `256`; 4 registered paired dataset/model replicates; **12 × 2 × 4 = 96** neural trainings.
- Fresh dataset seeds: **930101, 930113, 930127, 930139**. Fresh model seeds: **940101, 940113, 940127, 940139**.
- Historical `byte_tanh_mlp`, 32-bit four-round ToySPN, same original fixed public key schedule, agreed train/validation/test disjointness; **no changed cryptographic primitive or hidden test access**.
- Per-candidate neural score: mean of eight `2 × abs(test_AUC − 0.5)` results; corresponding shuffled-label null has the same absolute-AUC transform. The statistic is computed across **12 candidates, not 96 independent samples**.
- One primary positive Spearman rank correlation with classical scores: **rho ≥ 0.60**, one-sided seeded Monte-Carlo permutation **19,999** draws with seed **950101** and `p < 0.05`, PLUS global mean neural-minus-null margin **≥ 0.02**. Descriptive 2,000-resample bootstrap CI seed **950113**. These are preexisting 2T thresholds; **not** claimed as proven scientifically appropriate for Phase 2U without review.
- No post-hoc change to candidate panel, feature, signs, ranking, analysis direction, seeds, primary threshold, number of replicas, held-out key/data or missing-cell exclusions.

## 3. Prerequisites still incomplete
1. Phase 2R must establish actual dataset and model-initialization byte provenance for the intended training runner, not just synthetic no-training helper tests; frozen dependency lock, reproducible code version, verified CPU/BLAS/thread controls and serialized initial/final model states.
2. The prospective Phase 2U neural runner must be separately designed and locked. Its exact train/validation/test record counts, seed namespace, class-label shuffling method, optimizer order and feature extractor must match the intended historical neural model. This document is **not a neural runner**.
3. The statistical versioning and 12-candidate power/uncertainty justification need independent review. Any amended design is a separately dated **new protocol** before the first new label.
4. Independent review of a complete original 12-S-Box prediction receipt (from original source ZIP), and of the 96 per-run metadata hashes. The new source panel hash and prediction hash must be checked against actual archived bytes; do not trust metadata-only reports.
5. Preserve source ZIP artifacts before their advertised GitHub Actions expiration. A missing original archive cannot be replaced by hashes alone.
6. An explicit owner-controlled, dated **prospective execution authorization** is required prior to running any neural training. A green CI or merging this branch is NOT authorization.

## 4. Implementation and security boundaries
`src/adversarial_sbox/phase2u_neural_contract.py` is a read-only future-result validator and arithmetic calculator. It does **not** train networks, read private held-out labels, generate source candidates or overwrite receipts. It rejects:
- wrong frozen predictor or source panel;
- missing, duplicated or extra rows out of the 12 × 2 × 4 geometry;
- changed T/M seeds, invalid scalar AUC, malformed dataset/init/final/RNG/runtime/dependency hashes or missing 40-hex runner commit;
- drift in the already defined statistical implementation parameters.

The statistical output always has `scientific_validation_status=UNAUTHENTICATED_SUPPLIED_RECEIPTS_NOT_SCIENTIFIC_VERDICT` and `authorizes_neural_training=false`, even when mock rows satisfy mathematical thresholds. This tool cannot by itself certify real experiments, attack resistance, original cryptography or causality.

`tests/test_phase2u_neural_contract.py` runs **synthetic-only** fixtures and mocks the real frozen-prediction verifier to test the outer schema. The actual evaluator does NOT mock that verifier. The dedicated CI must pass on Python 3.10, 3.11 and 3.12 before any engineering-complete label.

## 5. Research novelty comparison (prior work already exists)
- Gohr, CRYPTO 2019, neural differential cryptanalysis of round-reduced SPECK: https://eprint.iacr.org/2019/037
- Neumann, Gohr & Leander (2022), *An Assessment of Differential-Neural Distinguishers*: https://research.patrickneumann.eu/publication/2022-11-07-diff-neural
- *Approximating neural distinguishers using differential-linear imbalance* (2024): https://doi.org/10.1007/s11227-024-06375-4
- *Keeping classical distinguisher and neural distinguisher in balance* (2024): https://doi.org/10.1016/j.jisa.2024.103816

Therefore neither neural distinguishers, classical-neural statistical relationships nor S-Box evolutionary design are novel concepts of this project. The **candidate contribution** is a transparent *forward prediction* on a fixed, classically matched but EA-distinct panel, backed by explicitly separated source selection and an independent neural test. Even a successful correlation is NOT a novel cipher or universal law. A failure remains publishable as a negative observation under the exact design.

**No training, merge, deployment, held-out opening or original result mutation is initiated by this research-only branch.**
