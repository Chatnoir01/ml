# Phase 2V-T3 — round count and between-round diffusion determine toy-cipher distinguishability
**Experimental result dated 2026-11-06. Prospectively registered protocol [PHASE2V_T3_ROUND_DIFFUSION_PROTOCOL_20261106.md](PHASE2V_T3_ROUND_DIFFUSION_PROTOCOL_20261106.md) was committed BEFORE first T3 AUC computation at `1c98f905ead28a17a8b3011b9c9052d44da3487a`.**

## The bounded scientific question

In a fixed 32-bit, educational ToySPN with four 8-bit S-Boxes per state and a public round-key schedule, how do increasing rounds and rotating state bits between rounds influence the power of a simple **ciphertext-only XOR-byte-frequency** distinguisher?

A prior, fixed four-round/rotate-11 experiment found classical test AUC around 0.69 against ~0.5 for a lazy sampled ideal random permutation. Here we separately vary **(i) original source key prefix with R in {2,3,4,5} rounds**, and **(ii) state rotation 0 (deliberately byte-separable and weakened) or 11 bits (original construction)**. The rotation-0 arm is a deliberate structural-ablation control, not a new secure design. A fifth round uses the existing sixth public key word `0x299F31D0` from the older source neural-heterogeneity key schedule; original 4-round/rotate-11 is the exact historical five-word ToySPN.

Exactly 18 original-source reconstructed cells: **9** evolution seed curricula × differences **1 and 256** × only original T seed **776003**. For each original SHA3-sorted 20-SBox curriculum, fit one four-position Laplace-1 histogram of ciphertext-pair XOR bytes on **4,200** train pairs from 15 S-Boxes, then test on **900** source-seen and **300** entirely held-out S-Box pairs. Also score fixed-sign negative XOR Hamming weight, count of zero XOR bytes, and constant null (AUC 0.5). Only the single original test set is used for AUC; validation unused. Labels and plaintext-pair schedules are fixed to original reconstructed source, not augmented or tuned.

A fixed matched, separate weak count-table oracle control uses a *reproducibly sampled* **32-bit lazy random bijection** per original evolution/SBox identity (180 persistent instances), not a random function with collisions. It is trained on its own 4,200 paired source-schedule examples and tested on matching 900/300 panels. Total exactly **288 ToySPN** and **36 sampled ideal-permutation** test rows, 324 in aggregate. This does **not** implement a full chosen-plaintext PRP security game, and cells are correlated rather than independent statistical replicates.

## Primary: held-out S-Box histogram test AUC declines with 11-bit rotation and more rounds

| Rounds | Original rotate 11, median seen AUC | Original rotate 11, median unseen-SBox AUC | Ablated rotate 0, median seen AUC | Ablated rotate 0, median unseen AUC |
|---:|---:|---:|---:|---:|
| **2** | **1.000000** | **1.000000** | **1.000000** | **1.000000** |
| **3** | **0.999129** | **0.999027** | **1.000000** | **1.000000** |
| **4** | **0.686128** | **0.683360** | **1.000000** | **1.000000** |
| **5** | **0.549570** | **0.544514** | **1.000000** | **1.000000** |
| Sampled ideal 32-bit permutation (no rounds defined) | 0.50396 | 0.49700 | – | – |

The ideal permutation results here are the **one newly fixed T3 sample**, not a universal expectation over independent random permutations. Each ToySPN median is across exactly 18 original-source reconstructed cells, not 18 IID seed samples.

- **All 36 seen+unseen** original-rotation comparisons decline strictly from rounds 3→4, and all 36 decline strictly from 4→5, with fixed complete panel comparison. Difference from 2→3 is non-positive, sometimes exactly zero because both scores are already perfect.
- At R=5, original rotation-11 histogram AUC lies in **0.522790–0.586855** on seen test S-Boxes, **0.493959–0.619163** on unseen. **17/18** unseen cell AUCs are > 0.5. It approaches but does **not** universally equal random-chance AUC after five rounds.
- The R=5 versus R=2 **paired** median histogram AUC difference is **−0.4504298643** on seen, **−0.4554864253** on entirely unseen test S-Boxes. Direct differences of independently reported medians are NOT substituted for paired medians.
- With **rotation 0**, **all 144 rotation-zero ToySPN panels** across R=2–5 have **exact AUC 1.0**. The fixed zero-byte-count method also yields perfect AUC on these tested data. This is consistent with the simple byte-separability mechanism: when each byte is substituted independently with per-byte key XOR and no cross-byte rotation, an original one-byte input XOR difference can affect only that byte at every round. The positive-pair output difference retains unchanged other bytes. It would be wrong to generalize the empirical AUC 1.0 to all possible data draws or real ciphers.
- Under the original 11-bit rotation, the count of test records with perfect AUC drops from **36/36 at two rounds**, to **11/36 at three**, to **0/36 at four or five**.
- The precommitted 4-round/rotate-11 original source case matches the previously published T1 calculation on **36/36 held-out/seen panels**, every AUC score and underlying test-ciphertext SHA3 **exactly**.

**Interpretation:** the particular ToySPN's 11-bit between-round bit mixing appears much more important than merely adding independent per-byte substitution layers. This is a model-specific empirical demonstration of the established **diffusion principle**, not the discovery of diffusion or a new cryptographic primitive. Additional rotations or affine/key changes were NOT optimized or tested, and the key prefix also changes with R.

## Secondary: S-Box differential uniformity measured, but no predictive relation established

The source-derived 180 authentic checkpoint-zero permutation S-Boxes were also characterized by their **maximum differential distribution table (DDT) transition count** over all 255 non-zero input differences. Across the nine evolution-seed curricula, medians per 20 S-Boxes are **11–12** (observed per-box range **10–14**).

This experiment does **not** establish that the DDT maximum predicts neural AUC or different round-count AUC curves for an unseen S-Box. Per-cell class distributions share plaintext schedules, and only 9 curriculum groups are available. Any proposed DDT–AUC relationship requires a distinct prospectively fixed design and preferably full DDT trail or differential bound metrics rather than a single maximum count.

## Independent source and numerical verification

The entire **standard-library-only** T3 script executed twice, including from a separate clean directory with only the required source inputs. The resulting **324-row JSON and CSV were identical byte for byte (SHA-256 exact)**.

Original source authentication and hard gates passed:
- **9/9** original reconstructed S-Box curriculum hashes, original September 2026 population source checks already authenticated by nested PR #169 evidence.
- **18/18** reconstructed full source train/validation/test split SHA3 match pinned prior Phase2G reconstruction; **36/36** original R=4/rotate=11 test AUCs + corresponding ciphertext SHA3 match previous T1 source exactly.
- **180/180** persistent sampled 32-bit ideal permutation maps remain bijective on queried inputs, with **180,000 sampled distinct input→unique-output mappings**; repeated input queries returned cached values.
- Zero exact ciphertext training/test block and exact-pair overlap on every executed ToySPN and ideal baseline panel.
- **256 / 256** independent tie-aware AUC calculations by *direct positive–negative score-pair enumeration*, on prespecified first/last evolution seeds, both differences, both test domains, all 2/3/4/5 rounds and both rotations, using an independently formulated arithmetic method rather than the primary sorted-rank AUC.
- **8,192 / 8,192** independently implemented cipher decryption/encryption round trips on selected 8-bit S-Box permutations embedded in 32-bit four-byte states (two edge original curricula, two S-Boxes each, four round-count regimes × both rotations × 256 plaintext blocks).
- The standalone archive verifier rechecked **12/12 member SHA256**, ZIP CRC including original nested Phase2G source-archive CRC, canonical T3 JSON self-hash, original-source and T1 file hash binding, all 324 panel rows, 180 sampled oracle identities and independent arithmetic controls.

### Exact primary reproducibility artifacts

| File | SHA-256 |
|---|---|
| Executable T3 script: `phase2v_t3_round_diffusion_ablation_20261106.py` | `b5f320166fe1b47294a94863c490e0d0d65c36a1dba6806cdc133aad58549a1d` |
| Detailed original 324-panel JSON: `phase2v_t3_round_diffusion_audit_20261106.json` | `bd9f73539e99d5df40c53876a91da5fc61b23711da553107200ea3f24c366ea0` |
| Original complete 324-row CSV: `phase2v_t3_round_diffusion_324_panels_20261106.csv` | `5d426f3d6eb1e8a528cff3c083d95d991578e4342ef973c1db5db9420086cf6b` |
| Independent direct AUC + invertible cipher checker: `phase2v_t3_independent_controls_20261106.py` | `50a2a88ce2b23682e8f55c97a0c0f61451117694775d929006d7cf4b85ff8e9b` |
| Source verification result JSON | `c289f686c403efd97c0b4e1757dc8a184e7a174d63e8731d605ecec0fa455a08` |
| Downloadable full self-contained evidence package: `phase2v_t3_round_diffusion_verified_evidence_20261106.zip` | **`5238c09d12bc396a2cce2880ca409038f8797bcde61c286af794651bccb8065e`** |

The entire evidence ZIP is **7,209,225 bytes**. It includes the unchanged original Phase2G source reconstruction ZIP (itself containing the original 39 historical GitHub archives), prior original-source helper scripts, previous 144-row T1 CSV, T3 code and raw JSON/CSV, independent verification code/results and README plus SHA256SUMS. It has been self-verified by the independent archive verifier. **No verified user-owned permanent external backup** of the archive exists yet. Research source scripts are in the conversation evidence ZIP, not committed as standalone GitHub files; the GitHub branch documents the exact protocol, code SHA, result and reproducibility route.

## Scientific limits and appropriate next steps

**Demonstrated:** a predeclared and independently rechecked causal **code intervention** on the educational ToySPN—removing its between-round mixing—preserves a *perfectly distinguishable* one-byte-input-difference pattern in the tested data across up to five rounds; retaining the original 11-bit mixing and adding more rounds reduces the measured test distinguishability, with values near chance by round five in some cases.

**NOT established:** security of real ciphers, an optimal classical differential attack, a DDT–AUC predictive law, a new cryptographic concept, an independently held-out random key-family generalization, the cause of historical Phase2G's 64 trained-state mismatches, neural superiority, or population-level inference from dependent source cells.

**Most informative next protocol:** hold all cipher architecture components fixed and independently vary *diffusion strength* and *full DDT differential trails*, use new per-S-Box plaintext schedules and multiple independent ideal permutations, then compare to a matched neural method only if the original sealed Phase2U governance permits. No existing historical verdict should be adjusted by this experiment.

Frozen Phase2G verdict `phase2g_adaptive_coevolution_not_supported` unchanged, **0** new neural training fits, **0** Phase2U prospective neural fits, no merge to `main`, research PR **DRAFT**.
