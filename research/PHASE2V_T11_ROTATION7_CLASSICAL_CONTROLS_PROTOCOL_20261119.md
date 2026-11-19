# Phase 2V–T11 — R7 diffusion generalization with classical DDT controls

**Prospective frozen registration, 2026-11-19. MUST commit BEFORE ANY T11 S-Box generation, panel ciphertext, AUC, predicted group outcome or experiment execution.** Study motivated by T10's valid negative on MixColumns (no zero-byte distinguisher signal). The T9/T10 GitHub three-version CI gates remained queued at preregistration; no T9/T10 status is inferred. Toy cipher research ONLY; no neural fits, no Phase2U unsealing, no changes to any older study. Original repository `main` SHA `b03da1d95e98709869d007571de4f8bbce234a1b`.

## Fixed scientific question
Does a **predefined, source-only geometry-specific early active-byte predictor** correlate negatively with the *classical* four-round ciphertext-pair count-zero-byte AUC on a distinct but still signal-bearing educational SPN architecture whose inter-round permutation is `ROTL32(state,7)` rather than historical `ROTL32(state,11)`? The score and SBox/round-key steps are unchanged. No new feature choice after seeing results. The original R11 reference must also be measured using the same candidates, public keys and plaintext pairs.

This is NOT a claim that R7 is a secure block cipher; it is a controlled change to the ToySPN's rotation, NOT AES, and cannot establish international novelty. The target score may again be at chance; a predeclared signal gate handles that.

## EXACT preregistered cohort, all new synthetic sources
- Exactly 12 parent labels `907011,907072,907133,907194,907255,907316,907377,907438,907499,907560,907621,907682`, no modification or replacement; each parent independent seeded shuffle `random.Random(SHA256_INT("phase2v-t11-parent-v1|GROUP")).shuffle(list(range(256)))`.
- Exactly six transformed child SBoxes for each parent (INDEX 0..5). `rng=random.Random(SHA256_INT("phase2v-t11-variant-v1|GROUP|INDEX"))`; separately shuffle `pin`, `pout` initially `list(range(8))`, derive `a,b=rng.getrandbits(8),rng.getrandbits(8)`; candidate output `S'(x) = bit_permute(PARENT[bit_permute(x,pin) XOR a],pout) XOR b`, with `bit_permute(x,p)=sum((((x>>i)&1)<<p[i]) for i in range(8))`.
- Exact SHA256 byte fingerprints of 12 parents and 72 candidate permutations; duplicates or non-bijective SBoxes -> whole study INVALID, no outcome-driven correction. Each candidate must exactly match its own parent in global DU, vectorial NL, maximum abs LAT, max algebraic degree and aggregate SAC, computed with actual repo `cryptoshield.py` + independent DDT/Walsh/ANF auditor (parent metrics may vary across groups). All six children of one parent are affine equivalent, not six statistically unrelated designs.

## Fixed predictors and honest classical comparators
For each candidate S and fixed input deltas d∈{1,256}, define a one-active-byte difference at lane `lane=0` if d=1, `lane=1` if d=256, using all 256 byte values x and output byte difference `S[x] XOR S[x XOR 1]`:
- **F7**, the **PRIMARY** predictor: arithmetic mean over the two d of `E_{x=0..255}[count_active_bytes(ROTL32((S[x] XOR S[x XOR 1])<<(8*lane),7))]`. Larger F7 predicts **LOWER AUC** at four rounds of the new R7 cipher. This is the direct geometry-matched, fixed mathematical analogue of the T9 feature.
- **F11**, **secondary transfer comparator**: identical formula, replace 7 with 11, never recalculated after seeing ciphertexts. Larger F11 predicts lower R7 AUC.
- **D1coll** (DDT control): `sum_t DDT_S[1,t]^2/(256*256)`; larger means more concentrated one-round differential output, prespecified **higher R7 AUC** direction. All 256 x source values, no ciphertext data. No feature fitting.
- **D1max** (DDT control): `max_t DDT_S[1,t]/256`; prespecified **higher R7 AUC** direction. No feature fitting.
All are computed source-only BEFORE associating outcomes and frozen by candidate fingerprint. They are **simple classical one-round reference statistics, not state-of-the-art multi-round cryptanalysis baselines**. Do not call higher F7 rho proof of novel security property or superior neural performance.

## Paired keys, samples, rounds and architectures
- Fixed key arms `K0,K1` per group, each shared across six SBox children, both architectures and depths. Exact six deterministic 32-bit words `int.from_bytes(SHA256(ascii("phase2v-t11-key-v1|GROUP|ARM|WORD_INDEX"))[:4],"big")` for index 0..5, **24 unique public research key schedules**.
- XOR plaintext differences `1,256`. Two independent plaintext pair schedules `REPLICATE=0,1` per group and delta, each seeded `random.Random(SHA256_INT("phase2v-t11-pairs-v1|GROUP|DELTA|REPLICATE"))`. For each schedule exactly **128 positive** `(p,p XOR delta)` and **128 negative** `(p,q)` excluding identical/delta-equal pairs; 32-bit values sampled by `getrandbits(32)`, reject any reused plaintext word *within* the full schedule; fixed 50,000 candidate cap, whole study INVALID on cap. Replicates must share NO plaintext words. SHA256 canonical serialized pair schedule, 48 distinct schedules. Same pairs across all SBoxes, key arms and both architectures for honest paired control. No training/test leakage because no fitted model.
- Exactly two architectures: **R11**, original `ToySPN` with ROTL11, versus **R7**, a newly separately implemented educational 32-bit SPN using the exact original order: round-key XOR, four independent byte S-Boxes, 32-bit ROTL7 between rounds, terminal XOR key. Exact inverse R7 and fixed parity with independently written reference for 4 and 5 rounds; round keys R4=first five, R5=all six.
- Exactly depths 4 and 5, and the **fixed** ciphertext pair score `S=number_of_zero_bytes(C(p) XOR C(q))` (0..4) with larger S meaning positive. Tie-aware AUC via discrete frequency U; independent slow positive-vs-negative pair enumeration on fixed edge cells. No neural models and no actual password/private key use.
- Exactly `12 groups ×6 variants ×2 architectures ×2 key arms ×2 deltas ×2 sample replicates ×2 depths=2304` panels, 256 pairs each. 128/128 balanced. Independent 256-label permutation null via `random.Random(SHA256_INT("phase2v-t11-null-v1|GROUP|SBOX_SHA256|ARCH|ARM|DELTA|REP|ROUNDS"))`. Null mean all panels must be [0.47,0.53].

## Frozen PRIMARY endpoint, no post-hoc rescue
For each group and its 6 variants, let Y7(S)=mean fixed R7 4-round AUC across the 2 key arms, 2 differences and 2 pair replicates (8 matched source cells). Compute Pearson-on-midranks Spearman rho(F7,Y7) of those SIX values for each group, ties retained, zero-variance vectors assigned rho=0. Exactly 12 group-level values are scientific units, not 2304 IID observations.

The preregistered F7 hypothesis is **SUPPORTED** only if **all**:
1. >=**10/12** group-level rho(F7,Y7) are strictly negative;
2. median of 12 rhos <= **−0.50**;
3. overall mean R7 4-round AUC >= **0.55**, an a priori signal floor to avoid interpreting a chance-level score as a predictor test;
4. shuffled-label null overall mean AUC between **0.47 and 0.53**;
5. all source, cipher, metric, balanced-pair, no-reuse and independent integrity checks pass.

If 1 or 2 fails but the R7 mean AUC signal gate passes, classify **NOT SUPPORTED**. If signal floor fails, classify **SIGNAL INSUFFICIENT** independent of any favorable subset. If source/checksum gates fail, **INVALID**. Never switch to R11 or change the feature, directions, group labels, key regime, thresholds or rounds to rescue a negative.

## Fixed secondary comparisons (always report; not primary)
- Per group Spearman(F11,Y7) with fixed negative direction, Spearman(D1coll,Y7) and Spearman(D1max,Y7) with positive direction; report all 12 group rhos per comparator, direction-consistent group counts, medians, and comparison of fixed directional rho score `-rho(F7,Y7)` against `-rho(F11,Y7)`, `+rho(D1coll,Y7)`, `+rho(D1max,Y7)` (no p-value/accuracy claim, no posthoc winning feature). Zero-variance output means rho=0.
- Same F7 and F11 against R11 4-round AUC on the matched source cohort, fully disclosed. Per-key-arm R7 and per-replicate R7 rank correlations and R4/R5 score means per architecture. No exclusions.
- R7 primary sample signal measured by mean 4-round AUC over all 1,152 R7 panels, descriptive R11 mean AUC and shuffled-label null; six-candidate AUC range and source feature range for each group. All panels and SHA fingerprints retained.
- Controls: no real AES deployed cipher, no "state of the art classical" claim for simple DDT row stats, no neural label training, no claims of resisting chosen-plaintext attacks beyond this educational score.

## Frozen execution/audit gate
1. Protocol SHA committed to GitHub FIRST. Then implementation and new source. Run original code twice, compare canonical JSON byte-for-byte and SHA256.
2. Independently reconstruct **all 12 parents, 72 candidates, five matched metrics per candidate, 24 keys, 48 input-pair sources, both R7/R11 ciphertexts and all 2,304 AUC and nulls**, all 12 group primary/comparator rhos and exact condition-based primary classification.
3. Force red tampering probes: changed metrics, box SHA, dropped/duplicate cell, changed AUC, wrong seed/protocol, wrong group headline statistic. All must fail. Python 3.10/11/12 CI exact head, raw evidence artifact; no CI success until actually checked.
4. Preserve every null/negative outcome and proof; all PRs remain DRAFT and no merge to `main` without independent review. Research archive is not confirmed independently durable. Full source and limitations report. Precommitted neither causal mechanism nor universal cryptographic finding.
