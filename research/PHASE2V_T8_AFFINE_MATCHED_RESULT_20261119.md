# Phase 2V–T8 — matched classical metrics, non-identical ToySPN distinguisher behavior

**Original measured result: 2026-11-19. Research-only. No neural training. GitHub PR #183 remains DRAFT.** The original complete preregistration was committed BEFORE data at **[`d8c5e96eeaadd3411b02071707881b9f58d223ff`](https://github.com/Chatnoir01/ml/commit/d8c5e96eeaadd3411b02071707881b9f58d223ff). No historical result, seed or sealed Phase2U neural data was consulted or changed.

## Original fixed test
Study: AES-reference affine variations generated via input/output bit permutations and XOR constants, six per each of **12 registered groups** (72 distinct SBoxes), all same classical headline metrics, subjected to matched-draw, shared-public-key 32-bit ToySPN zero-ciphertext-difference-byte count AUC at 4 vs 5 rounds, two differences (1,256), two key arms and two independent plaintext schedules: **1,152 panel scores**.

Exact base AES metrics, independently computed for original and all 72 variants:

| Classical metric | Identical verified value |
|---|---:|
| Differential uniformity | **4** |
| Vectorial nonlinearity | **112** |
| Maximum absolute LAT correlation | **32** |
| Maximum algebraic degree | **7** |
| Aggregate SAC | **0.5048828125** |

These are mathematical affine-equivalence invariants (and the average SAC is preserved by the *restricted bit-permutation* transforms). Individual local difference patterns and the composed ToySPN behavior need not be equal.

## Exact original GitHub measurement and engineering RED → GREEN
- **RED:** first real [GitHub Actions run 44450394274](https://github.com/Chatnoir01/ml/actions/runs/44450394274) completed all panel calculations but deliberately blocked output on a **bad expected independent AUC spotcheck count**: 96 expected vs 192 performed.
- **GREEN:** corrected only the assertion constant, not protocol, candidates, keys, input pair schedules, scores, metrics or acceptance criterion. Exact [GitHub run 44450542541](https://github.com/Chatnoir01/ml/actions/runs/44450542541) succeeded on `2fba27544c268363f1feedc52a606fe40200bea7`.
- Original primary result JSON canonical SHA-256: **`3b119b704aa658070f286dff5b58dc4a5c0903fcf010d4bf22b119c64d1457f6`**. This hash was locked into subsequent independent multi-Python workflow.

### Preregistered result and measurements

| Fixed measurement | Actual |
|---|---:|
| Positive R4 between-replicate 6-SBox Spearman groups | **11/12** |
| Median between-replicate Spearman | **0.5714285714285714** |
| Required thresholds | >=10/12 positive, median >=0.50 |
| Mean all-panel shuffled-label AUC | **0.5001516342163086** |
| Required null quality interval | [0.47, 0.53] |
| **Primary prospective directional criterion** | **SUPPORTED** |
| R4 classical AUC mean | **0.6778382725185819** |
| R5 classical AUC mean | **0.5496300061543783** |
| Secondary median cross-key Spearman within each group | **0.4** |
| Secondary median source-only early-diffusion ↔ R4 AUC Spearman | **−0.5661549817732507** |

### Independent 12-group values (replicate R4 rho and exploratory source-only descriptor rho)
| Group | Replicate rho | Early-diffusion rho | Key-arm rho |
| ---: | ---: | ---: | ---: |
| 904011 | 0.771429 | −0.394665 | 0.942857 |
| 904058 | **−0.142857** | −0.115954 | −0.714286 |
| 904105 | 0.428571 | −0.753702 | 0.542857 |
| 904152 | 0.885714 | −0.753702 | 0.371429 |
| 904199 | 0.142857 | −0.529641 | 0.542857 |
| 904246 | 0.600000 | −0.985611 | 0.771429 |
| 904293 | 0.028571 | −0.576818 | −0.028571 |
| 904340 | 0.942857 | −0.819689 | 0.885714 |
| 904387 | 0.771429 | −0.550782 | 0.085714 |
| 904434 | 0.600000 | −0.695725 | −0.142857 |
| 904481 | 0.428571 | −0.371429 | 0.257143 |
| 904528 | 0.542857 | −0.555492 | 0.428571 |

**Caution:** 11/12 groups favorable on replicate stability does not imply that each SBox is stably ranked across new keys; median cross-key correlation **0.4** with several negative groups. All 12 groups share **one AES affine-equivalence family**, so these are not 12 new independent parent SBox families.

## Independent implementation, exact reproducibility, and current CI status
A separate local Python source reconstructed AES's SBox from finite-field inversion/affine mapping rather than importing GitHub `references.py`. It generated the exact 72 candidate transforms, 48 source schedules, 24 matched public key schedules and **all 1,152** cipher panels. Independent AUC calculations produced **exactly identical primary and secondary numeric summaries** to the original measured GitHub result. A separate algorithm checked DU/NL/LAT/degree/SAC for **all 72**, all identical to AES; source AES SHA256 `c2d8e5eed6cbebd8625fc18f81486a7733c04f9b0129ffbe974c68b90308b4f2`.

The full local independent code, 1,152 per-panel outputs, 12 group summaries, metric-checking source and SHA256SUMS were preserved as downloadable `phase2v_t8_20261119_research_bundle.zip`, **SHA256 `22f15d27853e6cf2d76f8c373de01fff92b1d14f45c17bd4034ce4b0771aee92`** in the associated ChatGPT conversation. The ZIP is not uploaded to this repository or independently verified in owner-controlled durable storage.

The separate `scripts/phase2v_t8_independent_audit.py` is committed to this branch, and `.github/workflows/phase2v-t8.yml` is configured for Python 3.10/3.11/3.12 **double full regeneration, canonical SHA check, all 1,152 panel audit, full-metric audit and six corruption-control negatives**. At the last checked timestamp the matrix was **QUEUED**, not green. Do not claim CI acceptance before observing successful exact-head runs. The original one-Python green run and independent *local* reproduction are distinct evidence sources.

## Mechanistic signal and prior art
The predeclared **source-only** projection of expected active byte count after first AES-affine SBox and ROTL11 is negatively correlated with the fixed four-round zero-byte AUC, median per-group rho **−0.566**. This is a **secondary exploratory association**, not validated external prediction, causation, or neural resistance. Testing genuinely held-out parent S-Box families and different keys/architectures, with a pre-fixed predictor and honest null, is mandatory before any broader theory.

The general effect of affine-equivalent SBoxes yielding distinct multi-round cryptanalytic properties is **not novel**. Explicit prior art: **Anne Canteaut & Joëlle Roué, EUROCRYPT 2015, *On the Behaviors of Affine Equivalent Sboxes Regarding Differential and Linear Attacks*, DOI [10.1007/978-3-662-46800-5_3](https://doi.org/10.1007/978-3-662-46800-5_3)**. Their SPN/endpoint differ from T8's toy setup, but their work already establishes the broader phenomenon. See `PHASE2V_T8_PRIOR_ART_AND_NOVELTY_BOUNDARY_20261119.md`.

## Next strictly separated research gate
**Not executed or authorized in this study:** prospectively test the locked source-only diffusion predictor on a fresh, genuinely *different SBox parent family*, independently generated keys, multiple independent control score baselines and *completely unseen* candidates. A future neural comparison requires actual Phase2R model/data initialization-state provenance, preregistration and no access to sealed Phase2U labels.

**No AES vulnerability, neural superiority, deployed cipher security, post-quantum security, new general theorem or international novelty is demonstrated by T8. No merge, train, delete, reseed or change to the original frozen work.**
