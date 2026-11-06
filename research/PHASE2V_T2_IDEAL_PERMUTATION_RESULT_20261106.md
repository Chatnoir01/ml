# Phase 2V-T2 — matched ToySPN vs a sampled ideal 32-bit random permutation

**Dated 2026-11-06. Experimental scope: synthetic classical ciphertext-pair label distinguishability, with zero neural training. Protocol registered [before outcome](PHASE2V_T2_IDEAL_PERMUTATION_PROTOCOL_20261106.md) in commit `1b96d7d30604afde943afe9f3ca7f87d411c20e3`.**

## Question and null comparator

The previous [Phase 2V-T1](PHASE2V_T1_KEY_SBOX_TRANSFER_RESULT_20261106.md) showed a simple four-byte ciphertext XOR naive-Bayes histogram distinguish positive vs negative pairs from an educational four-round 32-bit **ToySPN** with median AUC ~0.69, including on five held-out S-Boxes and one alternate key schedule. We asked whether this pair-label signal exists even when the **ciphertext construction is replaced with a sampled uniformly random bijective 32-bit block permutation**, using *exactly the same plaintext pair draws, label sequence, train/test geometry, and baseline model*.

This is **NOT** itself the standard distinguishing security game in which an attacker decides whether an unknown oracle implements the cipher or a random permutation. It is a **matched control of the existing pair-label classification metric**. That difference matters scientifically. Formal random-permutation and PRP background: [Stanford PRP introduction](https://crypto.stanford.edu/pbc/crypto/prp.html), [lazy permutation sampling](https://eprint.iacr.org/2023/770).

## Prespecified design

Exactly the original 36 historical-source-**reconstructed** T1 cells (9 evolution curricula × input differences 1,256 × data seeds 776003,776097), first 15 SHA3-sorted curriculum S-Boxes for training and five entirely unseen S-Boxes for testing. Two key arms: the original fixed public ToySPN keys and the same ONE SHA256-fixed alternate-key schedule from T1. Four evaluation panels per cell: seen/original, unseen/original, seen/alternate and unseen/alternate; **144 source ToySPN panels and 144 matched ideal-permutation panels**.

For the ideal-permutation control, the pure-Python script samples an exact **bijection on queried 32-bit points** using **sparse Fisher–Yates without replacement**, with fixed published `SHA256`-domain-separated `random.Random` pseudorandom seeds for each (evolution seed, original S-Box fingerprint, key arm) identity. Exactly **360** persistent oracle instances, shared across both T seeds and both input differences. Each plaintext maps consistently and every distinct plaintext maps to a distinct ciphertext **within its oracle**. The two key arms are independent sampled oracle mappings. A 256-point exhaustive tiny-domain oracle control passed. All 360 real source oracles passed one-to-one domain checks over **720,000 distinct sampled input queries** combined. This is one reproducible deterministic sample from an ideal-permutation *simulation*, not an unknown real uniformly random permutation sampled with cryptographic randomness.

The same weak 4-byte empirical XOR histogram (Laplace smoothing alpha=1) was **fitted separately** for each family on its OWN **4,200 source-key/seen-SBox training pairs**, then tested without refitting across the four panels. Also tested fixed sign `-popcount(C0 xor C1)`, number of zero XOR bytes, and constant score AUC 0.5. **Neither family was allowed access to test labels when fitting**, alternate-key pairs or held-out S-Boxes. No model or hyperparameter selection from outcomes.

## Verified results — matched family AUC medians across 36 source cells per test arm

| Prespecified domain | ToySPN histogram AUC median | Ideal-permutation histogram AUC median | **Median of cell-by-cell paired AUC differences** (Toy−Ideal) | Ideal AUC observed range |
|---|---:|---:|---:|---:|
| Seen S-Boxes, original keys | **0.6867163831** | **0.5007893752** | **+0.1835844620** | 0.465537–0.526219 |
| Unseen S-Boxes, original keys | **0.6892143659** | **0.5043686107** | **+0.1894117647** | 0.416364–0.558137 |
| Seen S-Boxes, alternate keys | **0.6827086476** | **0.5040105626** | **+0.1897209653** | 0.468859–0.530143 |
| Unseen S-Boxes, alternate keys | **0.6862173266** | **0.5165158371** | **+0.1781060098** | 0.446510–0.560000 |

**All 144/144** *paired* ToySPN-minus-ideal histogram AUC deltas are strictly positive in this one oracle-sampling experiment. Minimum across the 144 panels **+0.05090909**, maximum **+0.29546577**, overall median paired delta **+0.18422419**. **Do not confuse the median of paired differences with the difference of separate AUC medians**; both appear above but were computed independently.

Across all 144 panels and their four arms pooled, the ordinary median ToySPN vs ideal AUC of the prespecified fixed methods:
- Constant score **0.50000 vs 0.50000**;
- Negative XOR Hamming weight **0.64049 vs 0.50308**;
- Count of zero ciphertext XOR bytes **0.68219 vs 0.50113**;
- Histogram **0.68657 vs 0.50443**.

The ideal histogram AUC is **not exactly 0.5 in each finite sample**; it ranges from about 0.416 to 0.560 on some smaller 300-pair held-out panels, which is consistent with finite sampling variation and potential weak train-only histogram overfitting. We **do not** assert a distributional p-value or ideal-oracle randomness theorem based on one deterministic draw and clustered source panels.

## Source and code-integrity controls

1. The **original Phase 2G source evidence ZIP** was independently reverified, and 9 original SHA3-ordered 20-SBox curricula reconstructed from the 2026-09 original seed generator. **36/36** selected original source cells were checked against the prior frozen reconstruction's exact complete **5,600 train, 1,200 validation, 1,200 test** split SHA3 fingerprints.
2. **All 144 new ToySPN panel AUC rows exactly match** the source T1 CSV and the corresponding original ToySPN test ciphertext-pair SHA3. The new script fails closed if any one differs; ToySPN historical data were not quietly regenerated or reselected.
3. Each ToySPN source/counterfactual and its ideal-oracle matched panel use **the same original plaintext sample pairs and binary labels**, with original 280/60/60 per-SBox split boundaries.
4. **360/360** sampled random-permutation oracles pass no-duplicate outputs (720,000 distinct sampled inputs). The complete per-oracle mapping SHA fingerprint and sampled size is in the result JSON, allowing source identity checks without exporting huge full maps.
5. An independent implementation of tie-aware AUC by **direct positive-versus-negative pair enumeration**, rather than ranking/sorting, matched **64/64** prespecified spot checks (first source cells of evolution seeds 726011 and 726023 × four test arms × four methods × two cipher families) **exactly**; maximal difference `0.0`.
6. The complete classical sampling experiment was **run twice** with unchanged source inputs, reproducing **the original JSON and CSV exactly byte for byte** (SHA-256 verified).
7. The complete ZIP contains an **independently executable read-only archive validator** which checks 13 included source file SHA256s, ZIP CRC, original nested evidence ZIP CRC, all 360 oracle identity counters, canonical T2 JSON self-digest, 144 panel identities and AUC values, 144 positive signed deltas and 64 pairwise AUC controls.

### Evidence artifacts, precise hashes and reproduction

| Saved artifact | Exact SHA-256 |
|---|---|
| T2 standalone Python sampling+baseline source script, `phase2v_t2_ideal_permutation_oracle_20261106.py` | `d08168c57547b2e037c253858f4e1ae708b6ca16e0858dea9b45c6dcb9ae7c52` |
| 144-row detailed JSON, `phase2v_t2_ideal_permutation_oracle_audit_20261106.json` | `5a85b2368c4fea33701f8f5fdd2f3a36782131502d24f96e389e528da9367d26` |
| 144-row paired CSV, `phase2v_t2_ideal_permutation_oracle_results_20261106.csv` | `85161424d3b2de1b15902b0d55a2b35c91a03597340d6fe41e6215acadf9956e` |
| Full packaged, verified conversation evidence ZIP, `phase2v_t2_ideal_permutation_verified_evidence_20261106.zip` | **`c7e8f4d608bdd912cbed4449b6781deb851a1d47d9f83354ab04d502c6428e3e`** |

**Bundle size**: **7,231,749 bytes**. Includes original Phase 2G 39-artifact archive (nested within source reconstruction ZIP), original reconstruction code, original T1 source and audited results, new full T2 source+results JSON/CSV, independent direct-pair AUC checker source+result, ZIP integrity checker, README and full SHA256SUMS. The bundle passed its standalone validator. It is a conversation file, **not a verified user-owned durable independent backup**, and the scripts are provided with that artifact rather than committed as standalone GitHub source files.

## Interpretation and boundaries

Within this fixed ToySPN sampling protocol, the classical ciphertext-pair class-label signal appears much stronger than in the matched **bijective random-permutation** control; it is **consistent with differential structure from this educational ToySPN's round design**, not merely an inevitable artifact of the label generator. No generalization beyond this one sampled deterministic oracle set or the registered 36 correlated cells follows automatically. The 144 panels share curricula, keys and plaintext draws; **no IID standard errors, confidence intervals or p-values** are provided.

This does **not** establish the security of any actual real-world block cipher, any novel cryptographic property, nor an advantage of the historical neural model over classical baselines. It also does not identify the cause of old Phase 2G's 64/144 mismatching neural weight SHA or reverse the original negative adaptive-coevolution verdict `phase2g_adaptive_coevolution_not_supported`.

**Most informative next distinct, separately preregistered tests:** independently resample plaintext schedules per S-Box and use *multiple* independent sampled random bijections, then perform a round-count ablation and matched held-out-key neural-vs-classical experiment only after proper registration. Do not silently enlarge this study after observing its outcomes.

**Research isolation:** PR remains DRAFT, no merge into `main`, no historical Phase 2G model retraining, no Phase 2U sealed 96-fit neural evaluation.
