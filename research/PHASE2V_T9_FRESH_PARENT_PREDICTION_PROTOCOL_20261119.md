# Phase 2V–T9: prospective cross-parent classical prediction falsification

**Preregistered 2026-11-19 BEFORE any T9 parent S-Box, candidate, ciphertext, score or AUC generation.** This text commits the hypothesis and all methods before viewing T9 outcomes. Research-only, no neural fitting and **no access to Phase 2U's sealed 96 training outcomes**. Source cipher is the original 32-bit educational ToySPN from `main` SHA `b03da1d95e98709869d007571de4f8bbce234a1b`. T8 PR #183 is exploratory motivation only, not a source of T9 data. Keep T7/T8/2G frozen, drafts unmerged.

## Primary question
T8's post-registration *secondary* association (median within-group Spearman approximately **−0.566**) suggested that a **source-only expected number of active output-difference bytes after the first S-Box and ROTL11** might predict the AUC of a 4-round fixed classical zero-output-byte distinguisher across variations of a parent S-Box. Does this **already-chosen feature, direction and endpoint** generalize to 12 new randomly shuffled independent parent S-Boxes, each with six mutually affine-equivalent variants? No new feature selection or model fitting is allowed.

## Frozen 12 source groups, not AES affine variants
- Exactly 12 distinct source-group IDs: `905011, 905064, 905117, 905170, 905223, 905276, 905329, 905382, 905435, 905488, 905541, 905594`; no reseeding, filtering or substitute groups after outcomes.
- For each group, one independent **random parent bijection**: `random.Random(SHA256_INT("phase2v-t9-parent-v1|GROUP")).shuffle(list(range(256)))`. SHA256_INT means unsigned big-endian integer from all 32 SHA256 digest bytes of the ASCII domain string.
- For each (group, variant index 0..5), derive `rng=random.Random(SHA256_INT("phase2v-t9-variant-v1|GROUP|INDEX"))`. Independently shuffle `pin=list(range(8))` and `pout=list(range(8))`. Generate input and output XOR offsets `a,b=rng.getrandbits(8)`. The candidate is `S'(x)=bit_permute_pout(PARENT[bit_permute_pin(x) XOR a]) XOR b`, with bit_permute(x,p)=Σ_{i=0}^7(((x>>i)&1)<<p[i]).
- Exactly **12 parent boxes** and **72 transformed variants**, source-unique by SHA256. All transformations are bijections. Every variant must have the same 5 full global metrics as its corresponding parent, computed by real repository `cryptoshield.py`: DU, NL, max absolute LAT, algebraic degree and mean SAC. Parent metrics may differ between groups; do NOT interpret groups as matched against each other. Any duplicate source, metric failure, or invalid candidate makes the **whole T9 INVALID**, not an opportunity to select a different seed.
- This generates independent *random parent permutation sources*, NOT a formal proof of 12 mathematically inequivalent affine orbits. Such a proof is outside scope; describe the limitation.

## Fixed unkeyed feature (BEFORE test labels)
For each candidate S' and each fixed input difference delta in {1,256}, let the active SBox input byte lane be `lane=0` (delta1) or `lane=1` (delta256), and compute
`E_delta(S') = 1/256 * Σ_{x=0}^{255} count_nonzero_bytes(ROTL32((S'(x) XOR S'(x XOR 1)) << (8*lane),11))`.
The single preregistered predictor `X(S') = (E_1(S') + E_256(S'))/2`. Higher X predicts **lower** 4-round AUC. This feature is frozen from T8 and uses only public SBox tables, not ciphertext scores or labels. It can be unchanged by some transforms; midrank Spearman tie handling is mandatory, constant-vector correlation defined as 0 and included as failure if no negative relation.

## Frozen keys, data, score and outcome
- Two public key-arm labels `K0,K1` per group, **shared among six candidate variants within group** but independent across groups. Each of six 32-bit words is `int.from_bytes(SHA256(ascii("phase2v-t9-key-v1|GROUP|ARM|WORD_INDEX"))[:4],"big")` for indices 0..5; 24 distinct full schedules. R4 uses first 5 words, R5 all six.
- Two input differences `1,256`, two replicate schedules `0,1` per (group,delta), so **48 distinct schedules**. Each uses `random.Random(SHA256_INT("phase2v-t9-pairs-v1|GROUP|DELTA|REPLICATE"))`. For each schedule: exactly 128 positive pairs `(p,p XOR delta)` and 128 negative pairs `(p,q)`, where `p!=q` and `p XOR q != delta`. Draw plaintext words with `getrandbits(32)`, reject any reused block within schedule across classes; cap at 50,000 candidate draws. Replicates 0/1 must have **zero shared plaintext blocks** within group/delta. The same schedule is deliberately shared across variants, key arms and rounds to obtain a matched comparison. Do not discard or replace any random-collision group; stop study INVALID.
- `ToySPN` encryption: 32-bit state, XOR roundkey, bytewise bijective SBox, ROTL11 between rounds, final key XOR. Exactly **4 and 5** rounds. Cipher validated against independently written bytewise reference, decryption round-trip, source hash and fixed public test vectors before outcome.
- `12 groups×6 variants×2 keys×2 differences×2 replicates×2 rounds=1152` complete panels, balanced 128+128 pairs each. Fixed score per ciphertext pair is `count_zero_bytes(ciphertext_a XOR ciphertext_b)` (0..4), larger score means positive. **No training**. Exact tie-aware AUC via discrete count U-statistic, independently checked against direct positive-negative enumeration. Null shuffles the 256 labels (128/128 unchanged) with `random.Random(SHA256_INT("phase2v-t9-null-v1|GROUP|BOX_SHA256|ARM|DELTA|REP|ROUNDS"))`. Report all 1152 AUC, null AUC, positive/negative any-zero-byte rates.

## Registered PRIMARY ENDPOINT and strictly frozen success criterion
For each group and six variants, define `Y(S')` = mean **R4** AUC across its 2 key arms × 2 input deltas × 2 independent replicate schedules (8 fixed cells). Calculate **tie-aware Spearman correlation** (midranks, Pearson-on-ranks) of `X(S')` and `Y(S')` across the six variants of that *one parent*; constant X or Y -> rho=0. The unit is **12 independent parent-group labels**, not 72 SBoxes or 1152 panels treated as IID.

The old T8 suggested a **negative** relation. Declare this new source-independent replication **SUPPORTED** only if:
  1. **At least 10/12** separate parent-group Spearman values are **strictly below 0**, AND
  2. The **median Spearman** over all twelve groups is **<= −0.50**, AND
  3. Mean shuffled-label AUC over 1,152 panels is in **[0.47,0.53]**, AND
  4. All metric, source, seed, sample, cipher, anti-reuse and non-tampering gates pass.

Otherwise **NOT SUPPORTED**, or **INVALID** if a hard scientific integrity gate fails. No alternative favorable score signs, exclusion of non-negative groups, post-result changes to statistics, feature or thresholds, subgroup selection or reinterpretation as neural success.

## Prespecified SECONDARY checks (all descriptive, never promote to primary)
- Per-group R4 source-only predictor correlation under K0 only and K1 only, and under replicate 0 only and replicate 1 only; group medians and counts of negative direction. Report any key-specific reversals; K0/K1 do NOT need to agree for primary qualification.
- Per-group R5 source-only predictor correlation and R4→R5 median AUC change.
- Per-group range of six variant R4 mean AUCs and first-round predictor descriptor; mean full-data R4/R5 AUC. Include 12 parent metrics, 72 candidate SHA256 and all primary raw values.
- Source descriptor null by fixed label shuffle of six `Y` candidate values within each group using `SHA256_INT("phase2v-t9-feature-null-v1|GROUP")` to expose chance correlation, but no significance claim or selection based on it.
- T8 historical row outcomes are not loaded by T9; no new neural labels; no Phase2U model execution.

## Integrity and reproducibility rules
- Entire protocol existed on GitHub BEFORE candidate/data calculation; record exact commit SHA. Scripts committed separately after protocol. Keep every failure and negative verdict.
- Original execution must reproducibly emit byte-for-byte canonical `json.dumps(sort_keys=True,separators=(',',':'),ensure_ascii=True)+'\\n'` twice on the unchanged code; log SHA256.
- Independent verifier must regenerate 12 random parents, all 72 candidate SBoxes and full classical metrics, 24 key schedules and 48 independent input schedules; independently reproduce **all 1,152 ciphertext panels** and exact AUC/null/group correlations. Include fail-closed intentional corruption tests for changed AUC, candidate fingerprint, raw count, source SHA, group correlation and duplicate/missing rows. Run Python 3.10/3.11/3.12 GitHub Actions matrix with raw output artifact and bounded resource limits. Do not claim green until actually observed.
- No deployment claims, real AES weaknesses, stable multi-key security ranking, neural originality, newly discovered general affine equivalence theory, or adaptive evolution superiority. The T8 result is not a demonstration of global novelty (see Canteaut & Roué, EUROCRYPT 2015).

## Follow-on decision
If T9 supports the feature, independent different cipher architecture and more out-of-family parental controls with honest prior-art evaluation remain required. If T9 fails, preserve the result and do NOT expand the feature by tuning on these 12 groups while calling it prospective. Subsequent neural research remains subject to the separately documented Phase2R model-state gate and Phase2U sealing.
