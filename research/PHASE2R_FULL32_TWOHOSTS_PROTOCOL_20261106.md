# Phase 2R-F32H2 — 32 original epochs on two last-unused seeds, repeated on two hosted runners
**PRE-EXECUTION PROTOCOL 2026-11-06. DRAFT branch stacked on #167. Synthetic numerical reproducibility only.**

## Previously seen results and why these NEW samples

The earlier synthetic Phase 2R studies explored Phase 2G seed indices 0–5. In the independent four-new-seed study r2–r5, **0/4 fresh seeds** exhibited a changed exact test AUC after epoch two even while many updated parameter float32 bit patterns differed; that is not a powered general result. The September historical Phase 2G 64/144 trained-state A/F hash mismatches **have no archived raw initial weights, raw dataset bytes or CPU/BLAS profile**, so their root cause remains unproven.

This prospectively registered study uses the **last TWO original seed pairs previously unused by the synthetic Phase 2R experiments**:

| Original first-checkpoint replicate | Dataset seed T | Model seed M |
|---:|---:|---:|
| **6** | **776083** | **786087** |
| **7** | **776097** | **786101** |

Selection is by fixed original index, **not** by any predicted finding. These are not unseen in the original Phase 2G historical study, and they are not a statistical random sample. They are new ONLY relative to the Phase 2R numerical sensitivity branch.

## Preregistered interventions, original computation and finite budget

- **Exactly TWO independently scheduled GitHub Actions `ubuntu-24.04` runner jobs** (host samples `1` and `2`); GitHub does not prove they are different physical silicon/microarchitecture. Do **not** claim independent hardware vendor/microarchitecture unless measured. Each job performs one fresh **same-host** paired contrast: (1) a process with `OPENBLAS_CORETYPE=HASWELL` and (2) a process with `OPENBLAS_CORETYPE=NEHALEM`. Each must report actual library core name in `threadpoolctl`, single observed thread and equal normalized host CPU/SIMD, BLAS library version and all other observed numerical profile attributes *within that job*. Cross-job profiles may differ; never force strict cross-job bytewise comparability when they do.
- Pin **Python 3.12.14 / NumPy 2.5.3 / threadpoolctl 3.6.0**, and all 5 thread-limit variables `=1` before NumPy import. Frozen Phase 2R synthetic source fixture `phase2r-synthetic-v1` 20 S-boxes, original `build_shared_training_splits` train/validation/test split sizes `5600/1200/1200`, difference=1, original 12→48→24→1 float32 network, 1,825 model float32 parameters, original seeded initialization, BCE derivatives with weight decay and **actual source `_adam_update`**.
- **Exactly 32 historical epochs × 22 consecutive original minibatches** per seed/kernel, each epoch with one new historical seeded `rng.permutation(5600)`; batch geometry `21×256 + 224`. Adam global step increments from 1 through **704**, carrying forward ALL first and second moments without reset; no early stopping, new hyperparameter, seed sweep, extra minibatch, or changing model selection based on test AUC.
- **Hard parity:** all 22 steps of epoch 1 per seed/kernel must bit-match the previously frozen `phase2r_first_epoch.epoch_step` stages and weights/moments; every step of epoch 2 must also match the prior `phase2r_four_fresh_seeds.bounded_historical_update` for steps 23–44 (which is independent code). Source parity failure terminates the experiment.
- Two seeds × two kernels × 704 updates × two hosts = **5,632** bounded gradient/Adam minibatch updates; this is a complete **32-epoch synthetic Phase 2R neural fit per cell** (8 complete synthetic fits in 2 jobs), **not** the original historical Phase 2G training evidence and **not ANY of Phase 2U's 96 sealed prospective neural fits**.
- Preserve the **exact two 5,600-index permutations' contents per epoch per seed** in sealed source JSON (64 permutations per kernel). For each, verify all 22 batch hashes against contiguous index slices and no repeated indices. Dataset/initial weight/RNG seeds and state hashes must be identical between kernels in each host.
- Save the original **6 model parameters, 6 Adam first moments and 6 second moments at each of 32 epoch ends** to exact `float32` NPZ, including scalar b3: **2 seeds × 32 epochs × 18 arrays = 1,152 source arrays per kernel**. Only after **epochs 1, 2, 4, 8, 16 and 32** (six fixed checkpoints) additionally save **test predictions and fixed test labels**: 2×6×2 = 24 arrays. **Total 1,176 source tensor SHA256 per kernel, 2,352 per host, 4,704 across both hosts**; original exact NPZ must support independent recomputation.
- Test predictions computed **once at each fixed checkpoint**, with original sigmoid and tie-aware `_auc_from_scores`. This is observation only; fixed test data never enter gradient updates. Save 1,200 float32 predictions and labels per checkpoint; verify exact recalculated tie-aware AUC from original bytes.
- One same-host comparison report per independent job computes each checkpoint's: (i) number and fraction of bitwise-different weight values, (ii) max/mean absolute differences, and relative vector L2 norm, (iii) probability-bit differences, exact signed AUC difference and any positive–negative order/tie relation transitions; no parameters tuned based on outcomes.
- Cross-host comparison is **descriptive** and limited: verify the two original Git SHA/fixture/T/M seeds, record each host's observed CPU/SIMD/BLAS normalized profile and whether strict cross-host equivalence happens. Under differing profiles report **CROSS_HOST_NUMERICAL_PROFILES_DIFFER**; the two independent **within-host** conclusions remain valid if their own gates pass. Do NOT assert that GitHub supplies different physical hardware or that identical host outcomes constitute a hardware-independent theorem.

## Primary/secondary fixed endpoints, interpretation and stop rule

**Primary (two last-unused seed pairs, after epoch 32):**
1. For each seed on each host, the exact tie-aware difference `test_auc_Haswell - test_auc_Nehalem` (including zero), the number of changed positive/negative score order/tie relations and number of changed float32 predicted scores.
2. Bitwise-different final model parameter count out of 1,825 and relative L2 parameter distance. Distinguish changed float bit representation from meaningful change in model function.
3. Whether each seed's within-host AUC delta agrees **numerically across both host jobs**, without treating those runs as four independent seed samples. State actual CPU/BLAS profiles.

**Prespecified secondary:** same measurements at epochs **1,2,4,8,16**; changes within a seed may be non-monotonic, so no assertion of monotonic amplification without inspection of every recorded epoch-end count. Count test pair order transitions for any AUC discrepancy. No multiple-comparison p-value for six repeated checkpoint observations, N=2 seeds or two hosted jobs.

**Invalid:** incorrect or unreported actual core, drift in split fingerprints, initial weights/ RNG or complete permutations, wrong CPU/BLAS equality within host, original 22+22 fidelity check failure, wrong number of epochs or source artifacts, any missing/extra source NPZ tensor, altered source digest, or incomplete exact AUC recomputation. Fail closed rather than labeling partial evidence a finding.

**No automatic expansion**, reruns, new seed selection or changes to protocol after seeing results. One originally scheduled CI attempt per job; an infrastructure-only retry must be reported explicitly with independent evidence.

## Scientific firewall

The experiment is an engineering *numerical reproducibility* control on a fixed **synthetic** S-box corpus. It cannot establish a novel cryptographic cipher, security strength, practical cryptanalytic advantage, proof of historical Phase 2G cause, or reverse the original **`phase2g_adaptive_coevolution_not_supported`** verdict. Original Phase2G and Phase2U frozen records and the private `main` branch remain untouched. The original **96 prospective Phase 2U neural trainings remain unexecuted**. Every PR remains DRAFT pending source-ZIP verification and independent review. Source artifacts in GitHub Actions expire; preserve and independently checksum the original ZIPs before publication or reuse.

Neither AUC stability nor instability in this synthetic study, without pre-specified threat model, constitutes security evidence.
