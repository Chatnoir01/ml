# Phase 2V–T10 — prospective ROTL11-to-MixColumns predictor transfer: NOT SUPPORTED

**Frozen preregistration before ALL T10 source generation: [`c939b4809c25087da09bc6361a534d3e2ee451ba`](https://github.com/Chatnoir01/ml/commit/c939b4809c25087da09bc6361a534d3e2ee451ba), 2026-11-19.** Research only. Does not alter the prior T7, T8, T9 or Phase2G experiments. **Zero Phase2U neural training/label inspection.**

## Question and locked method
Does the exact source-only T9 **ROTL11 early-active-byte predictor**, with its **negative sign already frozen**, predict the same four-round classical ciphertext-pair AUC after the entire ToySPN diffusion layer is replaced by an invertible 4x4 AES MixColumns linear transformation (GF(2^8), modulus 0x11B), without changing candidate generation, sampling or score direction? The original 11-bit-rotation architecture (R) is a paired fixed control; new architecture M (MixColumns) is the **only preregistered primary outcome**.

- 12 truly new random-permutation parent SBoxes, groups `906011..906660` at step 59, six affine-equivalent child variants per group = **72** unique bijections, each checked to exactly match its parent's DU/NL/maxLAT/algebraic degree/mean SAC.
- 24 new public matched key schedules, 48 disjoint fresh 128-positive+128-negative plaintext-pair sources, two fixed differences 1/256, two rounds counts 4/5.
- **2,304** fixed panels across R and M, with exact tie-aware AUC of the classical count of unchanged ciphertext-XOR bytes. Same keys, plaintexts and candidate SBoxes across R/M for paired control; no fitted neural or classical model.
- Frozen **primary success condition** for architecture M: **>=10/12** negative group-level Spearman(X,mean R4 AUC), median **<= -0.50**, null mean AUC [0.47,0.53], and all metric/source/integrity gates. No source or metric retuning after results.

## Preregistered primary result — valid NEGATIVE in independently reproduced local experiment

| Fixed measurement | Local measurement | Criterion |
|---|---:|---|
| M negative within-parent six-candidate rank correlations | **5/12** | >=10/12 required |
| M median rho | **+0.12001473964868806** | <=-0.50 required |
| All-panel shuffled-label null AUC | **0.4994071192211575** | 0.47–0.53 PASS |
| Primary feature transfer | **NOT SUPPORTED** | precommitted joint criterion failed |

| Architecture | R4 mean classical AUC | R5 mean classical AUC | Registered reference feature rho median |
|---|---:|---:|---:|
| Historical ROTL11 (R) | **0.6841250525580512** | **0.5532179408603244** | **−0.826173725804739** (12/12 negative) |
| AES MixColumns (M) | **0.4996207025316026** | **0.4999997880723741** | **+0.12001473964868806** (5/12 negative) |

### All twelve primary-group rank correlations (NO dropped failures)

| Group | M primary rho | R reference rho |
|---:|---:|---:|
| 906011 | +0.151794 | −0.091077 |
| 906070 | +0.191176 | −0.927634 |
| 906129 | −0.289886 | −0.898645 |
| 906188 | −0.115954 | −0.695725 |
| 906247 | +0.088235 | −0.840668 |
| 906306 | +0.279412 | −0.811679 |
| 906365 | +0.811679 | −0.405840 |
| 906424 | +0.235294 | −0.898645 |
| 906483 | −0.794118 | −0.405840 |
| 906542 | +0.753702 | −0.985611 |
| 906601 | −0.088273 | −0.971008 |
| 906660 | −0.371429 | −0.600000 |

## Mechanistic interpretation and essential caveat
With one nonzero input difference byte, standard AES MixColumns produces **four nonzero output difference bytes** after a single linear transformation (one nonzero field element multiplied by four nonzero matrix coefficients). This is a known MDS diffusion property and was **explicitly forecast in the T10 protocol**, not discovered after seeing results. A newly measured independent basis test checked **4×255 = 1,020** one-active-byte nonzero inputs and inverse-transform parity.

The **classical zero-output-XOR-byte distinguisher is essentially at chance already by R4 in architecture M**, so this does **not** prove that the old feature is meaningless or that the SBoxes are uniformly secure. It shows that our T9 correlation **cannot be claimed architecture-general** under this unchanged four-round score: the target has no useful signal in M. The R-reference arm retaining the previous negative correlation on entirely new sources is evidence of architecture-specific classical behavior, **not neural novelty**.

## Independent source and integrity audit
- A **source-independent local T10** program with optimized MixColumns generation produced all 2,304 original-parameter panels and full summaries; its deterministic report SHA256 is **`43f87ebbbadfccac090b5c74d7b6a99eab7cf0a1d881c67c4dea2ac572f982fa`** and raw panels SHA256 **`77a31e1de7b2d33006a2a5f63c7269155d3597b21a716611c75b5c7285b36935`**.
- A second fully independently implemented **GF(2^8) matrix** cipher and separate tie-aware rank-based AUC code successfully rederived **all 2,304/2,304 original local panels exactly**, including 12 group rank results and 1,020 MDS basis/inverse controls. Independent result saved as `t10_matrix_audit_result.json`.
- GitHub primary is `scripts/phase2v_t10_mds_transfer.py`; independent GitHub-source metric/GF matrix verifier is `scripts/phase2v_t10_independent_audit.py`; dedicated CI `.github/workflows/phase2v-t10.yml` reruns original study **twice**, then checks every panel, all five metrics, sample fingerprints and 8 deliberate corruption-controls across Python 3.10/3.11/3.12.
- Original GitHub [workflow run 44454909988](https://github.com/Chatnoir01/ml/actions/runs/44454909988) was **QUEUED** at first report registration. The independently reproduced local NEGATIVE is real, but **do NOT call exact GitHub original-source CI GREEN unless observed later**. The local evidence ZIP must be separately preserved by the owner; GitHub Actions artifacts are transient.
- The local source has no real private keys or user messages.

## Additional caution and next controls
This is a tiny 32-bit **educational ToySPN**, not actual AES. AES MixColumns **only** supplies the publicly known diffusion matrix; we did not evaluate the full AES block cipher. It does not demonstrate cryptanalytic novelty, neural resistance or secure deployment.

The next admissible study should define a new, genuinely signal-bearing outcome in a structurally distinct toy architecture **before** seeing any new data, and compare a source-only predictor against strong multi-round classical baselines. An unblinded/neural extension is excluded until independent Phase2R model-state gates and separately registered protocol. Preserve both positive T9 and negative T10 without outcome-driven switching.
