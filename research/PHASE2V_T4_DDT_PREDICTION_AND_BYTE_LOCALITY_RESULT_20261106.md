# Phase 2V-T4 — a structural byte-locality explanation, but no validated DDT-max predictor at five rounds
**Dated 2026-11-06; retrospective source-audited analysis, zero neural training.**
**Study boundary:** this report analyzes ALREADY-OBSERVED T3 ToySPN results. Its [locked analysis plan](PHASE2V_T4_DDT_PREDICTION_AND_BYTE_LOCALITY_PROTOCOL_20261106.md) was committed at `fdbe3114750f683845a5fd19dd25db18fbb509f1` before T4 calculations, BUT **T3 outcomes were already known**. It is *not* a new prospective/blinded validation of the predictive hypothesis.

## Motivation and original full evidence

The [Phase 2V-T3](PHASE2V_T3_ROUND_DIFFUSION_RESULT_20261106.md) original experimental script and a distinct verifier established that removing 11-bit cross-byte diffusion from the educational 32-bit, four-byte ToySPN caused 100% pair-label discrimination in all 144 tested rotation-0 panels across two-to-five rounds, while maintaining mixing reduced held-out S-Box histogram AUC to ~0.545 after five rounds. We now separate two questions which earlier analyses could conflate:

1. **Provable invariant:** why can a one-byte input XOR difference remain detectable after arbitrarily many rounds if each round operates separately on its four bytes?
2. **Prediction of measured five-round AUC:** is a coarse scalar S-Box feature—the average of maximum 8×8 DDT entries across 20 S-Boxes—enough to predict unseen-S-Box AUC across nine different source curricula?

The relevant classical research already distinguishes *per-S-Box differential probabilities* from *multi-round activity and diffusion*; e.g. Daemen and Rijmen's [Wide Trail Design Strategy](https://cs.ru.nl/~joan/papers/JDA_VRI_Wide_2001.pdf), and modern introductory [DDT/active-SBox review](https://www.mdpi.com/2073-8994/18/1/8). Neither concept is newly discovered here.

## Analytical lemma: byte separability without inter-byte mixing

Write a 32-bit state as four bytes `(x_0,x_1,x_2,x_3)`. Consider any number of rounds of this form:

`x_j <- S_j(x_j XOR k_{r,j})` for j=0,1,2,3, with each `S_j` a **bijective** 8-bit substitution; possible final XOR whitening is per byte. **There is no cross-byte rotation or mixing.**

For each byte j, the final ciphertext byte is therefore some composition of bytewise bijections and XOR keys `F_j(x_j)` and **does not depend on any other plaintext byte**. If a pair differs in exactly one input byte t, for every j != t the inputs are equal, hence `F_j(x_j) == F_j(x'_j)`. At position t the inputs differ and the composed `F_t` is bijective, so `F_t(x_t) != F_t(x'_t)`.

**Thus: a pair with a difference in one input byte has an output XOR with exactly three zero bytes, for ANY finite number of independent per-byte bijective rounds and any keys.** This mathematical conclusion is general under the stated product-cipher assumptions; it is **NOT new cryptographic theory**. Crucially, it **does not guarantee** that an arbitrary randomly sampled *negative* pair cannot also have a one-byte output XOR. Therefore T3's empirical **AUC 1** on its finite 144 panels is a sample outcome, not a theorem that all future datasets get perfect classification.

In a truly **uniform** 32-bit ideal permutation, conditional on two distinct inputs, the XOR of the outputs is uniform over `2^32 − 1` possible nonzero 32-bit differences. Exactly `4 × 255 = 1,020` differences have a nonzero value in **one and only one byte**. Hence the exact event probability:

\[ P(\text{three unchanged ciphertext bytes})=\frac{1020}{2^{32}-1}=2.3748725658224133\times 10^{-7}. \]

This formula concerns one fixed pair of distinct inputs under a uniform ideal permutation, not an AUC for any finite sample.

**Independent code tests:** `12,288/12,288` pre-registered deterministic cases, two fixed key schedules, rounds 1,2,3,4,5,7, two one-byte XOR input differences, 512 fixed plaintexts, bijective affine SBox `S(x)=(73x+41) mod256`; a deliberately non-bijective constant SBox control showed the bijection hypothesis cannot be dropped. The separate verifier confirmed **2,560/2,560** more cases with an *independently generated shuffled random bijective SBox and different key values*, and enumerated all **1,020** admissible one-byte nonzero XOR words. These tests are sanity checks of the general proof, not proof by random testing.

## DDT-max prediction: full registered nine-group LOSO outcomes

Original experiment source-byte identity:
- T3 canonical JSON `phase2v_t3_round_diffusion_audit_20261106.json` SHA256 **`bd9f73539e99d5df40c53876a91da5fc61b23711da553107200ea3f24c366ea0`**;
- exact original T3 324-panel CSV SHA256 **`5d426f3d6eb1e8a528cff3c083d95d991578e4342ef973c1db5db9420086cf6b`**;
- original source S-Box+data reconstruction ZIP SHA256 **`6f6b6fbe68a123ad8bf302b4ba3a80f069e9d8ab64188121c28e631a66444845`**.

The study uses exactly **N=9 evolution-seed curricula**. Predictor `x_e` is the arithmetic mean of **20 maximum-DDT counts** of its source S-Boxes; its group range is **11.0–11.7** (narrow). Each target `y_e` is the arithmetic mean of the fixed **two input-difference test AUCs** `1,256` on held-out S-Boxes under original **11-bit mixing**, at R5 (primary), R4 (secondary) and their difference (secondary). Group pairs share training/T seeds, keys and sampling schedules; nine curricula should NOT be interpreted as nine independent fresh unbiased draws.

Exactly nine leave-one-evolution-seed-group-out refits; **one-feature ordinary least-squares line fitted only on other eight groups** versus a baseline predicting the eight-group mean. No tuned ridge, hyperparameter, feature combination or after-outcome group selection. Report mean absolute error (MAE), root mean square error (RMSE), and relative squared improvement `1−SSE_DDT/SSE_baseline`. Both predictors are compared on the SAME group folds.

| Target, held-out S-Boxes | LOSO mean-only baseline MAE | LOSO linear mean-max-DDT MAE | LOSO baseline RMSE | LOSO DDT RMSE | Relative heldout SSE improvement vs mean baseline |
|---|---:|---:|---:|---:|---:|
| **Primary R5 AUC** | **0.02651835** | **0.02914663** | 0.03076290 | 0.03463854 | **−26.78%** |
| Secondary R4 AUC | 0.01830380 | 0.01516026 | 0.02070235 | 0.01843350 | +20.72% |
| Secondary R4−R5 AUC reduction | 0.02983409 | 0.02801775 | 0.03456580 | 0.03467527 | −0.63% |

**Primary falsification outcome:** the fixed **mean-of-DDT-max scalar does NOT show improvement** over a mean-only predictor for held-out R5 AUC in this source dataset. It has **9.91% larger MAE** and **26.78% larger SSE**. Its in-sample Pearson association with R5 AUC is −0.355 (descriptive only), compared with +0.487 for the retrospective R4 endpoint. The apparent R4 benefit does **not** persist at R5. For the R4−R5 drop, the DDT model modestly improves MAE but not RMSE/SSE: do not describe it as a positive predictive law. Observed group x range is only 11.0–11.7, limiting any extrapolation.

**This does NOT refute the DDT, full differential-trail analysis, active SBox counts, branch number, neural methods, or stronger SBox descriptors.** Maximum DDT count is a coarse local SBox statistic and disregards which transitions survive the specific 11-bit mixing, multiple-round nonlinear propagation and keys. The design literature is explicit that multi-round differential resistance involves the diffusion layer and active SBoxes, not the largest DDT entry alone.

### Provenance table (two difference AUCs aggregated by evolution group)

| Original evolution seed | Mean of 20 SBox max DDT | R4 held-out AUC mean | R5 held-out AUC mean |
|---:|---:|---:|---:|
| 726011 | 11.3 | 0.696731 | 0.526437 |
| 726023 | 11.4 | 0.667624 | 0.570113 |
| 726037 | 11.7 | 0.704717 | 0.509864 |
| 726049 | 11.3 | 0.717975 | 0.594548 |
| 726061 | 11.2 | 0.667048 | 0.545554 |
| 726073 | 11.2 | 0.684129 | 0.572986 |
| 726087 | 11.2 | 0.663993 | 0.511991 |
| 726099 | 11.3 | 0.671210 | 0.556538 |
| 726113 | 11.0 | 0.669830 | 0.561787 |

## Reproducibility and independent verification

- A **new pure-standard-library source script** `phase2v_t4_ddt_predictive_audit_20261106.py`, SHA256 **`a699327c76d377a6e35bb27507c7aea99857c4443ed392fbb4df60974b24f246`**, verifies source SHA/canonical receipts, reconstitutes the 9 groups and writes exact grouped LOSO audit JSON/27-prediction CSV and runs 12,288 structural lemma cases.
- Original 9-group JSON `phase2v_t4_ddt_LOSO_and_byte_locality_audit_20261106.json` SHA256 **`ef53cf6303d9b761250f424093c2241f56ca6f54a78baaa99d2013d5fa8ea80b`**, canonical receipt SHA256 `2b933bc241870a83cfdc79ca3ee0edc593b82322f49333fd2284be4a47fbccbd`.
- Original 27-fold CSV `phase2v_t4_LOSO_27_predictions_20261106.csv` SHA256 **`9c28f29e9a64f87c64d4f47d3c142c1a5d86f618389a14a8238b645c441487a5`**.
- Second, **mathematically independent NumPy least-squares** checker `phase2v_t4_independent_verifier_20261106.py` SHA256 **`fa481c0218a5e7b43d6e0747039eb01d42b1376d142041a51b1a8edbe907e5f3`**, matched **27/27 fitted leave-one-group-out predictions** to ≤5×10⁻¹² in numeric floating-point and executed a separate **2,560** shuffled-bijective-SBox case test. Output audit JSON SHA256 **`544158485c7650a32ff83e888abbac2009e98115de881fa30c7513df6b29d469`**.
- The original T4 pure-stdlib script was executed again in a clean output location; **both original JSON and 27-fold CSV reproduced EXACT BYTE-FOR-BYTE**, not just approximately equal metrics. Independently verified original T3 nested 12 checksummed files, 324 full source panels, 256 AUC arithmetic checks, and 8,192 invertibility checks using the T3 standalone archive verifier.
- **Complete conversation evidence package** `phase2v_t4_ddt_predictive_audit_verified_evidence_20261106.zip`: **7,230,811 bytes**, exact SHA256 **`328b986e47f158132da72c3aa815d0a78182fc0cffecf57649617d7e338c29ca`**. Contains original unchanged T3 evidence ZIP with historical Phase2G 39 source artifacts, original T3 self-auditor, T4 executable study+original JSON/CSV, independent source and numerical verifier+result, T4 standalone archive verifier, README, exact SHA256SUMS. T4 archive validator passed: **9/9** member hashes, CRC, canonical source identity, all 27 folds and both analytical tests. All files are downloadable in conversation, but **no durable user-controlled external archive has been verified**.
- Python environment for the independent regression checker used NumPy **2.3.5**, a separate analytical implementation from the standard-library script; this is not the original Phase2G training environment. No neural model was initialized or trained in either T4 execution.

## Important limits and next falsification

This is a narrow **retrospective post-hoc analysis on nine previously examined source curricula**, not new blinded confirmatory prediction. No statistical p-values, confidence intervals, claims about 32-bit real-cipher security or neural superior distinguishing power can be supported. The original source reconstruction itself is faithful to source SBox fingerprints but does not independently authenticate missing September 2026 original ciphertext input bytes.

The strongest *next scientific test* would construct **mechanism-aware predictors**: count the active byte/SBox positions allowed by the 11-bit rotation, use full differential transition structure and candidate trail scores, and then evaluate a preregistered prediction on **NEW** SBox curricula / original plaintext sampling schedules / alternative key families unseen by the fitted rule. Only after those controls should a same-split neural-vs-classical comparison be authorized separately. Do not adjust frozen September Phase2G `phase2g_adaptive_coevolution_not_supported` or execute any of the sealed Phase2U 96 model trainings. Branch/PR remains DRAFT, not merged to main.
