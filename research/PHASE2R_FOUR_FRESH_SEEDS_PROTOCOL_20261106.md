# Phase 2R-F4 — four NEW original-seed replicates, two epochs, fixed OpenBLAS intervention
**Registered 2026-11-06 BEFORE executing new study. Separate DRAFT branch stacked on #166; same synthetic fixture, no historic scientific rerun, no Phase 2U.**

## Why this exact sample was chosen before observing its outcomes

Previous synthetic two-epoch study #166 already observed replicates **0 and 1**. They are **NOT included** in the fresh replication cohort because their outcomes are known (including one first-epoch AUC tie transition); mixing them into a claimed independent confirmation would be misleading.

This next study uses precisely **FOUR NEW original checkpoint-zero replicates 2, 3, 4 and 5, consecutive in the previously fixed Phase 2G seed block**. These are chosen strictly by original numeric index, **not** by their future measured outcomes, S-Box metrics, expected likelihood of a tie, or hardware. The remaining original replicates 6 and 7 are **not sampled** here. Exactly ONE source GitHub Actions attempt per committed preregistered protocol, except an infrastructure-failure rerun separately documented without changing analysis thresholds. No optional repeat because results look surprising.

| Fresh replicate | Historical dataset T seed | Historical model M seed |
|---:|---:|---:|
| **2** | **776031** | **786033** |
| **3** | **776043** | **786047** |
| **4** | **776059** | **786061** |
| **5** | **776071** | **786073** |

## Fixed work, environment and stop rule

- One GitHub Ubuntu 24.04 x86_64 host, Python **3.12.14**, NumPy **2.5.3**, threadpoolctl **3.6.0**; five BLAS/NumExpr/OMP thread environment controls fixed to **1**. Two sequential fresh Python processes on the same host, forced **OPENBLAS_CORETYPE=HASWELL** vs **NEHALEM**, with actual selected cores and otherwise identical normalized CPU SIMD/BLAS library metadata verified.
- Frozen **synthetic Phase 2R 20-SBox fixture**, historical `build_shared_training_splits`, difference **1**, exact 5600/1200/1200 pair split for each of the four preregistered T seeds. Historical 12→48→24→1 float32 architecture, 1825 trainable floats, original initialized weights, BCE gradients, weight decay, `_adam_update` and state persistence.
- Exactly **TWO** consecutive historical epochs per seed/kernel: an independent original `rng.permutation(5600)` before each epoch, original **21×256 + 224** final training batch, Adam global step **1..44** without resetting moments. Total **4 fresh replicates × 2 BLAS kernels × 44 minibatches = 352 bounded Adam updates**. No full 32-epoch fitting, extra sample, hyperparameter tuning, early stopping, or phase2U neural fit. Halt after 44.
- **Hard mathematical fidelity gate:** at *every one* of the 22 first-epoch steps of each seed/kernel, compare source forward/gradient/Adam to the earlier frozen `phase2r_first_epoch.epoch_step` 32-stage implementation, exact float32 byte digests, and check all six parameter/moment/variance tensors. No new shared experiment evidence until all parity gates pass.
- Record exact full 5600-element permutation for both epochs and each seed, plus exact 22 batch SHA256s for each. Verify each full permutation is a bijection, its SHA matches the recorded explicit array, and each original batch SHA matches its exact contiguous permutation slice. Must agree between Haswell and Nehalem, alongside input split SHA, initialized state and RNG.
- Save **6 updated parameter tensors after every one of 44 steps**, plus **6 first moments + 6 second moments + 1,200 synthetic test probabilities + 1,200 synthetic test labels at BOTH epoch ends**, for each of FOUR seed replicates and each BLAS kernel. Thus **4 × (44×6 + 2×14) = 1,168** original float32 array SHA receipts **per kernel**, **2,336** receipts across both. NPZ source values and JSON canonical SHA256 verified independently; even scalar `b3` retains original zero-dimensional shape.
- Recompute `_auc_from_scores` and `_advantage` **from each original 1,200-item prediction NPZ**, separately for each seed/epoch/core. No test dataset is used for learning. Per-step group measures: count of unequal float32 parameter elements, maximum and mean absolute parameter difference and relative L2 full-vector distance.
- Preserve original artifact zip, original source receipts, raw stage NPZ, original summary JSON and SHA256SUMS. Green CI is not independent source integrity proof. Must explicitly inspect original source ZIP before claiming an outcome.

## Endpoints and analysis fixed before results

- **Primary endpoint:** for each of the four **new** seed pairs at **epoch 2 / step 44**, record (i) binary indicator `test_auc_Haswell != test_auc_Nehalem` (ties count as equal), (ii) signed and absolute numeric difference of exact tie-aware AUC, and (iii) number and magnitude of changed parameter floats with relative model L2 distance. Count the number of AUC differences across the FOUR fresh seeds; provide exact two-sided 95% binomial (Clopper–Pearson) confidence interval for that observed fraction as an **exploratory descriptive interval**, NOT a powered significance test. The N=4 interval will be wide.
- **Secondary, preregistered:** repeat the same AUC and changed-weight records after epoch 1; describe **per-seed step-22 to step-44** change (persist/grow/decrease) without claiming monotonic trend across all steps unless the complete trace actually shows it. Record fraction of different predicted float32 values and per-epoch max absolute prediction delta.
- **Mechanistic rank/tie audit, prespecified for fresh cohort:** if a nonzero AUC delta occurs, enumerate positive-negative test example pairs whose score relation (lower/tied/higher) changed and confirm the sum of tie-aware 0.5 pair contributions exactly accounts for the AUC delta. No classification threshold effects or cryptographic claims are predeclared.
- **Do not combine** the previously observed replicate 0/1 results with fresh replicate 2–5 results to claim a confirmatory N=6 p-value. Older results can be displayed separately as contextual controls with this selection caveat.
- No seed extension, loss/effect threshold tuning, CI reruns after looking at the outcomes, or promoted cryptographic-security conclusion. An absent AUC difference does NOT imply byte-identical weights; a tiny AUC difference caused by a tie does NOT prove a useful crypto property.

## Scientific boundary

No retained 2026-09 original Phase 2G CPU/BLAS profiles, original untrained weight bytes or original input-array bytes exist in the frozen evidence. Therefore this prospective **N=4 synthetic kernel intervention cannot establish the root cause of the original 64/144 differing trained-state SHA256s**, cannot rescue the original negative adaptive-coevolution verdict `phase2g_adaptive_coevolution_not_supported`, and does not authorize Phase 2U's sealed 96 neural trainings. All prior reports, original artifacts and main stay unchanged. This is a new independent DRAFT branch with explicit scope, not a merge.
