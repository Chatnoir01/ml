# Phase 2V — classical controls for neural differential distinguishers (2026-11-06)

**PROSPECTIVE RECORD CREATED BEFORE CLASSICAL BASELINE CALCULATIONS.** This separate DRAFT branch builds upon #169's checkpoint-0 reconstructed historical S-Box curricula. Read-only exploratory analysis; it performs **ZERO neural training**, no Phase 2U unblinding, no historical rerun, and no merge to main.

## Scientific question and the correct null hypothesis

Could elementary statistics of the *ciphertext XOR difference* distinguish the real-pair class from the random-pair class on the exact synthetic ToySPN Phase 2G checkpoint-0 data? If yes, observed neural AUC above chance alone is not evidence of any new cryptanalytic structure unless it improves upon appropriate classical baselines and survives held-out S-Boxes, held-out keys and independent sampling.

Existing neural differential cryptanalysis (e.g. Gohr 2019 on Speck) already combines neural distinguishers and comparisons against classical difference-distribution methods. A ToySPN-specific neural AUC is not itself a cryptographic innovation.

## Fixed sample panel (no adaptive selection)

Exactly **all 144** original checkpoint-0 reconstructed data cells, using nine frozen evolution seeds (726011, 726023, 726037, 726049, 726061, 726073, 726087, 726099, 726113), two input differences `1,256`, and eight original training T seeds (776003,776017,776031,776043,776059,776071,776083,776097). Regenerate each of the 20 ordered 256-byte permutation S-Boxes from the original Python `random.Random(evolution_seed)` and the original exact ToySPN fixed 4-round key sequence; enforce their original published S-Box hashes and the freshly reconstructed per-cell **5,600/1,200/1,200** train/validation/test split hashes (the hashes are newly reconstructed, **not** September original archived input bytes). The canonical A/F original checkpoint-0 curriculum identity is required. **No seed, input difference or S-Box cell can be omitted after looking at an outcome.**

## Fixed baselines (no tuning)

Scores use ONLY `(ciphertext_left, ciphertext_right)` and never true plaintext or secret key values at scoring time.

1. **Null constant**: score 0.0 for all test pairs. Exactly AUC 0.5 if both classes present.
2. **Unfitted XOR Hamming weight**: `-bit_count(ciphertext_left ^ ciphertext_right)` (higher means predicted true differential pair). Predeclare the *negative* sign; do not select the direction after observing the result.
3. **Unfitted equal-byte count**: sum of `1` for the four byte positions of the ciphertext XOR whose value is zero. Predeclare positive sign.
4. **Classic count-based naive Bayes / bytewise output difference histogram**: from only the **5,600 training examples** within the same historical checkpoint-0 cell, estimate four class-conditioned distributions of XOR-difference bytes using additive-one Laplace pseudocount and compute `score=Σ_byte_index log [(count_{pos,byte}+1)/(N_pos+256) / ((count_{neg,byte}+1)/(N_neg+256))]`. Fixed alpha=1, all four positions, no hyperparameter tuning, no neural optimization. Evaluate on the **1,200 held-out test examples**. This is a weak **empirical baseline**, not the theoretically optimal Markov differential distinguisher.
5. **Negative control:** fit the exact same count-based Bayes to the 5,600 training pairs after *permuting their binary labels*, with `random.Random(0xD15EA5E ^ evolution_seed ^ T_seed ^ difference)`. Evaluate on original held-out labels. Do NOT train/test on permuted test labels. This is a single precommitted random negative control, not a statistical null distribution.

All AUC computed by **exact tie-aware average ranks**; report signed AUC and neural-style `2*abs(AUC-0.5)` separately, never maximize baseline sign or model choice after seeing outcomes. The true labels are **never** entered as a feature. The Bayes table is fit on train only. Keep validation unused.

## Provenance and dependence

Recompute exact original-format per-cell SHA3-256 of all train/validation/test pairs and verify against the previous reconstruction manifest; enforce every cell's two original arms had the same declared curriculum/T/M seeds. All 20 S-Boxes of each cell share the same plaintext sample schedule and shuffled label order by construction; this induces cluster dependence. **The 144 cells are NOT 144 IID cryptographic experiments.** Report per-evolution-seed grouped summaries, and at most descriptive full-panel distributions, without p-values or an IID confidence interval.

Additional read-only data-integrity analysis: count exact ciphertext blocks and ciphertext pairs shared between train and test *across different S-Boxes* inside each mixture (and train vs validation). The original generator guarantees disjoint blocks **within** an individual S-Box sub-dataset, not necessarily across distinct S-Boxes. Check actual empirical collisions before making leakage assertions; a collision does NOT by itself establish label leakage or explain neural results.

## Interpretation / stop rule

- If classical baseline test AUC materially exceeds 0.5, this is **evidence that the source's synthetic pair classification contains ciphertext-only signal detectable without a neural network**, not a new cryptographic discovery.
- If a negative control also yields a large AUC in a single cell, do not infer chance violations; diagnose controls and evaluate larger null panels under a NEW registered protocol, not by post-hoc filtering.
- If neural scores are compared, require **matched original held-out cells, same keys, S-Box, difference, pair sampling and training budget**. Existing aggregate historical Phase 2G AUC from a DIFFERENT model/training context is not an apples-to-apples superiority claim.
- Future distinct experiments need held-out **round keys**, held-out **entire S-Boxes**, independent plaintext-draw seeds per S-Box, matched DDT/LAT classical baselines, and sealed prospective neural outcomes. Do not silently retrofit these novel test conditions to old Phase 2G or Phase 2U records.
- Original Phase 2G negative verdict `phase2g_adaptive_coevolution_not_supported` unchanged. No Phase 2U 96 neural fits, no new cryptographic primitive/attack claim, and this PR remains DRAFT.

## Reproducibility

A standard-library-only read-only verifier, run on the reconstructed original data script and previously validated manifest, will emit all **144 source-hash-bound cells**, CSV and JSON with original algorithm identifiers and SHA256. If a split hash, source S-Box fingerprint, geometry or original A/F receipt differs, fail closed with no scientific conclusion. GitHub source/CI must be separately validated; no training is authorized by a passing baseline test.
