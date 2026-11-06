# Phase 2V-T4 — locked retrospective DDT-prediction audit and analytical no-diffusion lemma
**Analysis plan committed 2026-11-06 before T4 statistical calculations.** This is NOT a prospective test of new outcomes: all Phase 2V-T3 measurements already exist and were inspected. Therefore any DDT→AUC relationship is **retrospective/exploratory**, must not be called independent confirmation, and cannot change the frozen Phase 2G negative verdict or authorize Phase 2U's sealed 96 neural fits.

## Why this study is useful

Phase 2V-T3 established on a toy 32-bit four-byte SPN that the original rotate-left-11 bit mixing causes a large loss of empirical positive-vs-negative ciphertext-pair distinguishability by round 5, while the zero-rotation byte-separable ablation retains perfect measured AUC. We now separate:
1. A **general mathematical invariant** for arbitrary per-byte bijective S-Boxes and arbitrary round keys **without mixing**;
2. A genuinely quantified, *possibly negative*, predictive check: does the coarse 8×8 differential uniformity statistic `mean(max_{dx!=0,dy} DDT[dx,dy])` measured over the **20** S-Boxes of a curriculum predict how strongly a trained histogram continues to distinguish pairs after 5 rounds **with mixing**?

The latter is NOT assumed to succeed. Classical DDT maxima alone omit round topology and specific differential trails, so failure is scientifically informative.

## Immutable source panel and exact pre-registered analysis

Inputs MUST be byte-exact:
- `phase2v_t3_round_diffusion_audit_20261106.json` SHA256 `bd9f73539e99d5df40c53876a91da5fc61b23711da553107200ea3f24c366ea0`;
- `phase2v_t3_round_diffusion_324_panels_20261106.csv` SHA256 `5d426f3d6eb1e8a528cff3c083d95d991578e4342ef973c1db5db9420086cf6b`;
- original source `phase2g_checkpoint0_forensics_reconstruction_verified_20261106.zip` SHA256 `6f6b6fbe68a123ad8bf302b4ba3a80f069e9d8ab64188121c28e631a66444845`.
- Original T3 preregistered experiment `1c98f905ead28a17a8b3011b9c9052d44da3487a`; source panel is exactly **9 evolution seeds ×2 differences (1,256) × only T seed 776003 × unseen test domain × original 11-bit mixing × rounds 4 and 5**. The 9 evolution-seed curricula are 726011,726023,726037,726049,726061,726073,726087,726099,726113. Nine independent *group labels* DO NOT imply independent data sampling.
- Verify T3 `receipt_sha256` by canonical JSON, CSV panel identity and strict AUC numeric equality, **324 registered rows**, original seed panel, 20 DDT entries / evolution seed with 10≤integer DDT≤256, nine groups, the T3 source fingerprint and zero original neural fits. Any mismatch -> INVALID.
- **One fixed coarse predictor per evolution-seed group:** arithmetic MEAN of original 20 S-Box maximum DDT counts (include both 15 source-seen and five held-out boxes; this uses known public S-Box properties, not test labels).
- **One fixed primary outcome per evolution-seed group:** arithmetic MEAN of the TWO original `auc_histogram` values, at original rotation 11, round 5, unseen S-Boxes, one each for input differences 1 and 256. No sign inversion.
- Fixed secondary outcomes: same mean at round 4, and paired difference `mean(R4 AUC) - mean(R5 AUC)`. Each has only nine training units; never train on 18 rows as independent duplicates.
- **Prediction benchmark: leave-one-evolution-seed-group-out (LOSO; nine folds).** Baseline forecasts training-eight target MEAN. One-feature model forecasts from **ordinary least-squares intercept + slope** fit on those same eight groups' `mean_max_DDT`; no tuning, regularizer, hyperparameter sweep or cherry-picking. Implement OLS from simple scalar sums; if the eight training x values are identical within a fold, fall back to intercept-only prediction with explicit flag. Scores: LOSO MAE and RMSE for both predictors, `LOSO_relative_squared_error = 1 - SSE(model)/SSE(baseline)`; report all nine held-out actual/predicted values and signed slopes of each train fold. Do not rename a negative value as a positive effect. One exact deterministic calculation; no p-values or confidence intervals (nine small correlated groups, data previously examined).
- Fixed descriptive Pearson correlation (and Spearman with average ranks for ties) of the nine `mean_max_DDT` group predictors vs each group target. This is exploratory and **not** a second proof of prediction. Report observed x range and limited between-group variation explicitly.
- **No permutation p-test, no regularization optimization, no selective outcome exclusion, no secret-key claim.** No additional neural training, no Phase2U prospective panel access.

## Pre-specified mathematical lemma for rotation=0

For a state of four 8-bit bytes, suppose EACH round consists only of per-byte XOR key and a bijective 8-bit substitution `S` applied independently to each byte, with optional final per-byte whitening, and **NO inter-byte diffusion or other cross-byte operation**. If two distinct plaintext states agree on three of four byte positions and differ at only one position, then after **ANY finite number of such rounds**:
- the ciphertexts agree in the same three positions;
- they differ in the remaining position because composition of bijections on a byte is bijective.
- Hence the 32-bit output XOR has EXACTLY three zero bytes for every positive pair generated with an input XOR contained in one byte; this holds for any keys, any bijective S-Box, any number of rounds. **It does not guarantee that negative pairs cannot also have exactly three zero-byte XOR positions.**

For a truly uniformly random permutation over distinct 32-bit outputs, the probability that two fixed distinct plaintexts encrypt to outputs differing in **exactly one byte** is exactly `(4×255)/(2^32−1) = 1020/4294967295 ≈ 2.3749×10^-7`. This is an exact two-output combinatorial property for an ideal permutation, not a claim about any finite sample or production cipher.

**Independent deterministic lemma check** (to be run after plan is committed): choose a small fixed toy bijective S-Box `S(x)=(73*x+41) mod 256` (73 odd, hence bijection); two fixed independent five-word key schedules (historical source and SHA256-derived alternate from T1); rounds 1,2,3,4,5,7; both one-byte input differences 1 and 256; 512 fixed plaintexts from `random.Random(20261106)`, using same deterministic fixed vector for all conditions. Verify the output-XOR zero-byte count = 3 and that the only differing byte matches the one input-active byte for all **2 × 6 × 2 × 512 = 12,288** conditions. Also test one deliberately **non-bijective constant S** as a negative control: byte-wise equality still holds in inactive bytes, but the changed byte need not stay different; this rejects a proof that silently omits bijectivity.
This is mathematical unit checking rather than new neural/scientific dataset construction.

## Interpretation and boundaries

If LOSO improvement is absent or negative, conclude only that the **single scalar mean DDT maximum** is not demonstrated predictive in this nine-curriculum observational panel, not that *all* DDT-related features or full differential trails fail. If positive, this remains exploratory and vulnerable to the narrow nine-source panel and earlier inspection; future **independent unseen S-Box/curriculum data and keys** must be fixed in a NEW protocol before observing outcomes. The byte-locality lemma is an established structural property of products of independent bijections, not a novel cryptographic theorem.

Do not claim a new secure cipher, new real-world attack, historical Phase 2G BLAS causation, neural advantage or Phase 2U results. Keep new PR DRAFT stacked on #173 and do not merge main.
