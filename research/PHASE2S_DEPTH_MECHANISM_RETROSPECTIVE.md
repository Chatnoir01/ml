# Phase 2S — Mechanistic hypotheses for the replicated depth-four S-Box signal

**Status: artifact-only retrospective analysis; scientific novelty and causal mechanism NOT established.**

This is a separate branch from \`main\`, independent of pending Phase 2G / 2H / 2R / RAVEN work. It imports the **unchanged frozen Phase 2A-T results and panel**. It performs no neural training, no new evolution, no fresh-seed confirmation, no retuning, and no modifications to previous scientific receipts.

## A. Facts observed in the locked source

The frozen six-candidate 8x8 bijective S-Box panel (digest \`35898535a0df0cfe64431e5f0b6142115d40e3dbeed4a973faa9ba70b1028a30\`) contains **six S-Boxes with identical values of**:

- DU=8; vectorial NL=100; max |LAT|=56; maximum algebraic degree=7.
- Their overall SAC scalar values are close to 0.5, **not all literally identical**.

Phase 2A-T, performed with a fixed \`byte_tanh_mlp\`, a single ToySPN round-key schedule, differences 0x00000001 / 0x00000100 and fresh paired seeds, reported:

| Depth | Mean advantage | Candidate-score range | Across-candidate heterogeneity |
|---:|---:|---:|---:|
| 3 | 0.9889908601 | 0.0032758821 | 0.00000133743 |
| 4 | 0.3283806659 | 0.1065815311 | 0.0013404629 |
| 5 | 0.0428012628 | 0.0177131665 | 0.0000455479 |

The preregistered depth-four profile was replicated in Phase 2A-T. This is a **specific ToySPN, six-candidate, key-schedule, representation and dataset result**, not a general theorem for block ciphers.

**Crucial distinction:** larger *between-candidate* variability at four rounds does not mean that the overall distinguisher performs better there than at three rounds. At three rounds the mean advantage was ~0.989 (near ceiling), whereas at five it was ~0.043 (near floor). This can constrain the available range of candidate-to-candidate variation; the causal contribution of saturation versus S-Box structure remains unknown.

## B. Source audit of the old design

- \`src/adversarial_sbox/spn.py\`: ToySPN uses a 32-bit, four-byte state, independent byte substitution, fixed **11-bit rotation** between rounds and XORed round keys. This is an educational construction, **not** AES.
- \`src/adversarial_sbox/phase2at_runner.py\`: each depth uses \`ROUND_KEYS[:depth+1]\` and the exact same six candidate fingerprints, fixed architectural family and two chosen input differences.
- \`src/adversarial_sbox/datasets.py\`: positive examples are pairs of ciphertext blocks encrypted from plaintexts with chosen XOR difference, negative examples are independently sampled plaintext pairs excluding that difference. Samples are balanced and ciphertext blocks globally disjoint.
- \`src/adversarial_sbox/neural_heterogeneity.py\`: byte-tanh network receives twelve numeric features: four bytes each from ciphertext left, right and left XOR right.
- \`src/adversarial_sbox/neural100.py\`: \`neural_advantage = 2*abs(test_auc-0.5)\`; this bounded absolute-AUC transformation has floor/ceiling effects that must be separated from neural convergence and signal provenance.

**Interpretation:** with all headline classical metrics matched, those scalars cannot directly explain between-candidate depth-four differences within this panel. Local differential statistics, subspace/bit-position structure, key schedule, input encoding, training convergence and multi-round propagation remain possible explanations.

## C. Actual new retrospective diagnostic (not confirmatory)

\`src/adversarial_sbox/phase2s_retro.py\` parses the frozen Phase 2A-T candidate advantages; verifies the six candidate fingerprints and headline-metric metadata; recomputes the *one-round* differential-distribution row for input byte difference 0x01 and its support, max, collision probability and entropy.

The six S-Boxes' row-0x01 profiles differ. Example:

| Candidate index | Max DDT[0x01,*] | Support | Collision |
|---:|---:|---:|---:|
| 0 | 6 | 105 | 0.010986328125 |
| 4 | 8 | 99 | 0.0126953125 |

A descriptive Pearson correlation across just the six candidates gives **r ~ 0.086** between this one-row collision probability and the old four-round neural advantage; entropy is also near zero correlation (**r ~ 0.017**). With n=6, no claim of absence of association, meaningful power, causality or significance follows.

**This is NOT a new S-Box cryptanalytic result.** DDT rows being different despite identical global maxima is expected. The useful finding is methodological: the simplest candidate-specific one-row explanation does not emerge clearly in this frozen panel, so causal follow-up needs controlled and better-powered experiments.

## D. Falsifiable prospective hypotheses — not authorized to execute

Each hypothesis below was formulated **after viewing Phase 2A-T** and is therefore *hypothesis-generating*. A separate prospective study must preregister fresh candidates/seeds, family-wise error control and exact computational budgets before looking at new outcomes.

- **H-SAT (measurement ceiling/floor):** depth-4 raw heterogeneity is amplified by ceiling at depth 3 and floor at depth 5. Compare raw AUC (with sign), absolute advantage, calibration, and a preregistered bounded-scale sensitivity analysis, without selecting metrics post hoc.
- **H-KEY (fixed key schedule):** S-Box-specific depth-four rankings partially depend on the fixed publicly pinned research \`ROUND_KEYS\`. Compare independent, frozen new round-key schedules while preserving depth/difference/sample and model-seed pairing. Never infer real encryption-key security from toy fixed-key experiments.
- **H-REP (feature representation):** the four-round separation depends on byte-tanh inductive bias; a bit-oriented model and representation ablations may change the profile. Equal *training counts* are not automatically equal compute or model capacity.
- **H-DIFF (multi-round differential geometry):** differences in local DDT rows alone do not predict the score; predefine higher-order differential/linear summary features, test predictive value against a null/label-shuffled baseline, and measure out-of-panel generalization. The old six candidate scores must not be used to select final features or thresholds.
- **H-GEN (panel specificity):** the depth-four profile is specific to the six historical winners. Test on a new, independently sampled matched-classical panel, with exact provenance, no candidate-selection leakage and held-out validation. No extrapolation before confirmation.

### Preferred staged design

1. **Artifact-only reanalysis (THIS PR):** publish deterministic calculations, tampering tests and hypotheses. No training.
2. **Source and reproducibility gate:** reconcile Phase 2R's baseline input/model-state hash anomalies before running expensive prospective neural work; pin code, dependency versions, data generator and model initializations.
3. **Mechanistic study preregistration (FUTURE PR):** independently frozen S-Box panel, fixed count, controlled key schedules, paired fresh seeds, model representations, exact outcome/censoring rules, one prespecified primary test and adjusted secondary tests.
4. **Execution marker and blinded comparison (FUTURE PR):** execute only after red/green tests, independent held-out holdback and provenance checks. Report negative or inconclusive outcomes unchanged.
5. **External replication:** independently implemented ToySPN/feature extractor and unrelated neural baseline; only then consider broader cipher families or mathematical claims.

No implementation of future H-SAT/H-KEY/H-REP/H-DIFF/H-GEN training has been authored or authorized in this PR.

## E. Exact checks and nonclaims

Run without NumPy or any neural extras:

\`\`\`bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_phase2s_retro.py
python -m adversarial_sbox.phase2s_retro > phase2s_diagnostic.json
\`\`\`

The report emits only candidate identifiers/fingerprints, scores already published in the frozen document and derived classical row statistics. It must not export private neural model state, raw samples, user data or cryptographic keys.

**No new crypto primitive, no AES weakness, no actual key recovery, no new neural security guarantee, no S-Box deployment claim, no automatic publication of a scientific paper.**
