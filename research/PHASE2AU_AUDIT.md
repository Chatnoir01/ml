# Phase 2A-U — Post-hoc provenance audit

## Status

The historical Phase 2A-U scientific outputs remain preserved exactly as archived in `research/PHASE2AU_RESULT.md`. This audit does not rewrite the observed neural scores, statistical endpoints, workflow run, artifacts, or hashes.

## Confirmed provenance defect

The historical implementation of `prior_frozen_neural_seed_registry()` omitted earlier frozen/executed Phase 2A-D and Phase 2A-P neural seed registries.

Phase 2A-P predates Phase 2A-U and executed 720 neural trainings. The historical Phase 2A-U seed registry overlaps Phase 2A-P at exactly these 13 values:

`74003, 74017, 74027, 74047, 74071, 74093, 74101, 84011, 84017, 84029, 84061, 84067, 84089`

Therefore the historical archived field `fresh_seed_registry_exact_and_disjoint: PASS` was produced by an incomplete registry check. Under the corrected complete Phase-2 registry, the historical Phase 2A-U experiment is **inconclusive on its freshness prerequisite**, even though its observed statistical qualification checks remain reproducible.

## Preserved evidence

The following remain historical facts of the executed run:

- scientific SHA: `9ed3fcc0a1d8099edffb1e4db170851a4884e448`
- workflow run: `34059256750`
- exact recorded neural trainings: `192`
- aggregate artifact ID: `9996948547`
- aggregate ZIP SHA-256: `4f20fe58cf19ba572c58d50450169a50b299d2bf58c42163e7a6c5c5fc3bea42`
- neural evolutionary pressure: `false`
- both blocked heterogeneity tests were significant under the frozen endpoint
- both score-range criteria passed
- cross-block rank/stability criteria passed

These observations are not erased. The defect changes the strength of the independence/provenance claim, not the historical bytes produced by the run.

## Remediation

Issues #85, #86, #88, and #89 define Phase 2A-U2. U2 repeats the same 4-round Oracle qualification question with:

- unchanged six-candidate panel;
- unchanged architecture, depth, differences, budget, and qualification thresholds;
- new seed blocks proven disjoint from every prior frozen/executed Phase-2 neural registry;
- a central Phase-2 neural seed registry;
- strict `pair_count` and train/validation/test split provenance checks;
- RED→GREEN CI evidence before scientific execution.

## Consequence boundary

The historical Phase 2A-U PASS is no longer sufficient by itself to authorize Phase 2B. Phase 2B remains locked by issue #87 until Phase 2A-U2 passes its complete fresh-seed provenance gate.

Educational/defensive ToySPN scope only. No deployed-cipher, AES, operational key-recovery, or production-security claim is made.
