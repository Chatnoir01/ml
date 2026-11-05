# Phase 2R — original independent-runner receipt audit and runtime-fingerprint correction (2026-11-05)

**Read-only audit of REAL original GitHub CI receipts. This document does not train a model, revise Phase 2G or authorize the prospective four-run Phase 2R experiment.**

## Source run and observed byte result

- [Original GitHub Actions run 42088664144](https://github.com/Chatnoir01/ml/actions/runs/42088664144), head commit `e75310a9c32764cc4d072a9bb507d1580bc2e22b`.
- Original independent A receipt artifact **13442884785**, created 2026-11-05 18:57 UTC; original independent F artifact **13445836723**, created 19:09 UTC; original pairwise audit artifact **13443764911** created 19:12 UTC.
- Both original jobs ran on Ubuntu 24.04.5, same image version `20261101.360.1`, Python **3.12.14**, NumPy **2.5.3**, on separate Azure runners (A: centralus; F: northcentralus), with five numerical thread-limit environment variables explicitly **1**.
- Each source JSON contains exactly **16** training-free cells, using the pinned synthetic Phase 2R 20-S-Box fixture. Each generated 5,600 train, 1,200 validation and 1,200 test ciphertext pairs and independently constructed initialized network weights and pre-shuffle RNG state.
- Original completed audit: **16/16 dataset split SHA-256 tuples equal, 16/16 initialization SHA-256 equal, 16/16 pre-shuffle NumPy RNG-state SHA-256 equal**. The completed read-only measurement establishes exact pretraining byte agreement in this sampled two-worker synthetic control. NO neural network training or evolution occurred.
- **IMPORTANT unexpected finding:** the original `numpy_runtime_report_sha256` values are **different**:
  - A: `420bc5b33d82349dd6934b99ca353e238e277f8dac03294167fcf6c883c1f8af`
  - F: `9316300a1b9c6f121f562badc598e79a50b9e84657482aed18b521135d408023`
  The original summary says `numpy_runtime_report_hashes_match=false` but still reports `PASS_PRETRAINING_TWO_RUNNER_BYTE_INVARIANCE`. **This discrepancy must not be hidden.**

## Why hashing raw `numpy.show_runtime()` is not a reliable comparability test

NumPy 2.5.3's `show_runtime()` serializes a `platform.uname()` record, including its **host-specific `node` hostname**. Thus two otherwise comparable runner processes can have different *raw* report digests solely because the VM names differ. The raw digest is not adequate to prove either runtime equivalence **or runtime inequivalence**. Source documentation: https://fossies.org/dox/numpy-2.5.3/namespacenumpy_1_1lib_1_1__utils__impl.html and https://numpy.org/devdocs/reference/generated/numpy.show_runtime.html.

## Prospective corrected comparator (new experiment protocol, NOT retroactive rewrite)

A new source-level function `stable_numpy_runtime_profile()` records only the numerical properties relevant to this controlled workload:
- Python and NumPy versions, operating system name and machine architecture;
- **CPU SIMD** baseline, available dispatch features and supported feature set;
- runtime **BLAS provider, version, threading layer, BLAS CPU architecture and observed numerical thread count** obtained using pinned `threadpoolctl==3.6.0`;
- excludes transient runner hostname, filesystem paths, mutable IDs, job timestamps and volatile `uname()` fields.

The canonical JSON SHA-256 of the structured runtime profile is checked against its content and compared between jobs. **Unlike a raw `show_runtime` hash, this normalized profile controls the comparability verdict.** If the normalized profiles differ, the new read-only verifier returns `INCOMPARABLE_NUMERICAL_RUNTIME_PROFILE_MISMATCH` even if all initial bytes matched. If the normalized profiles match AND all 16 cells' data/weights/RNG hashes match, it reports `PASS_PRETRAINING_TWO_RUNNER_BYTE_INVARIANCE`. A new job explicitly logs that conclusion; all outcomes are preserved, including negative or incomparable results.

The original run's **raw A/F numerical profile was not recorded**, and cannot be reconstructed from only a SHA-256 string. Therefore **we do not retroactively certify that the original two workers had the same CPU or BLAS capabilities**. The old run remains byte-identical at the observed pretraining boundary, with hardware/runtime comparability uncertain.

## Research firewall

- No original Phase 2G results altered; its negative scientific outcome remains `phase2g_adaptive_coevolution_not_supported`.
- A green exact-input/initial-weight comparison does **not** establish deterministic numerical training, identical final model weights, the cause of the historical 64/144 discrepancies, a stronger S-Box, or cryptographic security.
- A future genuine controlled training run and the 96-run prospective Phase 2U experiment remain unauthorized.
- The originally downloaded A/F/audit ZIPs are stored as conversation attachments; expiry date for the original CI three artifacts is **2026-12-05**. Preserve them durably and verify hashes before that date.
