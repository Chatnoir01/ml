# Phase 2V–T11 — R7 vs R11, four frozen classical predictors: valid negative

**Research result frozen 2026-11-19.** Original preregistration SHA **[`207331148f05689f288d6b510e524db8668d41b2`](https://github.com/Chatnoir01/ml/commit/207331148f05689f288d6b510e524db8668d41b2)** existed **before T11 SBoxes/keys/ciphertexts or results**. T11 study source is `scripts/phase2v_t11_rotation7_controls.py`, accompanied by independently coded metric/cipher/AUC verifier `scripts/phase2v_t11_independent_audit.py`. No Phase2U neural runs, Phase2G changes, T9/T10 retrospective rewrites or production cipher deployment.

## Question
T10 showed the originally learned-within-ToySPN-ROTL11 *source-only first-round active-byte geometry* feature failed after substituting AES MixColumns (AUC ≈0.5). The new T11 preregistered a distinct SPN that rotates the 32-bit state by **7 bits** between rounds (R7), compared pairwise with original 11-bit rotation (R11); it tests a new **rotation-7 matched version of the exact same mathematical feature**, against three fixed controls: old F11, DDT row-1 collision probability, and DDT row-1 maximum probability. DDT controls have *positive* directional predictions, F7/F11 have *negative* directional predictions.

All scientific inputs are new: exactly 12 independently shuffled random parent SBoxes (groups 907011 through 907682, step 61), 6 affine child variants each, 72 exact parent-metric-matched candidate boxes, 24 public group key schedules, 48 pair schedules, two XOR input deltas 1/256, two replicates, both R7/R11 ciphers, rounds 4/5, **2,304 panels** balanced 128 positive + 128 negative each. An unbiased-label permutation over each unchanged score panel provides a no-signal check; no model is trained.

## Locked primary result, negative (two locally byte-identical replications and a second implementation)

| Strict preregistered primary measure | Threshold | Observed |
| --- | --- | --- |
| Mean R7 AUC at 4 rounds | >=0.55 signal floor | **0.9337608019510905 — PASS** |
| Negative within-parent 6-SBox Spearman(F7,R7 AUC) groups | >=10/12 | **9/12 — FAIL** |
| Median of all 12 group Spearman | <= −0.50 | **−0.2571428571428571 — FAIL** |
| Label-shuffled null mean over all 2,304 panels | [0.47,0.53] | **0.5008240540822347 — PASS** |
| Exact key/sampling/SBox/global-metric cardinality | All complete | **12 parents,72 candidates,24 keys,48 sources,2,304 panels** |
| **Official preregistered classification** | All required | **NOT_SUPPORTED** |

**This negative result is not the same as T10's AUC-at-chance limitation:** the fixed classical R7 distinguisher has plenty of signal (AUC ≈0.934), albeit close enough to the ceiling that candidate-level AUC variation may be compressed. Median within-parent 6-candidate R7 mean-AUC range across groups ≈ **0.0311**; signals should not be interpreted as broad cryptanalytic superiority.

Reference arm R11 mean AUC: **R4 0.6846888330247667**, R5 **0.5531198183695475**. New arm R7: **R4 0.9337608019510905**, R5 **0.8401698536343045**. This does not make R7 insecure for all adversaries or R11 secure; it measures only one particular 32-bit toy distinguisher.

## All twelve group outcomes — no hidden unfavorable seeds

| Group | rho(F7,R7) PRIMARY | rho(F11,R7) | rho(D1coll,R7) | rho(D1max,R7) |
| ---: | ---: | ---: | ---: | ---: |
| 907011 | −0.085714 | −0.085714 | −0.617914 | −0.683130 |
| 907072 | **0.000000** | −0.828571 | +0.576818 | −0.392792 |
| 907133 | **+0.028989** | +0.318874 | −0.294245 | −0.292770 |
| 907194 | **+0.811679** | −0.405840 | +0.621059 | −0.878310 |
| 907255 | −0.142857 | +0.235396 | −0.028989 | +0.207020 |
| 907316 | −0.811679 | −0.371429 | −0.277746 | +0.304256 |
| 907377 | −0.657143 | −0.058849 | +0.030359 | 0.000000 |
| 907438 | −0.828571 | +0.057977 | +0.212512 | 0.000000 |
| 907499 | −0.550782 | −0.657143 | +0.405840 | +0.185164 |
| 907560 | −0.257143 | +0.898645 | +0.030359 | −0.654654 |
| 907621 | −0.318874 | −0.173931 | −0.277746 | −0.277746 |
| 907682 | −0.257143 | −0.318874 | +0.169031 | +0.654654 |

### Prespecified secondary comparators — descriptive ONLY

| Source-only classical statistic | Expected rho direction | 12-group median rho | Groups correctly directed |
| --- | --- | ---: | ---: |
| F7 active-byte expectation after ROTL7 | negative | −0.257143 | **9/12** |
| Original F11 active-byte expectation after ROTL11 | negative | −0.129823 | **8/12** |
| DDT[1] collision probability | positive | +0.030359 | **7/12** |
| DDT[1] maximum differential frequency | positive | −0.138873 | **4/12** |

Even though F7 is more aligned to the expected direction descriptively than these three controls, **it failed the original positive criterion**. No posthoc superiority, no multi-round state-of-the-art baseline claim, no p-value pooling 2,304 dependent panels and **no neural-resistance claim**.

## Engineering and reproducibility
- Exact source registration on GitHub predates the local original-parameter independent implementation.
- Local source-independent `t11_independent_local.py`, using standard Python and newly seeded parental box construction, executed twice; two JSON files were **byte-identical** across repetitions:
  - canonical complete **2,304-panel** rows SHA256: `4f3110519fe7f51518ba76b0e46e04324096389bcec7451ec8752cfd228d0902`;
  - canonical summary and all twelve group outcomes SHA256: `c3fd60786e53fd642f33fbc7561bd71f6f366c89f6f7f7dacca924ff0464be25`.
- A **second non-importing local implementation** `t11_independent_second_audit.py` rederived the new parent SBoxes, their affine variants, the input schedule, all **2,304 AUC and shuffled-label AUCs** through separate exact-rank statistic and cipher code, and every registered 12 group primary score **with no divergence**. It does not import the first local study, ToySPN or the primary GitHub program. It also independently checked plaintext pair nonreuse, 72 distinct candidate identifiers and group/source totals.
- Actual GitHub-source implementation `scripts/phase2v_t11_rotation7_controls.py` uses original ToySPN for R11, a distinct inverse-capable R7 SPN and actual classical full-metric functions from the source repository; the GitHub-side independent auditor independently recalculates all five global metrics, generated SBoxes, ciphertext scores, nulls and 12 group comparator correlations.
- Dedicated `.github/workflows/phase2v-t11.yml` on Python 3.10/3.11/3.12 runs exact experiment twice, byte comparison, full independent audit and nine intentional mutation-rejection tests. **Status at initial report time: QUEUED**, not certified green. This external CI is separate from local two-implementation verification. Do not assert fully GitHub validated until exact-head jobs pass.
- Standalone local ZIP is provided in the generating ChatGPT conversation, with original local code, results, second audit, README and SHA256SUMS; **no proof of durable owner-controlled archive**.

## Scientific interpretation and next path
The new architecture R7 shows a **very high four-round classical AUC** but the simple, preregistered first-round activity feature fails to predict its *within-parent six-variant differences* to the required standard. Saturation of the score and accumulated *multi-round* differential/linear effects could explain this. These are **hypotheses, not measured causal conclusions**.

This result prevents upgrading T9's successful ROTL11-specific predictor into a general cryptographic structural invariant. It also shows that merely matching the modified architecture's first-round rotation does not guarantee predictive generalization. Compare with multi-round DDT propagation in a separately frozen prospective test; consider different depths where both architectures retain statistically discriminating variability. Any neural claims remain blocked by separate Phase2R model-state prerequisites and Phase2U seals.

**No real AES weakness, secure encryption design, post-quantum property, novel universal theorem, or neural superiority follows from this toy result. The T11 negative is retained as scientific evidence.**
