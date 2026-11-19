# Phase 2V–T9 — source-only diffusion feature on fresh random-parent SBoxes

**2026-11-19. Prospective fixed protocol SHA `7cec70cbcff7ffb4dcb01f39c160867142e25c47` committed BEFORE T9 source generation or observed outcome.** This report records the **independent local original-parameter replication**, which was executed after preregistration. The independently executed **GitHub source and original-GitHub report SHA still require finished CI**; do not conflate local results with CI. No new neural model training, no Phase2U unsealing, no modifications to historical negative/positive records.

## Exact scientific question
The *preselected, source-only* feature is the expected count of active output-difference bytes after one SBox plus the ToySPN's 11-bit rotation for fixed input differences `1` and `256`. The T8 **secondary descriptive** result showed within-AES-affine-group rho approximately −0.566. T9 tests this same feature and sign **without tuning** against an **independently generated cohort of twelve random-permutation parent sources**, with six affine equivalent candidates per parent, and a locked four-round **classical** zero-output-XOR-byte AUC target.

The new cohort consists of 12 independent parent shuffles and **72/72 distinct bijective transformed candidates**. Within each parent group, all six boxes were independently checked to have equal DU/NL/max absolute LAT/algebraic degree/mean SAC to that parent; **parent metrics differ among groups**, e.g. DU 10–14 and NL 92–96. The 12 random sources are distinct as bytes but **not formally proven to be distinct affine-equivalence orbits**.

## Precommitted primary criteria and independently measured local results

| Registration item | Criterion | Local result |
| --- | --- | --- |
| Group-level within-parent Spearman(X,mean_R4_AUC) | >=10 of 12 strictly negative | **10/12 negative** |
| Median of all 12 Spearman values | <= −0.50 | **−0.7714285714285715** |
| Mean shuffled-label AUC over all 1,152 panels | [0.47,0.53] | **0.4996459749009874** |
| Exact source/metric/pairing/panel controls | All must pass | **12 parents, 72 candidate boxes, 24 public key schedules, 48 source schedules, 1,152 balanced panels** |
| Registered joint decision | All above | **SUPPORTED (local independent run)** |

The 12 registered group correlations are retained **without dropping unfavorable or null groups**:

| Parent-group ID | Registered predictor rho |
| ---: | ---: |
| 905011 | −0.882735 |
| 905064 | **+0.338062** |
| 905117 | −0.771429 |
| 905170 | −0.308607 |
| 905223 | −0.811679 |
| 905276 | −0.985611 |
| 905329 | −0.828571 |
| 905382 | −0.376851 |
| 905435 | **0.000000** |
| 905488 | −0.333947 |
| 905541 | −0.942857 |
| 905594 | −0.771429 |

**Prespecified secondary checks, not separate confirmatory findings:** among the twelve groups the fixed feature has a negative correlation in K0-only panels in **10/12** groups and K1-only panels in **11/12** groups. Overall mean fixed classical AUC: **R4 0.6878697607252333**, **R5 0.5542416572570801**. A pre-fixed single feature-null rank shuffle has median rho **−0.23670441264761125**; one shuffle per group is merely diagnostic and not a power-calibrated statistical control or formal p-value.

## Reproducibility and provenance
- **Original scientific preregistration:** `7cec70cbcff7ffb4dcb01f39c160867142e25c47` (prior to candidate/data/outcome generation).
- **Primary experiment source on this GitHub branch:** `scripts/phase2v_t9_cross_parent_prediction.py`, faithfully importing the main ToySPN and classical full-metric implementations.
- **Second GitHub-source full audit:** `scripts/phase2v_t9_independent_audit.py`, independently implementing source generation, full classical metric calculation, cipher and all raw AUC+null+group fields.
- **Local source-independent implementation** is bundled as the separate standard-library-only `t9_independent_local.py`, using a bundled locally authored `t8_independent_local.py` purely for general score and arithmetic helpers, **not importing the project's original experiment/ToySPN or cryptoshield**.
- Local primary summary file **SHA-256 `02ee275b8664b37c5a65dd5c4ff7b6356b39eb565c32b7169c3f8cbd2cfaa05f`**; full 1,152 panel file **SHA-256 `5d22485a1bd1210802535a674cf130542f46dbf6246944e641def1b9b914c4be`**.
- Two independent local repetitions and a **fresh extracted-folder reproduction** produced both result files **BYTE-IDENTICALLY**. The clean bundle `phase2v_t9_20261119_research_bundle.zip` is **24,242 bytes, SHA256 `4e28aed57e18b8295f95916db65e00d7ced2462be0bc25734bbe8bbb13123496`**, downloadable in the generating ChatGPT conversation; **not verified in long-term user-owned storage or uploaded to GitHub**.
- Dedicated `.github/workflows/phase2v-t9.yml` contains Python 3.10/3.11/3.12 double replication and an independent 1,152-panel/72-box/12-parent verifier plus eight deliberately corrupted-output rejection tests. The actual GitHub test jobs were **QUEUED** at the last check: see [workflow](https://github.com/Chatnoir01/ml/actions/runs/44452720306). **Green CI is NOT asserted until confirmed for the latest source head.**

## Strict interpretation
**The preregistered single scalar feature's negative association persisted on 10/12 newly generated random parent-group contexts, at the registered median threshold.** This is a **within-project predictive replication on a new synthetic cohort** against a **simple classical distinguisher**, not the requested demonstration of a genuinely new resistance property against neural distinguishers. Stronger multi-round differential/linear theory and classical baselines may account for the relationship.

This is a tiny 32-bit SPN with fixed rotation, not deployed AES. Affine equivalence preservation and differential diffusion are long studied (see Canteaut & Roué EUROCRYPT 2015); no universal novelty claim. Different random parent permutations are not multiple reviewed cipher families, shared samples across variants are correlated by design, public keys/schedules do not establish cryptographic security, and twelve parent groups limit statistical generalization.

**No Phase 2U neural labels, zero new neural fits, no Phase 2G result changes, no merges, no deployed crypto.** A future genuinely independent architecture/keys prospective trial and then separate, explicitly authorized Phase2R-gated neural comparison are needed before any broader claim.
