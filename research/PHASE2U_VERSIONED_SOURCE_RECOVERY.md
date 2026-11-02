# Phase 2U — Versioned prospective source recovery after Phase 2T-v1 generator stall

**Status: NEW pre-neural source study, explicitly separate from the BLOCKED Phase 2T-v1.**

## Incident and scientific version boundary

On 2026-11-02 the original 24-seed Phase 2T-v1 attempted source seed 31013 and raised:

\`RuntimeError: unable to generate globally unique Phase 1O proposals\`

The legacy collector accumulates proposals from a fixed parent pool; after more
than 512 consecutive no-new-proposal parent attempts it crashes without a
completed 340-evaluation receipt. The original v1 design required a *contiguous
seed-prefix ledger* and exactly 340 classical evaluations per seed. It is
**not permissible** to skip 31013, relabel it ineligible or mix later
successful seeds with a modified collector without an explicit new study.

The old output receipts are preserved as discovery/development data:
31001 ineligible; 31013 crashed; 31019 accepted; 31033 ineligible;
31039 accepted. The accepted candidates were independently verified by
a standard-library implementation of NL, DU, LAT, algebraic degree, SAC and
SHA3 fingerprints. None can be silently reused as an independent 2U sample.

**Phase 2U is an explicit source-protocol amendment** formulated after
seeing those FIVE outcomes but before any Phase 2T/2U neural outcome.
It does NOT supersede the frozen v1 result or assert that v1 succeeded.

## What is changed versus v1

Only source candidate generation changes. The retained classical target
remains a bijective 8-bit S-Box with:

- Nonlinearity **exactly 100**;
- Differential uniformity **exactly 8**;
- Maximum nontrivial linear correlation **exactly 56**;
- Maximum algebraic degree **exactly 7**;
- SAC score within **0.05** of 0.5.

New source version identifier: \`phase2u_source_v1\`.

New public source seeds, in required fixed order:
\`41003, 41011, 41017, 41027, 41039, 41047, 41051, 41057, 41063, 41071, 41077, 41081, 41089, 41101, 41113, 41117, 41131, 41141, 41143, 41149, 41161, 41177, 41183, 41189\`.

Exactly **340 full unique classical evaluations per completed seed**;
20 initial population members plus 20 generations × 16 proposals per generation.
Retain the original Phase-1O multi-hotspot guided proposals until they become
locally stuck.

New explicitly versioned deterministic **fallback**:

1. If 32 consecutive guided parent selection attempts yield no new candidate,
   enter fallback for the remaining proposals in the current generation.
2. Select a parent uniformly from the same four frozen NSGA-II-selected parents
   using the same public-seed \`random.Random\` stream.
3. Sample two distinct coordinates among 256, swap the parent's values and
   accept the child **only if globally new** across all completed generations.
4. Stop at the required 16 unique proposals per generation, or after
   **8192 bounded fallback attempts** report \`source_exhausted\` with the
   *actual* classical evaluation count and a signed-by-nobody SHA-256 receipt.
   Such a partial source is NOT an ineligible completed seed.
5. Selection from the unique evaluated ledger uses **classical metrics only**
   and the lexicographically lowest SHA3-256 fingerprint among eligible hits.
   Source runs do not inspect neural scores or train any network.
6. The first twelve independently admissible source candidates in the new
   contiguous fixed-order registry would form the panel *only after* explicit
   source replay and new-version exclusion/equivalence audits.
   Any uncompleted source or fewer than twelve eligible seeds after the whole
   registry **blocks** the study, not a reason to silently change thresholds.

The fallback is a search *reliability* device, not a cryptographic innovation
or a proof of improved S-Box resistance. A fallback proposal that does not
satisfy the exact frozen metrics will not be selected. We may measure the
fraction of accepted proposals requiring fallback, but it is a secondary
exploratory source-quality metric.

## Version boundaries and outcome interpretation

- **Do not mix** the two v1 candidate S-Boxes, their seeds, counts or SHA
  receipts into Phase 2U's prospective candidate panel.
- This new source registry is frozen before any Phase 2U seed is executed.
- A successful Phase 2U source receipt is not yet a blind neural prediction.
- If source selection succeeds, a separate Phase 2U candidate-admission and
  **prediction-freeze** protocol must be explicitly approved in code,
  committed and audited *before* any new neural experiment is executed.
- Phase 2T's prospective Spearman gate cannot simply be transplanted with a
  version label changed. A future 2U analysis plan must pin its exact
  inference family, architecture, dataset splits, power assumptions and
  provenance requirements before outcome access.
- SHA-256 receipt digests are accidental-change detectors, **not signatures**
  and not a proof of timestamp/origin. GitHub logs plus independent replay
  remain external evidence.

## Tests and first pilot

Software tests in \`tests/test_phase2u_generate.py\` explicitly force the
guided generator to return only previously seen parents, checking that the
bounded random-swap fallback delivers unique, bijective, deterministic
children with auditable mode metadata.

A pilot CI workflow is restricted to seed **41003**, the first of the new
registry, and archives the raw JSON regardless of \`accepted\` or
\`ineligible\`. It does not train a neural network or predict neural scores.

\`\`\`bash
python -m pytest -q tests/test_phase2u_generate.py
python -m adversarial_sbox.phase2u_generate --seed 41003 --output seed-41003.json
\`\`\`

The pilot may be a legitimate negative result. Source study failure or
generator exhaustion must be reported unchanged. **No novel cryptographic
primitive, AES weakness, production readiness or neural-generalization
claim is made.**
