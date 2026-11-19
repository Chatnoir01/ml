# Phase 2V–T7 — input-difference activity: source-independent ToySPN result
**19 November 2026 • Research-only • Original preregistration first • No Phase 2U neural labels.**

## Exact preregistration and executable
- The protocol was committed **before T7 outcome generation** at [`4d44c2702d98f27fd2b43cb935942323a432e4a6`](https://github.com/Chatnoir01/ml/commit/4d44c2702d98f27fd2b43cb935942323a432e4a6): `research/PHASE2V_T7_INPUT_ACTIVITY_PROTOCOL_20261119.md`.
- Experimental source: `scripts/phase2v_t7_input_activity.py`, operating against actual `src/adversarial_sbox/spn.py` at `main` SHA `b03da1d95e98709869d007571de4f8bbce234a1b`.
- 12 independent fresh `903xxx` evolution-group IDs; 8 deterministic shuffled 8×8 bijective S-Boxes each = **96 distinct** boxes, all SHA256-fingerprinted; **96 distinct public deterministic key schedules**, **384 distinct plaintext schedules**.
- Exact fixed XOR differences `0x00000001`, `0x00000100`, `0x00010100`, `0x01010101`; exact 4- and 5-round original ToySPN; 128 positive + 128 negative ciphertext pairs per panel; **768/768** complete evaluation panels.
- Registered classical score = count of unchanged ciphertext-XOR output bytes, 0..4, direction fixed in advance; no fitted features, no neural model training or user data.

## Primary result
The registered hypothesis required at least **10/12 strictly positive** independent-group differences between the mean 1-byte-input-delta AUC and the 4-byte-input-delta AUC at 4 rounds, with **median difference >= 0.05**, plus a permutation-label control mean AUC in [0.47,0.53].

| Locked metric | Observed |
| --- | ---: |
| Four-round 1-byte delta `0x1` AUC mean | 0.6843461990356445 |
| Four-round 1-byte delta `0x100` AUC mean | 0.6846564610799154 |
| Four-round 2-byte delta `0x10100` AUC mean | 0.5277970631917318 |
| Four-round 4-byte delta `0x1010101` AUC mean | 0.49959278106689453 |
| Positive group contrasts | **12 / 12** |
| Median 4-round group contrast | **0.1852273941040039** |
| Shuffled-label mean null AUC (all 768) | **0.5002166032791138** |
| Registered directional decision | **SUPPORTED** |

### Registered secondary outcomes
| Input XOR activity | Four-round AUC | Five-round AUC |
| --- | ---: | ---: |
| Single active byte, `0x1` | 0.6843461990356445 | 0.5522028605143229 |
| Single active byte, `0x100` | 0.6846564610799154 | 0.5531400044759115 |
| Two active bytes, `0x10100` | 0.5277970631917318 | 0.506190299987793 |
| Four active bytes, `0x1010101` | 0.49959278106689453 | 0.49951171875 |

The median registered R5 one-byte minus four-byte group contrast was **0.053012847900390625**.

### Twelve independent group summaries (R4/R5 contrast)
| Group | R4 | R5 |
| ---: | ---: | ---: |
| 903011 | 0.185966 | 0.051598 |
| 903048 | 0.182974 | 0.051643 |
| 903085 | 0.153671 | 0.041334 |
| 903122 | 0.184488 | 0.055275 |
| 903159 | 0.183872 | 0.055536 |
| 903196 | 0.194998 | 0.060682 |
| 903233 | 0.197994 | 0.060190 |
| 903270 | 0.186920 | 0.050426 |
| 903307 | 0.178455 | 0.055723 |
| 903344 | 0.182932 | 0.049482 |
| 903381 | 0.188431 | 0.052177 |
| 903418 | 0.198200 | 0.053848 |

## Reproducibility and corruption checks
- Local complete canonical output SHA-256: **`7225a3823d3e57d583d2b2f1b000e839a9a7371f0046bcb7601384dc7a4dfd1e`**.
- Locally regenerated the **entire dataset three times**; all three JSON byte streams matched that exact SHA.
- Built a second standard-library-only cipher/data/score implementation (does not import ToySPN or primary script), regenerated **768/768** original ciphertext-score panels, **384/384** pair sources, **96/96** S-Boxes, and checked all AUCs, null controls, group contrasts and source fingerprints. All passed.
- Negative controls: independent auditor rejected **5/5** deliberately corrupted output variants (AUC, pair-source SHA, panel deletion, group summary, null AUC).
- Full primary canonical raw JSON and second independent auditor are available in the companion conversation-generated downloadable research bundle. **They are not yet represented by an independent CI artifact or long-term owner-controlled archive.**
- An additional GitHub Actions run on this exact source is required before asserting CI provenance. Passing future CI would verify numerical reproduction, not cryptanalytic generality.

## Scientific interpretation and strict boundary
The fixed and elementary zero-XOR-byte score detects one-active-byte plaintext XOR differences far more often than four-active-byte differences after **four** rounds of the given **32-bit educational ToySPN**. At five rounds the same score is closer to random, with a much smaller contrast.

This is a prespecified fresh controlled empirical effect **within this cipher, its rotation 11 and selected differences**. It is not necessarily a new property in the world's cryptographic literature: differential activity and diffusion are known. It does **not** demonstrate a previously unknown S-Box-specific feature, predict neural ranking, explain Phase 2A-T/U2, change frozen Phase 2G negative findings, prove AES weakness or justify cryptographic deployment.

**Next scientific hypothesis, not tested here:** find a source-only, preregistered predictor that explains held-out differences **among** S-Boxes even when major classical metrics match; validate it on fresh unseen candidate families with independent neural baselines after Phase 2R comparability gates. Do not use or unseal the 96 Phase 2U neural outcomes as a development set.
