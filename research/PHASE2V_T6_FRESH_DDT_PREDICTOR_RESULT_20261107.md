# Phase 2V-T6 — prospective full-DDT/active-byte feature DOES NOT predict 5-round ToySPN AUC beyond an intercept baseline
**Result 2026-11-07. Protocol was committed BEFORE T6 data generation at `eb68e196bc43b1ef8abf1f135294b983931cfa4a`.** T6 is a fully fresh cohort. Preceding [T5](../research/PHASE2V_T5_ABORTED_INCIDENTAL_COLLISION_20261107.md) is explicitly **INVALID**, not a source of test or train data. Zero neural training / zero Phase 2U sealed labels. DRAFT, not main.

## Scientific question

The earlier [T4](PHASE2V_T4_DDT_PREDICTION_AND_BYTE_LOCALITY_RESULT_20261106.md) retrospective prediction study found no out-of-group improvement at five rounds from one coarse SBox statistic (mean max-DDT). Could a more *mechanistically relevant* feature computed using **full DDT transition probabilities and exact 11-bit diffusion** forecast a newly created dataset's classical five-round ciphertext-pair distinguishability **before observing its test labels**, rather than merely correlate with known data?

The feature is the expected number of nonzero 8-bit output-difference bytes after TWO substitution+11-bit-mixing rounds in an explicitly approximate independent-per-byte Markov DDT model. It is a mathematically calculable deterministic statistic from the SBox alone; **not an exact full cipher trail, not a fitted neural model and not a security proof**.

## Prospective new cohort and test design

- Exactly **12 NEW source-independent evolution seeds** `902011,902047,902083,902119,902155,902191,902227,902263,902299,902335,902371,902407`. These were chosen **before** T6 outcomes and do not overlap T5's invalidated `901xxx` or original 2026-09 `726xxx`.
- Exact original 20×256-byte random-SBox permutation construction for each seed, with SHA3-256-sorted fingerprints, first **15 source-train** SBoxes and last **5 source-held-out** SBoxes. **240/240 distinct bijective SBoxes**, independent of September 2026 original source evidence.
- Exactly two original input XOR differences `1` and `256`; two source-independent public 6-word 32-bit key-schedule derivation families `K0,K1` per SBox (**480 distinct key schedules**); distinct SHA256-seeded independent original 400-pair plaintext draws per (SBox, key-arm, input difference), **960 distinct plaintext draw schedules** (unlike historical shared per-SBox plaintext schedules). The keyed ToySPN 32-bit/4-byte cipher uses the original 11-bit rotation, with either **4 or 5 rounds**.
- Histogram baseline: four XOR-byte Laplace-1 class-conditional log-likelihood ratios trained separately on **4,200** source-train examples from the 15 source-seen SBoxes for each (new seed, key arm, difference, rounds); evaluated **without test-label training** on 900 source-seen and 300 completely source-held-out-SBox test records. Exactly **192/192** fixed held-out AUC panels, four controls each: constant/null, negative output Hamming weight, zero output-XOR-byte count, fitted four-byte histogram. Original 60 validation pairs per SBox never used for fitting or selection.
- This is a *source-independent synthetic ToySPN* result, not an archival replay of the 2026-09 original Phase 2G neural training; no historical missing raw bytes or CPU identities are falsely authenticated.

## Exact 12-group leave-one-curriculum-out predictive falsification

For each new evolution group calculate a precommitted scalar feature from only SBox input bytes: average maximum DDT (existing coarse comparator), and average full-DDT-weighted **two-round expected active-byte count** using exact rotate-left-11 masks, averaged across 20 SBoxes and both input differences. Outcome for primary prediction is the **arithmetic mean of the four entirely source-unseen SBox R5 histogram AUCs** (K0/K1 × diff1/256); secondary: corresponding R4 AUC and R4-minus-R5 AUC. One evolution-seed group is the unit, **N=12**, not 192 independent observations.

Twelve LOCO folds, each fitting **one scalar OLS feature and an intercept on the OTHER eleven groups only**, compared with the baseline predicting the other-eleven target mean. No feature or hyperparameter selection based on test outcomes. Prespecified *primary success requires BOTH MAE and SSE improvement over mean-only*. It FAILED.

| Registered target and feature | Mean-only LOCO MAE | Single-feature OLS LOCO MAE | Relative SSE change vs mean baseline |
|---|---:|---:|---:|
| **Primary R5**, full-DDT+rotation 2-round active bytes | **0.00923995** | **0.00993473** | **−26.35% (worse)** |
| Primary R5, mean maximum DDT count | 0.00923995 | 0.00948947 | −6.35% (worse) |
| Secondary R4, full-DDT+rotation | 0.01784771 | 0.01881436 | −6.17% (worse) |
| Secondary R4, max DDT count | 0.01784771 | 0.01807640 | −2.36% (worse) |
| Secondary R4−R5, full-DDT+rotation | 0.018? (see raw JSON for exact mean) | **0.02014008** | −18.45% (worse) |
| Secondary R4−R5, max DDT count | 0.018? (see raw JSON for exact mean) | **0.01847463** | −5.52% (worse) |

*For the R4−R5 secondary rows, the exact baseline MAE is specified in the machine JSON; no rounded/invented value is used here.* One key failure mode: the new physics-aware x feature varies only from **2.68662 to 2.71440** across the 12 new curricula, which is a small dynamic range compared to outcome variation; despite exact DDT computation, the scalar discards considerable per-trail information.

### Source-seen/held-out test AUC persists with independent keys and plaintext schedules

| Test domain and rounds | Number of fixed panels | Histogram median AUC | Observed AUC range |
|---|---:|---:|---:|
| Source-seen SBoxes, R4 | 48 | **0.688656** | 0.652061–0.725353 |
| Entirely source-unseen SBoxes, R4 | 48 | **0.686403** | 0.634609–0.748507 |
| Source-seen SBoxes, R5 | 48 | **0.551420** | 0.513062–0.600790 |
| Entirely source-unseen SBoxes, R5 | 48 | **0.552488** | 0.484888–0.616154 |

This **independently sampled new dataset** confirms a limited, descriptive property of this 4-byte educational ToySPN: this weak classical histogram can distinguish the prescribed ciphertext-pair labels above chance on average at R4 but its AUC is much closer to chance at R5. The statistics do not establish real-world cryptographic advantage, general security, formal statistical significance or new scientific novelty. Some R5 unseen panels have AUC below 0.5, as expected under finite sampling; not all models/arms behave identically.

## Important methodological correction: T5 was INVALID, T6 succeeds without outcome repair

The first prospective attempt T5 required zero exact ciphertext BLOCK overlaps between its large pooled 32-bit train/test ciphertext sets. It detected one same-block collision in the final T5 group and **stopped without scientific output**. See [T5 invalidation](PHASE2V_T5_ABORTED_INCIDENTAL_COLLISION_20261107.md) and [draft PR #175](https://github.com/Chatnoir01/ml/pull/175). Its previously seen partial group progress values were **NOT used as training data, test results or group selection**.

T6 was separately preregistered before generation of new disjoint `902xxx` curricula. It declared an explicit exact ciphertext **block** collision counter and pre-specified sensitivity AUC removing only colliding test rows, with **full-panel AUC always PRIMARY** and unchanged training. It separately treats **any full ciphertext PAIR reuse** as an immediate abort. On the entire T6 cohort: **zero panels have any full same-pair OR same-block train/test overlaps**. All 192 sensitivity AUCs equal their primary AUC exactly, with zero excluded rows. No T6 records were filtered, reseeded, omitted, or modified after outcomes.

## Independent engineering audit and byte-identical reproducibility

Source program `phase2v_t6_fresh_ddt_predictor_20261107.py` SHA256 **(see attached SHA256SUMS)**, full 12-group JSON `phase2v_t6_fresh_ddt_predictor_audit_20261107.json` SHA256 **`92429269409b696129e0ad85298ae45db3fafcdac9c78f3ea74925f91b45c3cb`**, 192-panel CSV SHA256 **`c7ec91d52c4bcbf31a28e862a10980a231e45aa2e0306dbbdd4ca1b7d66978bb`**, 72 held-out-fold CSV SHA256 **`0ded1b40a408b1b8be5c4840997edf29391d2c648dd530bb58a2a9525ff905dd`**.

A second fully independent audit script:
- Reconstructed exactly **72/72 OLS held-out fold predictions** from *NumPy least squares* independently of the original standard-library scalar covariance OLS, max absolute delta **4.44×10⁻¹⁶**.
- Mathematically separately enumerated **all second-round full-DDT transition combinations** for the two preselected first SBoxes and both input differences: **4/4** direct checks of the new DDT/active-byte feature EXACTLY match the original analytic masked-product method (zero error).
- Regenerated the full source trains and test labels for the first and last new evolution seeds × both inputs × both key arms × both rounds, and computed AUC with direct positive–negative score-pair enumeration, independent of rank sorting: **16/16 EXACT AUC** and source SHA3 split matches, error zero.
- Original data generation source passed exact ToySPN 4-round parity on fixed reference inputs, exact 12-group panel identity and 240 unique SBox/480 key/960 independent plaintext schedule identity, DDT row mass 256, no zero-output transitions for nonzero input differences.
- A separate clean directory reran the **entire deterministic experiment** and reproduced original JSON, 192-panel CSV and 72-fold CSV **byte-for-byte** with their identical SHA256 hashes.
- ZIP integrity verifier checked **12/12 original package members**, canonical JSON internal receipt, exact panel CSV parity, exact independent audit results, historical nested Phase2V-T4 ZIP CRC, and the literal earlier T5 abort log; report `source-original` source independence is explicit.

**Complete conversation-download evidence** `phase2v_t6_fresh_ddt_predictor_verified_evidence_20261107.zip` **7,379,943 bytes**, SHA256 **`047336b1384a152eb2cffed0bd5382a86c1a86de0a03f3a7ca2cdbb6365c0126`**. Includes unchanged nested T4 evidence (itself containing original frozen historical 39 GitHub ZIPs), original T5 aborted code/log, complete T6 execution source, primary raw JSON+192-row CSV+72-fold CSV, independent NumPy math verifier and audit, ZIP integrity verifier, explanatory README/SHA256SUMS. Scripts are attached to the ChatGPT conversation rather than committed separately in GitHub. **No independently user-owned durable storage has been verified**.

## Conclusions and next research design

**Primary predictive hypothesis rejected at the preregistered criterion**: this scalar full-DDT two-round active-byte descriptor does **not** outperform a trivial mean forecast for a five-round classical ToySPN AUC on twelve freshly sampled curricula. A more elaborate but inappropriate post-result tuning of this cohort would overfit small N=12. This finding is NOT a global refutation of differential trails, stronger matrix/branch-number features, multi-round exact DDT support, key conditioning or neuronal methods.

The positive source-backed finding is methodological: after explicitly correcting the old shared-per-SBox plaintext sample design and using genuinely distinct public key schedules per SBox, the classical ToySPN R4/R5 distinguishability degradation remains reproducible in a wholly new synthetic cohort. This supports a toy-mechanism observation, not a cryptographic novelty claim.

**Before any new neural training:** propose stronger mechanism-aware predictors with multi-round differential probabilities, a much larger independent sample of truly varied cipher architectures (not all random permutations of same family), and an independent held-out cohort fixed BEFORE any feature fitting. Preserve the original T6 negative result unmodified.

Historical Phase2G frozen verdict `phase2g_adaptive_coevolution_not_supported` remains unchanged; original sealed Phase2U 96 prospective neural fits remain ZERO; no main merge, PR DRAFT.
