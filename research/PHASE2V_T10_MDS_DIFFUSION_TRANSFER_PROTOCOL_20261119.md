# Phase 2V–T10 — source-only predictor transfer from ROTL11 to AES-MixColumns diffusion
**Research preregistration — 2026-11-19. THIS FILE MUST BE COMMITTED BEFORE generating any T10 parent S-Box, experimental key schedule, plaintext pair, ciphertext, panel AUC or scientific result.**
This experiment is isolated from T8/T9 and all Phase2U sealed neural runs. T9 GitHub 3-version CI is queued as of registration; do not treat any T9 preliminary local result as confirmed CI. No new neural fits or production cipher use. Source `main` SHA `b03da1d95e98709869d007571de4f8bbce234a1b` supplies the reference `ToySPN`, metrics and research semantics.

## Hypothesis being falsified
T9 selected **before its independent random-parent outcomes** a source-only S-Box scalar:
`X(S) = (E_ROTL11(S,1)+E_ROTL11(S,256))/2`, where `E` enumerates all 256 input byte values and counts the active 8-bit state bytes after applying the S-Box difference and ROTL32 by 11 bits, starting in the appropriate byte lane. Higher X predicts **lower** AUC at 4 rounds for the fixed classical score `zero_byte_count(encrypt(p) XOR encrypt(q))`.
T10 asks whether this **UNCHANGED, ROTL11-SPECIFIC X and negative sign** can still predict R4 AUC after **replacing the entire inter-round bit-rotation layer** with the standard four-byte Rijndael/AES MixColumns matrix over GF(2^8). There will be no fitting or new choice of feature, threshold, difference, key, score, architecture or arm based on T10 outcomes. The reference ROTL11 architecture is also measured in parallel as a fixed comparison and sanity control, but **the primary endpoint is MixColumns only**.

## Frozen cohort (new sources, all original values withheld until protocol committed)
- Exactly **12 independently seeded parent-source groups**: `(906011,906070,906129,906188,906247,906306,906365,906424,906483,906542,906601,906660)`. Each parent is a uniformly shuffled permutation of bytes: `random.Random(SHA256_INT("phase2v-t10-parent-v1|GROUP")).shuffle(list(range(256)))`; full SHA256 digest interpreted as big-endian integer.
- Exactly six candidate variants INDEX 0..5 per parent. `random.Random(SHA256_INT("phase2v-t10-variant-v1|GROUP|INDEX"))` independently shuffles `pin,pout=list(range(8))`; draws `a=rng.getrandbits(8)`, `b=rng.getrandbits(8)`; `S'(x)=P_pout(PARENT[P_pin(x) XOR a]) XOR b`, where `P_p(x)=sum((((x>>i)&1)<<p[i]) for i=0..7)`. Exactly **12 unique parents and 72 unique variants**, all bijective, SHA256 fingerprinted; any duplicate or nonbijection => INVALID, no reseeding.
- Within each group all six variants must match the parent's **five headline metrics exactly**, computed with actual `cryptoshield` functions: differential uniformity (DU), vectorial nonlinearity (NL), maximum absolute linear correlation (maxLAT), maximum algebraic degree, mean strict-avalanche score SAC; parent metrics may differ across the 12 groups. Verify each via second independent metric implementation. Six variants share one parent affine family, **not 72 independent parent families**.
- Exact original T9 X formula: for delta 1 active lane 0, for 256 lane 1; `(S'(x)^S'(x^1))<<(8*lane)`, `ROTL32(.,11)`, count nonzero bytes, average over x=0..255 and the two deltas. Compute from S-Box only. It is NOT recalculated for MixColumns and is not a fitted regression coefficient.

## Frozen two architectures
Architecture **R** (historical reference): source `ToySPN` with bytewise S-Box, XOR round keys, 11-bit left rotation after every round except last, final whitening XOR.
Architecture **M** (new independent toy SPN): exactly the same 32-bit state, bytewise S-Box and key XOR and last-round whitening, but replace each inter-round rotation by AES MixColumns on the entire 4-byte state in high-to-low byte order with 4x4 forward matrix:
`[[2,3,1,1],[1,2,3,1],[1,1,2,3],[3,1,1,2]]`.
GF(2^8) field uses polynomial `0x11B` and AES multiplication, no key dependency. Standard inverse matrix is `[[14,11,13,9],[9,14,11,13],[13,9,14,11],[11,13,9,14]]`; verify inverse on all four nonzero one-byte lanes and all 255 possible nonzero bytes, plus random 32-bit values. **R and M are two different fixed diffusion architectures, not AES encryption.**
Both use exactly four and five rounds, 4-round key prefix of the same six-word public key schedule; verify known end-to-end roundtrip, independent forward M implementation, and no unexpected cross-protocol data reuse for any panel.

## Frozen keys, pairs, panels and score
- 2 key arms `K0,K1` per parent group; each is **shared over all six variants and both architectures** for matched control, separate across groups; six public 32-bit words `int.from_bytes(SHA256("phase2v-t10-key-v1|GROUP|ARM|WORD_INDEX")[:4],"big")`, 0<=INDEX<=5, 24 unique key schedules.
- XOR input differences: exactly `1` and `256`. Two independent plaintext pair sources per (group,delta), replicate 0/1: `random.Random(SHA256_INT("phase2v-t10-pairs-v1|GROUP|DELTA|REPLICATE"))`. Each has precisely 128 positives `(p,p XOR delta)` and 128 negative independent `(p,q)`, excluding same block/delta. Sample via `getrandbits(32)`; reject plaintext-block reuse in each 256-row source, cross-replicate any block overlap is HARD INVALID; 50,000 maximum draw attempts per source. **48 original paired sources** reused across six variants, both architectures, both keys, 4/5 rounds (by design).
- Exactly `12 groups × 6 variants × 2 architectures × 2 keys × 2 deltas × 2 pair replicates × 2 depths = 2,304 balanced AUC panels`, each with 128 positive and 128 negative. Score `S=count of zero-valued XOR bytes between ciphertext blocks`, range 0..4, **higher S means positive**, fixed direction. Tie-aware U-statistic AUC computed from class histograms, and independent direct pair enumeration on registered deterministic edge cells.
- Label-permutation null on the exact observed score list, permuting 256 labels while retaining 128/128 class counts, with `random.Random(SHA256_INT("phase2v-t10-null-v1|GROUP|BOX_SHA256|ARCH|ARM|DELTA|REP|ROUNDS"))`. Mean null AUC across ALL 2,304 panels must lie between 0.47 and 0.53. Do not use alternative random seed or reshuffle for better p-value.

## Preregistered PRIMARY test, T9 feature transport
For each group/variant `Y_M(S')` is the arithmetic mean R4 **M architecture** AUC over 2 key arms ×2 input deltas ×2 plaintext replicates (8 panels). Compute exact **Spearman with averaged ranks for ties** between six precomputed X values and six Y_M values; a zero-variance feature or target has rho=0. The primary sample size is **12 parent groups** (NOT 72 or 2,304 IID observations).

The T9 negative-direction feature **transfers to new architecture M** only if **all**:
1. at least **10 of 12** group Spearman(X,Y_M) are **strictly negative**;
2. median of all 12 group correlations is **at most −0.50**;
3. full 2,304-panel shuffled-label null average in [0.47,0.53];
4. every parent/metric/pair/round/diffusion/source/audit gate passes.

If 1 or 2 fails with source gates valid, report `NOT_SUPPORTED`. If a hard source gate fails report `INVALID`, not scientific negative. Do not drop groups with constant features or null-like M targets. No post-result threshold changes, source reselection, endpoint switching to R architecture, or altered model to rescue negatives. No formal pooled panel-level p-values.

## Fixed SECONDARY outcomes (describe regardless of primary)
- Same rank correlation of X to R architecture R4 AUC for the 12 new groups; report observed number negative and median (not an alternative main claim).
- For M: R4 and R5 mean and per-group AUC, key-arm specific rankings, across-six-variant R4 AUC span per group, and source-feature within-group range. R4→R5 change and positive-vs-negative any-zero byte frequencies; do NOT promote good secondary values.
- **A priori diffusion diagnostic:** for M architecture each one-active-byte input to MixColumns produces **four active output bytes** regardless of SBox permutation because each nonzero GF(2^8) input difference is multiplied by nonzero constants {1,2,3}; verify all 4×255 nonzero one-byte basis inputs and report the exact constant four-active-byte expectation. This calculation is a structural *reason a geometry-dependent T9 feature may fail to transport*, not a new predictor.
- Per-group M AUC signal floor and independence: if the fixed classical distinguisher is at 0.5 after full diffusion, label `not enough exploitable signal` rather than `feature disproved in general`. All 12 group rows preserved.
- Descriptive source-only detail and existing prior art: AES/Rijndael MixColumns MDS matrix and affine-equivalent S-Box multi-round differences are known. No novelty claim, deployed AES weakness, production security or neural finding.

## Hard scientific engineering, retention and follow-up
Run exact T10 program twice (byte-identical canonical JSON and SHA256), then rederive every candidate/key/pair/cipher score/null and all 2,304 AUC with a **second independent implementation**; validate metrics with independent Walsh/DDT/ANF, and 8+ intentional corruption-failure tests. Python 3.10/3.11/3.12 GitHub Actions on the exact finalized commit and raw evidence artifact. Human owner controls preservation beyond temporary GitHub retention. No merge to main without review. Keep prior T8/T9/2G frozen, Phase2U sealed; no Phase2R-bypassing neural fits. The next neural experiment, if warranted, must be separately preregistered and compared with stronger classical baselines.

**Precomputation is forbidden before this protocol's recorded source commit. Result negative, positive, invalid or inconclusive must be preserved as observed.**
