# Phase 2T — Prospective, blinded prediction of unseen S-Box neural distinguishability

**Status: prospective protocol and implementation scaffold, NOT an executed prospective experiment.**
**No fresh candidate panel, prediction receipt, or neural result has yet been produced.**
**Research only: the 32-bit ToySPN is not a real-world secure cipher.**

## 1. The precise claim to falsify

After seeing the historical six S-Box neural results (Phase 2A-T), Phase 2S identified a classical single-bit differential baseline that shows related behavior.

**One primary hypothesis, selected post hoc on the historical panel but frozen before seeing any NEW panel's neural scores:**

> Across a genuinely fresh, fixed, exact-classical-metric-matched panel of 12 independent candidate S-Boxes, the **mean held-out one-bit differential advantage at depth four**, using input differences 0x00000001 and 0x00000100 under the historical public round-key schedule, **positively predicts** the candidate's mean neural distinguishing advantage at depth four.

The hypothesis is NOT that the one-bit classical baseline equals the neural model, that it causally explains learning, that it discovers an unknown cipher weakness, or that S-Boxes can be securely ranked for production deployment.

## 2. What is frozen before prospective execution

- Old derivation source: **six historical Phase 2A-T S-Boxes**, official artifact, depth-four neural scores; its original protocol and receipts are never edited.
- New generator: new independent initial populations through Phase-1O multihotspot classical evolution; fixed **340 unique full classical evaluations per seed**; 24 ordered source seeds and deterministic classical selection.
- Seeds (in order): 31001, 31013, 31019, 31033, 31039, 31051, 31063, 31069, 31079, 31081, 31091, 31103, 31121, 31139, 31153, 31159, 31171, 31177, 31181, 31189, 31201, 31211, 31219, 31223.
- Candidate acceptance is **classical-only**, never based on neural labels or the Phase 2T single-bit feature. From the evaluated ledger of each seed, select the candidate with the lexicographically smallest SHA3-256 fingerprint that satisfies all EXACT classical-metric bounds. Reject seeds with none; take the **first 12 successful seeds**, stopping on the twelfth success. There is no replacement, manual pick or relaxed threshold.
- Exactly matched classical criteria: NL=100, DU=8, max |LAT|=56, algebraic degree=7, SAC within ±0.05 of 0.5 and a bijective 8-bit S-Box. These are standard S-Box properties, not a claim of adequate cipher-level security.
- If 24 predeclared seeds fail to produce 12 exact-metric matches, **panel incomplete and experiment blocked**. A proposed expanded seed registry or relaxed metrics would create a *new prospective study*, not a silent update to this one.
- Exclude all historical SHA3-256 S-Box fingerprints, duplicate candidates, and direct XOR input/output shifted copies of the six historical S-Boxes. General linear/affine equivalence across families is NOT comprehensively excluded by this guard; this requires further review.
- Fixed 32-bit ToySPN, 4 rounds, original six public round keys, original 11-bit rotation; **no change to the cipher, no new keys or neural architectures** for the primary test.
- Fixed chosen-plaintext XOR differences: 0x00000001 and 0x00000100.
- Classical feature: one ciphertext-XOR output bit selected on 2,048 positive and 2,048 negative **training pairs** per difference, with sign fixed by training; signed advantage evaluated on separate 4,096+4,096 pairs per difference. Same deterministic paired plaintext sources across S-Boxes; no train/evaluation plaintext-block reuse.
- Primary predictor: **arithmetic mean of the two signed holdout one-bit advantages**. Predict rank by decreasing value with fingerprint tie-break. No supervised fitting to the historical neural labels and no choice between competing features after prospectively observing outcomes.
- All results are committed as candidate-generation and prediction receipts **BEFORE** any Phase 2T neural training. A SHA-256 receipt digest provides integrity against accidental changes, but **is NOT an independently authenticated signature, timestamp, or proof of origin**. A public version-controlled commit plus independent receipt review supplies the temporal evidence.

## 3. Separation of duties — 3 successive irreversible stages

**Stage A — Generate fresh classical panel**:
- Run registered source seeds in order. Each source job emits S-Box, exact classical metrics, source seed, 340-evaluation count, initial-population digest and proposal audit digest.
- Independently re-run a sample of seeds to validate deterministic outcomes. Complete the contiguous seed ledger. If not enough matching S-Boxes, stop.
- Aggregate only the first 12 accepted candidates. Produce full raw panel with no neural labels. Audit whether supposedly independent source candidates are affine-related or otherwise closely correlated; explicitly downgrade claims if independence fails.

**Stage B — FREEZE classical predictions**:
- Run classical bit selection/holdout scorer on the 12 admitted candidates. Produce immutable prediction receipt with exact panel digest, score and best-first ranking.
- Independently reproduce the list and commit its digest. Neural results **must not yet exist** for these new candidates when this prediction receipt is frozen.
- Do not change feature, sign convention, selected depths, sample sizes or ranking to improve observed correlations.

**Stage C — Independent neural outcome execution (separate PR/CI authorization)**:
- Only AFTER Stage B is publicly frozen: exact 12 S-Boxes × 2 input differences × 4 independent paired model/dataset seeds = **96 neural trainings**.
- Fixed depth 4, existing \`byte_tanh_mlp\` implementation, unchanged feature extractor, balanced datasets, non-overlapping train/validation/test splits. Fresh dataset seeds: 930101, 930113, 930127, 930139. Fresh model seeds: 940101, 940113, 940127, 940139. Both input differences use the prespecified paired replicate index; seeds are not chosen after seeing scores.
- Preserve full per-run output, AUC, null AUC, fingerprints of sample splits/model initialization/runner code, loss diagnostics, runtime and versions. Run source-input invariance checks and initialization checks before accepting each run. Address Phase 2R's previously identified baseline provenance issue before attributing small effects.
- Neural candidate score: arithmetic mean across all 8 runs of \`2*abs(test_auc - 0.5)\`; null score analogously computed using shuffled labels. **No winner selection, no removal of failed runs, no retraining based on test performance.**
- Seal neural outcome artifact; evaluate once against the already frozen classical predictions.

## 4. Primary prospective statistical test

One prespecified, directed hypothesis: Spearman rank correlation (with average tied ranks) between the 12 frozen classical feature scores and 12 mean neural advantages **must be positive**.

- Primary threshold: **rho >= 0.60**.
- One-sided Monte Carlo permutation test: **19,999 shuffled rankings**, RNG seed 950101, p-value with +1 correction; require **p < 0.05**.
- Independent neural signal gate: mean over candidates of (mean neural advantage − mean shuffled-null advantage) must be **at least 0.02**.
- **All three criteria** required for the label \`SUPPORTED_WITHIN_PINNED_TOY_CIPHER_PANEL\`. If not, record \`NOT_SUPPORTED_OR_INCONCLUSIVE\` without in-place retuning.
- Report an exploratory paired nonparametric bootstrap 95% interval (2,000 resamples, seed 950113), all individual candidate outcomes, missing-data gates and exact sample counts.
- There is only **one** primary test. Secondary checks (classical 3/5 round features, alternative rotation/keys, DDT entropy or more complex multibit oracles) are expressly excluded from deciding this preregistered hypothesis. They require a different preregistration.

With only twelve candidates, uncertainty is high; using candidate-level scores avoids incorrectly counting the 96 correlated neural trainings as 96 independent S-Box observations. Statistical gate passage does not establish an original cryptographic theorem.

## 5. Rigorous failure and integrity conditions

- Any seed reuse, non-prefix seed order, modified 340-evaluation budget, non-matched classical candidate, duplicate/historical S-Box, obvious affine copy or provenance mismatch: reject and do not silently substitute.
- A missing generation receipt or candidate-generation code not independently reproducible: report provenance limitation; do not upgrade result to independently validated.
- If the panel does not reach 12 within 24 seeds: **no primary neural execution**. Report the panel-generation failure, not a falsified neural hypothesis.
- A neural outcomes file must reference the exact frozen prediction and panel digests and contain **96** unique candidate/difference/replicate rows, valid fingerprint, paired fresh seeds and finite AUC/null-AUC. Missing/duplicate/modified rows invalidate the report; do not replace or drop them.
- The evaluator is a distinct module and cannot alter frozen rankings. The CLI creates outputs with exclusive file mode to avoid silently overwriting an existing receipt.
- Never claim cryptographic security, AES implications, nonce safety, post-quantum protection, learned key recovery, or general cipher robustness from ToySPN classification performance.

## 6. Source files and command separation

- \`src/adversarial_sbox/phase2t_generate.py\` — classical-only fresh seed evaluator and contiguous ledger (expensive, NOT automatically run by CI).
- \`src/adversarial_sbox/phase2t_predict.py\` — admission, classical scoring, sealed prediction receipt, **no new neural data**.
- \`src/adversarial_sbox/phase2t_evaluate.py\` — accepts externally prepared 96-row neural results only AFTER prediction receipt is fixed; performs the single primary test.
- \`tests/test_phase2t_prediction.py\` — synthetic validation fixtures, negative controls and smoke tests. Fake panels are explicitly NOT scientific samples; no 96 real neural jobs run as part of tests.
- \`.github/workflows/phase2t-preregistration.yml\` — low-cost tests and syntax checking only, **not automatic classical evolution or neural training**.

Example separation:

\`\`\`bash
# Classical candidate source stages (run in separate controlled jobs):
python -m adversarial_sbox.phase2t_generate seed --seed 31001 --output seed-31001.json
# ... sequentially, until 12 exact matches or 24 exhausted.
python -m adversarial_sbox.phase2t_generate aggregate --results seed-31001.json ... --output panel.json

# Only after provenance audit of exact 12 independent S-Boxes:
python -m adversarial_sbox.phase2t_predict --panel panel.json --output predictions-frozen.json

# Only after predictions-frozen.json and its SHA have been committed and reviewed:
# Run Phase 2T neural experiment in a distinct and subsequently authorized CI step.
python -m adversarial_sbox.phase2t_evaluate \
  --predictions predictions-frozen.json \
  --neural-outcomes independently-generated-neural-results.json \
  --output prospective-test-result.json
\`\`\`

**As of the initial PR creation, no real Phase 2T candidate panel, frozen prediction or neural response exists.** Its code and test fixtures are methodological preparation, NOT a new positive scientific result.
