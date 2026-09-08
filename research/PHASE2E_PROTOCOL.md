# Phase 2E — Artifact-only diagnostics protocol

**PREREGISTERED / FORENSIC ONLY / ZERO NEURAL TRAINING / NO EVOLUTION REPLAY**

Governing issues: #112 and #113.

## Frozen source

Phase 2E may read only Phase 2D artifacts from workflow run `34147455097` generated at marker commit `2cc913e33cc5848f12ae5493f992b49fa89bc3d2`.

Required identities:

- terminal-freeze payload SHA-256: `8b50e71ab8fc082d1c49fa9b7da0e896c3ecf0f851a82500617bc34927799107`
- Phase 2D aggregate payload SHA-256: `51f41197482c5695ed00267c69dfc81b937cf12871336457308755f8e5e64e5c`
- exact cells: `C / O0 / OP1 / SP1 × 9` frozen evolution seeds = 36 arm receipts
- per cell: 340 classical evaluations, 32 candidate fitness scores, 512 fitness trainings, 32 score receipts

Receipt SHA failure, duplicate/missing cells, budget drift, or source identity drift produces only `phase2e_inconclusive_artifact_provenance`.

## Zero-compute lock

Phase 2E performs zero neural training, zero fitness/held-out scorer calls, zero candidate generation, zero evolution replay and zero Block-W reevaluation. The implementation must not import `phase2d_oracle` or `phase2d_validation`.

## Frozen diagnostics

D1: OP1/SP1 tag creation, active appearances, order use, membership use and expiry/non-use, with raw-event and unique-fingerprint counts separated.

D2: O0/OP1/SP1 score-caused entrant fate at +1/+2/+5, direct and descendant, plus terminal self/descendant ancestry. Unique-fingerprint fate merges repeated appearances by logical OR and explicitly reports defined/undefined denominators.

D3: conservative replacement classification at the next tagged stage: `lineage_not_present`, `same_key_not_selected`, `strictly_better_classical_key_present`, or `not_reconstructible`. No neural score is used to redefine protected classical geometry.

D4: preclosure boundary opportunities, scored opportunities, budget-closing events, postclosure observational-only opportunities and actionable fraction.

D5: OP1 vs SP1 descriptive comparison only. No support threshold or p-value is introduced.

D6: deterministic matched per-seed table with exact source arm payload SHAs.

## Determinism

Analyze the same exact receipts in canonical `(seed, arm)` order and reverse input order. Canonical JSON output must be byte-identical.

## Status

Only:

- `phase2e_artifact_diagnostics_valid`
- `phase2e_inconclusive_artifact_provenance`

Phase 2E cannot alter the frozen Phase 2D verdict `phase2d_bounded_persistence_not_supported` and cannot authorize a longer persistence rule, larger score budget, adaptive retraining or bidirectional GA↔NN experiment.
