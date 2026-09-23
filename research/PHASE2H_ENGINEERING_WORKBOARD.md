# Phase 2H — Engineering workboard

This board defines work that may proceed while CI is unavailable or pending.
None of these items may alter frozen Phase-2G evidence or authorize Phase 2I.

## Lane A — evidence and provenance

- [x] A1 bind Phase-2G parent commit and aggregate SHA-256.
- [x] A2 inventory all 18 primary A/F workflow artifacts.
- [ ] A3 record SHA-256 for every consumed input payload.
- [ ] A4 produce deterministic evidence manifest sorted by seed/arm/path.
- [ ] A5 reject duplicate, missing, unexpected, or hash-mismatched inputs.

Exit: one machine-verifiable manifest completely identifies the 2H evidence set.

## Lane B — H2 dynamics

- [x] B1 adjacent curriculum/population Jaccard.
- [x] B2 non-adjacent recurrence checks.
- [ ] B3 exact fingerprint recurrence matrix.
- [ ] B4 checkpoint direction-reversal metrics on comparable ranks/scores.
- [ ] B5 distinguish drift, recurrence, and true reversal explicitly.

Exit: H2 cannot be called from movement alone.

## Lane C — H3 selection distortion

- [x] C1 recover score-caused entrant/exit evidence and classical ledger.
- [x] C2 deterministic primary-coordinate comparison implementation.
- [ ] C3 validate event set semantics before pairing entrants/exits.
- [ ] C4 compute event-level protected-band before/after summaries.
- [ ] C5 aggregate all events by seed and checkpoint without cherry-picking.

Exit: every claimed distortion is traceable to exact fingerprints and ledger rows.

## Lane D — A/F divergence timeline

- [x] D1 define comparable state identities at checkpoints.
- [x] D2 identify earliest curriculum/model/rank/population divergence per seed.
- [ ] D3 attach downstream selection events.
- [ ] D4 attach terminal A-F held-out gap only after causal ordering is frozen.

Exit: nine deterministic per-seed timelines.

## Lane E — H1 feasibility

- [ ] E1 inventory checkpoint model artifacts/receipts.
- [ ] E2 inventory candidate immutable probe sources.
- [ ] E3 prove probe leakage firewall.
- [ ] E4 GO/NO-GO forgetting matrix.
- [ ] E5 if NO-GO, freeze missing-evidence reason; never reconstruct absent evidence.

Exit: H1 is either measured validly or explicitly unavailable.

## Lane F — deterministic product

- [ ] F1 CLI/runner consumes evidence manifest.
- [ ] F2 emit phase2h-diagnostics.json.
- [ ] F3 canonical JSON and aggregate SHA-256.
- [ ] F4 emit human-readable PHASE2H_RESULT.md from machine result.
- [ ] F5 rerun-order invariance.
- [ ] F6 corruption/missing-input negative tests.

Exit: same evidence always produces byte-identical scientific result.

## Lane G — future infrastructure, scientifically dormant

- [x] G1 Phase-2I mechanism-to-intervention firewall.
- [x] G2 forbid rescue sweep / ambiguous combination.
- [ ] G3 reserve fresh seed registry without opening held-out values.
- [ ] G4 exact budget calculator and invariant tests.
- [ ] G5 intervention interfaces behind execution lock.
- [ ] G6 Phase-2J independent replication firewall.

Exit: engineering ready; scientific execution still impossible before frozen 2H.

## Lane H — CI/repository integration

- [x] H1 detect first workflow attached to 2H head.
- [x] H2 inspect failures without changing scientific hypotheses. (No failures observed on current head.)
- [x] H3 fix implementation defects only. (No CI defect observed on current head.)
- [x] H4 require green scientific/test gates before merge. (Phase 0 CI + Phase 1 Benchmark green on audited head.)
- [x] H5 mergeability/base synchronization audit. (PR mergeable on audited head.)

Exit: repository proof agrees with local scientific contracts.
