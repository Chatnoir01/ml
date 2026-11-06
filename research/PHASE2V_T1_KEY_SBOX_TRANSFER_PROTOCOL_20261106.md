# Phase 2V-T1 — pre-registered key and unseen-S-Box transfer for classical ToySPN distinguishers
**Protocol committed 2026-11-06 BEFORE any T1 transfer-outcome calculation. DRAFT research only.**

## Scientific question

The earlier Phase 2V experiment on all 144 reconstructed Phase 2G checkpoint-zero ToySPN cells found median ciphertext-only ROC AUC around 0.69 using a smoothed four-byte XOR histogram. **Does that elementary signal survive a controlled switch to previously unseen S-Boxes and an independently generated fixed round-key schedule?** The purpose is to FALSIFY over-generalization of an in-distribution result, not to claim a new cryptographic result.

This is a source-verified read-only CLASSICAL baseline experiment; no neural models will be initialized, fitted, scored or unblinded; original Phase 2G verdict and prospective Phase 2U remain frozen.

## Fixed data and sample-selection design

- Exactly **36** checkpoint-zero source-reconstructed cells: all original 9 evolution seeds `(726011,726023,726037,726049,726061,726073,726087,726099,726113)` × both original input differences `(1,256)` × exactly TWO selected original T-seeds `(776003,776097)` (first and last from the original ordered registered seed panel, selected before outcomes).
- Each original 20-S-Box curriculum is sorted lexicographically by SHA3-256 fingerprint, strictly verifying its SHA-256 against the original frozen 2026-09 A/F source evidence via PR #169's pinned reconstructed curriculum. **First 15 sorted S-Boxes** are TRAINING-domain/seen S-Boxes; **last 5 sorted S-Boxes** are entirely held-out S-Boxes. This split is fixed by fingerprint order, not by classical performance.
- Each original candidate uses the same pure-Python original `random.Random(T_seed)` draw/400-pair labeling/split protocol (280 train / 60 validation / 60 test). Source original fixed 5-word 4-round key schedule: `(0x243F6A88,0x85A308D3,0x13198A2E,0x03707344,0xA4093822)`.
- A second, **fully fixed independent public 5-word key schedule**, with each unsigned 32-bit key generated as `int.from_bytes(sha256(b"phase2v-t1-key-schedule-20261106-v1|" + str(i).encode()).digest()[:4],"big")` for `i=0..4`. The schedule is not optimized/selected based on metrics and is not meant to be secret.
- The alternate-key observations are generated using the exact same original **plaintext pair draws, original T seed, labels and permutation** as for the source keys, with only the round key schedule swapped. This is a *paired* counterfactual key intervention, **NOT an independent test corpus or key-family generalization guarantee**.

## Four fully prespecified evaluation arms per cell

Fit exactly ONE four-byte naive-Bayes XOR difference table to **only the original-key train pairs from first 15 S-Boxes** (4,200 training examples, 15×280), using per-byte positive/negative frequency counts with fixed alpha = 1 and log likelihood-ratio. Do not fit to held-out S-Boxes, alternate-key ciphertexts, validation data or any test labels. Evaluate unchanged scoring table plus two UNFITTED fixed-direction baselines on:

1. **Seen S-Boxes, original key**: 15×60 = **900** original-key TEST pairs;
2. **Unseen S-Boxes, original key**: 5×60 = **300** original-key TEST pairs;
3. **Seen S-Boxes, alternate key**: 15×60 = **900** counterfactual-key TEST pairs;
4. **Unseen S-Boxes, alternate key**: 5×60 = **300** counterfactual-key TEST pairs.

Fixed scoring methods (higher score indicates `label=1`, except where below sign is fixed):
- Constant score 0.0 (AUC 0.5);
- Unfitted negative ciphertext XOR Hamming weight `-popcount(C0 XOR C1)`;
- Unfitted count of zero bytes in `C0 XOR C1`;
- Trained-once **source-key-seen-SBox** four-position Laplace-1 naive-Bayes XOR difference log-likelihood ratio.

Use original tie-aware ROC AUC with no post-hoc direction optimization, no AUC inversion and no p-values. All 36×4×4 AUC values included; do not choose a favorable cell/arm afterward. Compare each cell's AUC to its own original-key-seen baseline. Report descriptive medians and ranges **clustered by evolution seed**; 36 cells share many keys/labels/SBoxes and are not 36 statistically independent samples.

## Hard controls, provenance and error gates

- Recheck each source A/F-signed evolution/S-Box curriculum SHA, 20/20 S-Box uniqueness/permutation, and source original-key full 20-SBox train, validation, test SHA3 from the previous reconstruction manifest (PR #169). This authenticates reconstructed curricula but **does not supply original archived 2026-09 dataset bytes**, which were never saved.
- Reconstruct original-key 20×400 pairs first, then recompute alternate-key 20×400 pairs with the **same random draw stream**. Compare both labels and plaintext-source pairing by a standalone plaintext-sequence probe (or source-stable hash of original pair draws) and verify all 20 per-S-Box label sequences still agree. Reject mismatches.
- Enforce 4,200 training samples, 900/300 seen/unseen test samples for each key, binary labels present in all partitions, fixed SHA3 of each output sample panel. Check no exact ciphertext (or full ciphertext pair) overlap between the source-key training panel and each evaluation panel; any overlap invalidates that cell unless explicitly disclosed and separately analyzed.
- All 36 cells must pass; missing/extra data, stage/test leakage, undeclared keys, AUC NaNs, drift from historical source hashes or selection of any extra seed fail closed.
- **No optimization based on test scores**, no new classical/neural model after viewing data, no repeated alternate-key cherry-picking. A new intervention requires a distinct prospectively registered protocol.
- For a scientific interpretation, distinguish a rank difference from model-weight byte changes (this experiment has **zero neural training**). AUC changes under alternate keys do not establish generalization across independent keys or security against real-world cryptanalysis.

## Precommitted endpoints, limitations and next hypotheses

**Primary**: for the trained source histogram, paired changes in AUC for each cell between seen/original versus unseen/original and seen/alternate, plus the absolute AUC on **unseen/alternate**. Report medians and per-evolution-seed grouped medians; no hypothesis-test p-value and no after-the-fact threshold.

**Secondary**: the same four-domain AUC values for unfitted Hamming-weight and zero-byte statistics; their performance under changes in keys/S-Boxes helps identify whether signal originates in the ToySPN round structure rather than a fitted lookup table. Original constant null must remain exactly 0.5.

**Interpretation**: high cross-key AUC on a fixed alternate schedule is one controlled transfer observation, **not** a universal cryptographic theorem. Poor cross-key/SBox transfer would demonstrate a distributional weakness of the baseline and motivate properly blinded fresh-key/new-plaintext tests. Any eventual matched neural-vs-classical experiment must share the exact same splits, scores and test key/SBox isolation, and MUST be separately approved and registered. It is not authorized by this protocol.

No original Phase2G negative verdict changes, zero Phase2U sealed 96-run neural fits, no `main` merge. Preserve raw source, full per-cell scores, predeclared key schedule and source/protocol SHAs in durable evidence.
