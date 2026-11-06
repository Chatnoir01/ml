# Phase 2R-F4 — four NEW seeds, two epochs: original source independently re-audited (2026-11-06)

**Status:** Source-backed synthetic numerical experiment complete. No original Phase 2G historical-run recreation or Phase 2U neural training. This report is NOT an independent scientific validation of a cryptographic claim.

## Preregistration and scope

[Original prospective protocol](PHASE2R_FOUR_FRESH_SEEDS_PROTOCOL_20261106.md) was frozen BEFORE the new outcomes at commit `3f1b0d31a90e6105a5eee113cc6cfd528eb2e6a5`. The only **fresh** cohort comprises the original sequential seeds **2, 3, 4, 5** with dataset T seeds (776031, 776043, 776059, 776071) and model M seeds (786033, 786047, 786061, 786073). The previously seen two-epoch results for replicates 0/1 are NOT included in the fresh N=4 denominator.

The original source GitHub Actions [run 42224805145](https://github.com/Chatnoir01/ml/actions/runs/42224805145) succeeded, with original test + simulation checkout SHA `cae24da9114b746927cc2d62ed9a201da37e11b3`. Two sequential processes on one runner with **actual Haswell** and **Nehalem** forced OpenBLAS, one BLAS thread, original Python **3.12.14** and NumPy **2.5.3**. Four fixture-only seed replicas; exactly 44 original Adam updates per seed/kernel across two epochs; 1,200 fixed synthetic test rows at each epoch end. All first-epoch steps checked against frozen original first-epoch code. NO sealed Phase 2U candidate, original Phase 2G hidden artifacts, full 32-epoch fit or model-selection exercise.

## Original-source audit evidence

Official original GitHub Actions artifact **13504673342**, expiring approximately 2026-12-06. Downloaded and re-audited completely:

- Original source ZIP SHA-256: **`187ad620f363520eb4fc2329770081dcc7d966a4f6952eab3c5431f25274e1f7`**; ZIP CRC valid.
- Original ZIP member `SOURCE_SHA256SUMS.txt`: **5/5 matched**.
- Both canonical original receipt SHA256 and original numeric report canonical SHA256: **3/3 matched**.
- All **2,336/2,336** original exact float32 tensor bytes were checked with versioned, shape-bound digest (1,168 per kernel) including zero-dimensional scalar b3; all 4×2×5600 stored permutation contents were independently verified, along with all 4×2×22 minibatch slice hashes. Each dataset, initial weight, RNG and normalized CPU/BLAS profile matched across the two subprocesses except chosen core.
- All 4×44 weight differences, relative parameter vector distances and all **eight synthetic test AUC values independently recomputed** from the *original* source NPZ and compared to the GitHub derived report.
- Independent verifier SHA256 **`fe44e5688dd438b0b5f52f606587c18607897f56335e260d70f06b0897401463`**; independent audit JSON SHA256 **`46a5acdfe34dc27edb6ab4f8c4d9098f74e650fe1f6457cbd4c5970d6ad626d9`**. Full conversation evidence archive `phase2r_four_fresh_seeds_verified_evidence_20261106.zip`, 3,133,678 bytes, SHA256 **`bc5f7c53663fe4c6f50f6c2b4215485b38d248209646d567c36899c4796199f0`**. Original GitHub ZIP and read-only verifier are included with checksums. This is **not yet a verified user-owned independent durable backup**.

A transparent numerical-verification note: the independent version of NumPy/BLAS produced last-bit rounding differences of order `1e-23` when recomputing some *aggregate relative L2 norms* around `1e-8`. The verifier accepts these derived norm scalars only within `rel_tol=5e-13`, `abs_tol=1e-19`; original tensor SHA, changed element counts, minibatch identities and exact tie-aware AUC are compared **without any tolerance**. This is a correction to the external verification method, not a modification of original source evidence or a relaxed scientific endpoint.

## Prespecified per-seed numerical outcomes

**Model weight array length: 1,825 float32 scalars.** "Different weights" means **different float32 bit patterns**, not necessarily different neural behaviour or security.

| Fresh model M seed | Epoch | Different parameter float values / 1,825 | Relative L2 distance of parameter vectors | Haswell AUC | Nehalem AUC | Signed AUC delta H−N | Different test probability floats / 1200 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 786033 (replicate 2) | 1 | 813 | 5.0454049900127165e-8 | 0.6726140155728587 | 0.6726140155728587 | **0** | 270 |
| 786033 | **2** | **1025** | **6.618906206112633e-8** | 0.677472191323693 | 0.677472191323693 | **0** | 256 |
| 786047 (replicate 3) | 1 | 784 | 4.6852987743136424e-8 | 0.66552 | 0.66552 | **0** | 287 |
| 786047 | **2** | **1020** | **6.484423153551703e-8** | 0.6631685714285714 | 0.6631685714285714 | **0** | 282 |
| 786061 (replicate 4) | 1 | 798 | 4.9789266252393295e-8 | 0.6442824074074074 | 0.6442824074074074 | **0** | 287 |
| 786061 | **2** | **1045** | **6.556219414558513e-8** | 0.6404311342592592 | 0.6404311342592592 | **0** | 282 |
| 786073 (replicate 5) | 1 | 776 | 4.716443935841616e-8 | 0.6191063348416289 | 0.6191063348416289 | **0** | 288 |
| 786073 | **2** | **997** | **6.543424511089886e-8** | 0.6213122171945701 | 0.6213122171945701 | **0** | 277 |

**Primary prespecified endpoint**: **0/4 new seeds** have a changed exact tie-aware AUC after epoch 2. The formal two-sided 95% Clopper–Pearson binomial interval on 0/4 is **[0, 0.6023646356164747]**, but these **fixed consecutive seed identifiers are NOT an iid random sample**. Therefore this is at most an illustrative descriptive binomial interval, not reliable population generalization or a powered hypothesis-test result.

**Secondary**: At epoch 1, 0/4 also have an AUC difference; all four show higher counts of bitwise-different parameter values after epoch 2 than after epoch 1, but the relative L2 magnitudes remain of order `10^-8`. Fixed test probabilities differed by only 256–288 of the 1,200 float32 bit patterns across the eight seed/epoch cases.

**Prespecified mechanistic positive–negative pair check**: the independent auditor computed all cross-class score ordering/tie relations. **Zero changed positive–negative relations in each of the eight comparisons.** Therefore both kernels' exact AUC equality is supported by their underlying class-order/tie ranking, not an accidental cancellation of positive and negative AUC shifts.

## Interpretation and limitations

This is a genuine independent **fresh-seed synthetic replication** of backend-dependent *weight byte divergence* coexisting with **stable test AUC** after 22 and 44 Adam steps. The effect sizes of the parameter-vector changes are extremely small. The prior replicate 1 in #166 had one first-epoch positive/negative score tie change and a small transient AUC delta; this is separate earlier **seen** evidence, not included in the N=4 fresh denominator or used to pick these seeds.

Still **NOT PROVEN**: that old September 2026 Phase 2G's **64/144** trained checkpoint-zero A/F model-state SHA discrepancies were caused by OpenBLAS CPU dispatch; its original CPU/BLAS profiles, raw untrained weights and original input bytes were not recorded. Neither a full 32-epoch model fit nor real-world cryptanalysis or security findings arise from this two-epoch N=4 study. Sealed Phase 2U 96 prospective neural trainings remain **0 executed**.

The historical frozen negative verdict **`phase2g_adaptive_coevolution_not_supported` remains unchanged**. Source PR #167 stays DRAFT, stacked on #166. No merge into `main`. At the initial scientific report preparation, the dedicated workflow and benchmark passed, but the general Phase 0 Python matrix was still completing. Recheck that CI independently; do not infer a full green matrix from this report.

**Evidence retention:** Archive the downloaded and independently checked ZIP outside temporary Actions before its 2026-12-06 advertised expiry; GitHub's 30-day retention is not permanent.
