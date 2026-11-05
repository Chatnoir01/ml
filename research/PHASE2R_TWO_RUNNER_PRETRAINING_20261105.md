# Phase 2R — independent two-runner *pretraining* byte check (2026-11-05)

**Research instrumentation only — NO neural training, evolutionary search, held-out data, or changes to frozen Phase 2G outputs.** This is a new prospective engineering control, not a reenactment of the historical 4/9 anomaly.

## Why this control exists

The independent re-audit of all original [Phase 2G A/F frozen artifact ZIPs](PHASE2R_CHECKPOINT0_FROZEN_ARTIFACT_REAUDIT_20261105.md) established **64 of 144 mismatched checkpoint-zero trained-model state hashes**, concentrated in four evolution seeds with every one of those seeds' 16 A/F cell hashes different. Declared curriculum and seed identity match, but original *input bytes* and checkpoint-zero *initialized model bytes* were not preserved, so the causal point of divergence is unknown.

The actual original Phase 2G training job pinned **CPython 3.12.14 and NumPy 2.5.3**, on ubuntu-24.04. Original job logs lack a guaranteed numerical thread/BLAS/CPU manifest.

## New no-training design

[Workflow `phase2r-two-runner-pretraining.yml`](../.github/workflows/phase2r-two-runner-pretraining.yml) runs two **independent GitHub hosted CI jobs**, labeled **A** and **F**. The letters are *metadata only*: in contrast to the old adaptive-versus-fixed scientific arms, both new jobs do exactly the same pretraining computation. They are not full A1/A2/F1/F2 training experiments.

Each job:
1. Checks out the PR code and installs Python **3.12.14** and NumPy **2.5.3**, and sets five numeric thread environment variables to **1** *before Python starts*.
2. Loads the separately pinned, **synthetic** 20-S-Box Phase 2R fixture (`phase2r-synthetic-v1`, SHA-256 `09e94da031992240d857a139768445c042cb712abf866f15084300a4a267e8a2`).
3. Uses the actual `phase2g_shared_model.build_shared_training_splits` and canonical `phase2r_serialization.hash_pair_split` for all **2 input differences × 8 original checkpoint-zero replicate seeds**. Each model receives 5,600 training, 1,200 validation and 1,200 test ciphertext pairs.
4. Independently mirrors **exactly the original pre-epoch NumPy initialization recipe** (initial weights only), using original `BYTE_HIDDEN_1`, `BYTE_HIDDEN_2` and `TRAINING_MODEL_BASE_SEEDS`; calls `observe_checkpoint_zero` using the existing Phase 2G wire serializer. No epoch shuffling, optimizer updates, model fit or inference occurs.
5. Emits only 16 sets of SHA-256 input/initialization/RNG fingerprints, seed identities, fixed Python/NumPy/thread information and diagnostic NumPy runtime SHA; contains no candidate bytes, training pairs, trained weights or secrets. Original final-model code is not altered.

The third job downloads the two independent output receipts, checks their receipt hashes and exact grid identities, and compares all 16 tuples of **train/validation/test digests, initial model-state hashes, and RNG-state hashes**. If any of the 16 differs, it reports **FAIL_PRETRAINING_BYTES_DIVERGE** and fails CI. A passing result only means these inputs and initialized states are identical **under this fixture and two sampled runners**.

Ten synthetically generated tamper/seed/receipt tests support the verifier; the CI test lane is Python 3.12.14 NumPy 2.5.3, distinct from the broader existing observation-only 3.10/3.11/3.12 matrix.

## Scientific interpretation

**If all pass:** the concrete **new** synthetic pretraining data and initialization bytes appear invariant across those two jobs under fixed versions/threads. This makes hypotheses about the *later training/numerical stage* worth investigating, but **does not rule out** a historical data-input discrepancy, original runner-specific CPU differences, model-training non-determinism, or differences from the actual old population.

**If any fail:** the independent report identifies exactly whether the split generator, initialized model or RNG state first disagrees at the pretraining boundary in the new fixture, warranting further isolated measurement without rewriting frozen old outcomes.

The original 2G **negative verdict remains locked** `phase2g_adaptive_coevolution_not_supported`. Even a green pretraining CI run does **not** validate full model-state equivalence, cryptographic strength, future 2U neural generalization, nor any scientific claim of originality.

This file and workflow are **not** an authorization to start the preregistered four-run Phase 2R actual training experiment or the 96-training Phase 2U neural campaign. Additional owner authorization, dependency/CPU/BLAS review, true runtime byte attestation, and exactly registered final-model tests remain required.

## Machine evidence

Once workflow finishes, link its actual exact-head run here via a separate *new* dated record; do not edit this protocol to manufacture a CI result. Preserve the two source JSONs and comparison JSON outside transient Actions artifacts before they expire.
