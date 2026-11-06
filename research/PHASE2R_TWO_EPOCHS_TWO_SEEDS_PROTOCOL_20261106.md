# Phase 2R-E2S2 — two epochs, two registered seeds, same-host BLAS contrast
**Pre-execution protocol registered 2026-11-06. Separate DRAFT branch stacked on #165. NO Phase 2G frozen experiment is overwritten; NO Phase 2U model is trained.**

## Pre-existing evidence and specific question

The independently re-audited first synthetic epoch from [run 42156027912](https://github.com/Chatnoir01/ml/actions/runs/42156027912) showed **771/1,825 float32 parameters** differed bitwise after 22 original Adam steps when the numerical backend alone was forced to **Haswell** vs **Nehalem**. However, on the same 1,200-item synthetic test split, both networks showed exactly the same tie-aware AUC **0.6318184389140271**, and a post-hoc audit found no changes in test prediction order. Relative model weight-vector L2 difference after one epoch was only **4.416324867426168e-8**. Thus '42.25% changed bits' is NOT a large effect in weight magnitude or functional outcome.

**New, bounded question:** are the parameter-bit differences still present after **two**, not 32, epochs, and are the resulting same-seed fixed synthetic test AUC and predicted probability bytes stable for **two independently preregistered original Phase2G checkpoint-zero seed replicates**?

## Fixed, independent variables and two pre-registered cells

One GitHub-hosted Ubuntu 24.04 x86-64 machine, **two fresh sequential Python processes**, `OPENBLAS_CORETYPE=HASWELL` vs `OPENBLAS_CORETYPE=NEHALEM`; actual `threadpoolctl` kernels must match; host CPU/SIMD and all numerical library metadata otherwise identical. **CPython 3.12.14**, **NumPy 2.5.3**, **threadpoolctl 3.6.0**, with `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=VECLIB_MAXIMUM_THREADS=1` set before import.

The exact **frozen synthetic** 20-S-Box Phase 2R fixture `phase2r-synthetic-v1`, existing original `build_shared_training_splits`, first checkpoint, input difference **1**. Exactly the original first **two** checkpoint-zero replicate seed pairs, chosen before execution:

| Replicate | Dataset seed T | Model seed M |
|---:|---:|---:|
| 0 | **776003** | **786009** |
| 1 | **776017** | **786021** |

Each cell has precisely **5,600 train, 1,200 validation, 1,200 test samples**. Network: original 12→48→24→1 float32 byte_tanh_mlp with six trainable tensors, original weight initialization, BCE gradient with weight decay and original `_adam_update`. **Two epochs only**: a new original seeded `rng.permutation(5600)` **before each epoch**, 21 minibatches of 256 plus one final minibatch of **224**, **44 total updates per replica per kernel**. Adam update counter increments continuously **1→44**; moments and variances are never reset at the epoch boundary. No third epoch, model selection, synthetic test score tuning, or retraining.

**Work budget:** exactly **2 registered seeds × 2 epochs × 2 kernel processes = 8 per-epoch model portions = 176 bounded Adam minibatch updates**, not any of Phase 2U's sealed 96 full neural trainings.

## Stop gates and originally preserved output

- First epoch's **22×32** intermediate-stage tensors in the new code are checked by the original frozen `phase2r_first_epoch.epoch_step` on the *same first-epoch exact state* for each seed/kernel. Any difference fails closed. At the end of the first epoch, the original source AUC is recomputed on unchanged synthetic test records; previous replicate 0 first-epoch AUC is an external contextual benchmark, not a substitute for this internal fidelity gate.
- Every paired seed and kernel must have exactly matching dataset split SHA-256s, initialized model-state SHA, initial and post-permutation RNG SHA, 2 full permutation SHA digests, exact SHA of every original minibatch's 22 selected indices **per epoch**. Index lists must be complete permutations of the same 5,600 training rows each epoch; no duplicates within an epoch. Original model architecture, float32 and scalar b3 state must be preserved.
- Original source evidence NPZ preserves **6 updated weights after EVERY one of 44 updates**, both epoch-end **6 first moments and 6 second moments**, and fixed **1,200 test probabilities and their exact labels after EACH epoch**, for each of 2 seeds. Expected **584 exact source float32 tensor SHA-256 receipts per kernel**, **1,168 original tensor SHA-256 digests** across two kernel processes, with versioned stage/shape/dtype-bound hashing and no unreported or extra source arrays. The six updated parameters plus Adam moment and variance tensors use exact original shapes (including scalar b3). The NPZ captures **no historical secret or Phase 2U data**.
- All source raw NPZ and JSON receipts, SHA256SUMS, preregistered source/git/runtime metadata and independent derived comparison JSON are retained even on failure. Third comparison process recomputes ALL original SHA receipts and BOTH kernels' `_auc_from_scores` and `_advantage` directly from saved `float32` test arrays; checks source commit and same BLAS metadata except the deliberately forced OpenBLAS kernel. No unvalidated/unsigned user-supplied receipts may produce a scientific verdict.
- **Primary observations:** for each seed separately, each Adam step's count of bitwise-unequal weight elements and relative/mean/max absolute model-weight difference; checkpoint after steps **22** and **44**; at each epoch-end 1200-row probability bit differences and signed AUC difference. No significance test for **N=2**.
- **Secondary exploratory:** rank/tie changes or classification flips may be computed *after* outcome only if labelled post-hoc; not part of preregistered decision.
- A null AUC difference is not evidence of an identical parameter vector or a secure cipher. A non-zero synthetic AUC difference is not proof of a meaningful cryptographic security difference or historical Phase 2G causal mechanism.
- Do **not** generalize from 2 seeds to the historical nine seed-pair model, to real cryptanalysis, or to adaptive evolution. No claimed sample-size power, p-value, or universality.

## Fail closed, provenance, and boundaries

- Failing input SHA, repeated or missing indices, incorrect runtime, seed drift, wrong scalar float shape, wrong actual selected kernel, missing NPZ, invalid source receipt, first-epoch mathematical parity failure, or any new/proposed model-training steps beyond the registered **44** produce **invalid experiment**, never an inferred result.
- **Frozen historical Phase 2G verdict remains `phase2g_adaptive_coevolution_not_supported`.** Its 64/144 trained checkpoint-zero A/F hash mismatches are not causally explained without the archived 2026-09 runner BLAS profiles and original initial bytes.
- **Zero Phase 2U 96-run experiments** are run; no original sealed Phase 2U ranking/receipts altered; no `main` merge; separate DRAFT PR stacked on #165.
- Only independently recomputed source SHA, NPZ float32 bytes and CI run evidence can support findings. GitHub artifact retention is temporary and must be followed by a durable user-owned backup verified by SHA-256.

No specific outcome is predicted. Any future change to seeds, two-epoch bound, numerical constants or acceptance criteria requires a new dated protocol/branch and explicit scientific rationale rather than silently revising this preregistration.
