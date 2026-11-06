# Phase 2G — deterministic checkpoint-zero input reconstruction, WITHOUT new neural training
**Date 2026-11-06. Original research source: `030652489dd489a4705bbf64a12d7e6fa01ca03b`, frozen run 35572084785. This is a forensic reconstruction and a research-design audit, not historical weight-byte evidence.**

## New source-backed result: 180 original S-Boxes recovered from their seeds

The original 2026-09-21 source `src/adversarial_sbox/phase2g_experiment.py` delegates checkpoint-0 initial population creation to `phase1m._initial_population`, which calls `evolution.random_sbox`. Its exact deterministic recipe is `random.Random(evolution_seed)` and 20 unique shuffled permutations of `range(256)`. The S-Box fingerprint is `sha3_256(bytes(sbox))`, and Phase 2G's curriculum is those 20 S-Boxes sorted lexicographically by that fingerprint.

A **separate read-only script** `phase2g_checkpoint0_reconstruct_inputs_20261106.py` reproduced this historical generator. For all **nine original evolution seeds**, independent checks against *both original A/F ZIP archives* succeeded:

- **9/9** complete 20-candidate initial population SHA256 match exact historical `initial_population_digest_sha256`.
- **9/9** exact original **ordered 20 SHA3-256 candidate fingerprints** match `population_before_fingerprints`.
- **9/9** canonical sorted 20 curriculum fingerprints and SHA256 match `curriculum_fingerprints` and `curriculum_digest_sha256` from both A/F source records.
- **180 of 180** candidate S-Box values can consequently be reconstructed with their 256 raw byte values; these values are checked against 180 preserved S-Box fingerprints in each arm. The reconstruction **does not infer** those bytes merely from a hash; it runs the exact seeded original source generator and independently checks the output against original hashes.

The original A/F ZIP's canonical `scientific_payload_sha256` is checked for each seed before using its reported population, curriculum and model-seed references. The original source ZIPs remain unchanged.

## New source-based reconstruction of the original checkpoint-0 candidate inputs

The original `phase2g_shared_model.build_shared_training_splits` calls `datasets.generate_balanced_pairs` with each S-Box, its original T seed, input difference (1 or 256), and `ToySPN` 4-round fixed key schedule. The generator is pure-Python deterministic and its original recipe, pair order and train/validation/test split boundaries (280/60/60 pairs per S-Box) were reproduced exactly in the separate script.

Across all checkpoint-0 combinations:

| Registered dimension | Values |
|---|---:|
| Original evolution seeds | **9** |
| Original differences | **2**: 1, 256 |
| Original per-difference T/M seed replicates | **8** |
| Total distinct *declared training input cells* | **144** |
| Reconstructed fixed curricula | **9 × 20 = 180 S-Boxes** |
| For each cell, train/validation/test pairs | **5,600 / 1,200 / 1,200** |
| All reconstructed dataset grids | **144/144** |
| Original source M/T declarations verified against both arms | **144/144** |

Every grid has a reproducible **SHA3-256** checksum over the ordered original-format `(left ciphertext 32-bit, right ciphertext 32-bit, label byte)` tuples, separately for train, validation and test. They are in the read-only reconstruction CSV.

**Critical evidence boundary:** the original September Phase 2G archives did **NOT** contain raw training pairs nor their independently recorded dataset hashes. Therefore these 144 SHA3 digests are **NEW RECONSTRUCTED input hashes**, not historical input hashes authenticated against stored September bytes. The experiment executed Python **3.12.14**, while the read-only reconstruction script is currently executed with Python **3.13**; the observed initial-population SHA3/SHA matches fully establish the permutation construction but **do not independently prove every original September dataset byte matched**. Original untrained neural parameter bytes are also absent and were not regenerated here. This experiment does **not** run a model, calculate gradients, or modify model weights.

## New methodological finding: per-S-Box sampled labels are deliberately coupled by reused dataset seed

For each original dataset T seed and input difference, the implementation calls `random.Random(seed)` **afresh for each of the 20 curriculum S-Boxes**. Cipher encryption does not consume that RNG. Thus all 20 S-Boxes are fed the **same randomly drawn underlying plaintext pairs and identical 400-item label sequence** (though the resulting ciphertext values differ by S-Box). The same 280/60/60 split indices and label order are reused across those S-Boxes.

Read-only tests on **all 144 reconstructed checkpoint-0 grids** verified the **20/20 per-S-Box label sequences match exactly** within each grid. The ordered label distributions depend on the T seed, but not on the S-Box values or the evolution seed for the same T/difference. For example:

| Original T seed | Positive labels per S-Box in train (of 280) | Validation (of 60) | Test (of 60) |
|---:|---:|---:|---:|
| 776003 | 152 | 22 | 26 |
| 776017 | 140 | 29 | 31 |
| 776031 | 137 | 32 | 31 |
| 776043 | 140 | 35 | 25 |
| 776059 | 143 | 21 | 36 |
| 776071 | 135 | 31 | 34 |
| 776083 | 133 | 35 | 32 |
| 776097 | 141 | 32 | 27 |

Although each **400-sample S-Box sub-dataset is exactly balanced 200/200 before shuffling**, the train/validation/test slices have fixed seed-dependent label counts, identical across the 20 S-Boxes. This does **not** demonstrate test contamination or an invalid AUC. It does establish that the individual S-Box sub-datasets **do not have independently drawn plaintext examples or independently shuffled label orders**; treating the 20 slices as fully independently sampled replicas would overstate design independence. This is a methodological limitation for later interpretation, NOT a cause identified for the historical A/F state-hash mismatch, since A and F shared the same seed and curriculum at generation 0.

## State-receipt comparison remains intact

Original historical checkpoint 0 still has **144** paired A/F trained-state SHA comparisons: **80 identical, 64 differing** (all 16 copies in each of evolution seeds 726049, 726061, 726073, 726113). All 144 reconstructed input-grid entries list the corresponding original trained model SHA for A and F; same declared T/M seeds and same reconstructed input bytes are used when interpreting a pair. **No neural training was executed** in this audit.

The arm identifier itself is passed to `train_shared_checkpoint_model` for metadata but is **NOT an argument to `_fit_shared_model_state_bytes`**, which receives only the input samples and model seed. Thus the original frozen model-training mathematical path contains no direct arm flag branch. This is **code-path evidence**, not proof of identical actual historical CPU/BLAS dispatch or source input bytes. Historical aggregate `training_receipt_sha256` *does* include `arm`, as separately established in [PHASE2G_HISTORICAL_ARM_RECEIPT_FORENSICS_20261106.md](PHASE2G_HISTORICAL_ARM_RECEIPT_FORENSICS_20261106.md). Arm-conditioned receipt inequality is NOT trained-state inequality.

## Three open scientific limits before any causal claim

1. Exact **original September 2026 effective CPU/BLAS core, SIMD, threads and numerical-library runtime** not recorded in the old hosted job logs, although they record Ubuntu 24.04 image release `ubuntu24/20260907.300`, Python 3.12.14 and NumPy 2.5.3. Same image does not imply same CPU.
2. Raw original dataset and **initial model-weight array bytes** were not archived. Deterministically reconstructed input data here are now inspectable and falsifiable against source, but cannot be retroactively authenticated against missing original raw bytes.
3. Historical **trained-state hashes alone** cannot quantify model-vector numerical magnitude or cryptographic performance impact. Modern Phase 2R synthetic BLAS controls show a plausible float32 mechanism, not historical 64-state causation.

**Frozen scientific verdict remains `phase2g_adaptive_coevolution_not_supported`.** No original Phase2G run or frozen scientific receipt was altered, zero Phase2U neural fits, zero new model fits in this reconstruction, no merge to `main`.

## Reproducible evidence and rerun instructions

- Original 39 source ZIP archival bundle: `phase2g_all_39_original_evidence_20261105.zip` (39 nested source ZIP CRC verified) and 18 extracted A/F original ZIPs.
- Read-only historical arm receipt audit: `phase2g_historical_af_provenance_verifier_20261106.py`, detailed JSON audit and CSV.
- **New read-only deterministic reconstruction:** `phase2g_checkpoint0_reconstruct_inputs_20261106.py` (Python standard library; no NumPy, no neural package, no model training), JSON containing all **180 raw S-Box byte sequences** and 144 grid receipts, plus compact CSV of split hashes and original A/F model-state receipt mappings.
- Run with the user's locally preserved original ZIPs: `python phase2g_checkpoint0_reconstruct_inputs_20261106.py --folder /path/to/extracted_original_zips`. The input folder must include `phase2g-A-726011.zip`, `phase2g-F-726011.zip`, etc. Original source code does not need to be executed to generate neural training, and the frozen experiment remains untouched.
- This provenance reconstruction was built and evaluated within the conversation working container. Complete evidence ZIP and exact SHA-256 checksum supplied separately in the PR and conversation; **a durable user-controlled external scientific backup is not yet verified**.
