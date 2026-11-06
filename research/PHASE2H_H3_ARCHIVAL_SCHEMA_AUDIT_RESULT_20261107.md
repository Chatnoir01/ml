# Phase 2H-H3 — Archived A/F classical-selection receipt audit (2026-11-07)

**Exploratory, read-only, noncausal.** No Phase 2G mutation, new neural fitting, Phase 2U release or main merge. Original Phase 2G negative verdict `phase2g_adaptive_coevolution_not_supported` unchanged.

## Preregistration and evidence

H3 archive schema repair protocol was committed at `dbfe02617b807c4193fbfc59ae0ca9358f240347` **before any candidate-quality outcomes were computed** (the 2H H3 hypothesis is older; this is an exploratory implementation/measurement repair, not a retrospectively confirmatory new criterion).

Analyzed all 18 ORIGINAL paired A/F arm ZIPs from official Phase 2G run [35572084785](https://github.com/Chatnoir01/ml/actions/runs/35572084785), source marker `030652489dd489a4705bbf64a12d7e6fa01ca03b`, and compared the source ZIP bytes against the authenticated [39-artifact preservation snapshot](https://github.com/Chatnoir01/ml/pull/169). All 18/18 original JSON payload SHA-256 digests, ZIP CRC and embedded 340-row classical ledgers verified. No reconstructed historical raw weights or ciphertext were claimed.

## Two actual Phase 2H implementation/schema defects

- The current Phase 2H `_classical_distortion()` seeks `score_caused_exited`, missing from **720/720** archived A/F selection events. The September frozen producer `phase2g_ga_adapter.py` records `exited` as the actual difference `selected_before - selected_after`, alongside `entered` and `score_caused_entered`. All 720 sets and 713 nonzero score-caused swaps were independently checked.
- The current `_classical_tuple()` requests `max_linear_correlation` from the historical classical ledger, but `phase2g_experiment.py` stores that value under `max_abs_lat`. Therefore Phase 2H's existing `A_classical_distortion` and `F_classical_distortion` values are **not usable for H3**, notwithstanding their true availability flag. The pre-existing H3 reader remains unmodified in this branch pending integration tests.

## Fingerprint-order-invariant exploratory event-set results

For each historical scored selection event, derive exact *sets* of entrants/exits from saved before/after selections; verify the source's `score_caused_entered`; map frozen ledger to favorable-direction security coordinates `(nonlinearity, -differential_uniformity, -max_abs_lat, algebraic_degree)`. Compare separately lexicographically sorted *classical tuple multisets*, not arbitrary fingerprint-paired candidates. Independently compare mean four-coordinate Pareto directions. All event records, including null outcomes, are retained.

| Arm | Recorded events | Events with nonempty swaps | Swapped candidate slots | Strictly classically worse event sets | Classically equal event sets |
|---|---:|---:|---:|---:|---:|
| A adaptive | 360 | 356 | 1,895 | 105 | 255 |
| F fixed | 360 | 357 | 1,953 | 107 | 253 |
| **Total** | **720** | **713** | **3,848** | **212** | **508** |

No swapped entrant set was strictly better than its displaced set by the registered order-statistic or four-coordinate Pareto definitions. This is compatible with the historical classical-priority/B1 selection geometry; it is **not** a new cryptographic theorem. **A and F have very similar negative-tradeoff frequencies (105 vs 107)**, and seedwise effects vary in both directions. Thus this receipt-level measure does **not** isolate H3 classical selection distortion as the cause of A's worse final held-out score.

## New chronological constraint on historical numerical anomalies

- **90/90** A/F `selected_after` event sets for generations **0–4** were exactly identical (5 generations × 2 stages × 9 evolution seeds), **including the four seeds with checkpoint-zero model-state SHA mismatch**.
- **9/9** first A/F selection-set differences occur at **generation 5, stage `shortlist`**, after A's first adaptive curriculum refresh while F remains fixed. Every first-divergence event has exactly matching A/F pre-selection and B1 group.
- Only **102/360** A/F event contexts share exactly the same pre-selection and B1 group; 90 of these first-block events produce identical outcomes, and 12 later contexts produce differing choices. Later dissimilar populations cannot be compared as a controlled model-only contrast.
- For the nine first divergent selection events, A/F selected classical tuple multisets are identical **8/9**, and differ for seed **726113**.

This rules out an observed *selection-membership* effect of the 64/144 historical initial neural state SHA mismatches during the first five generations, **not** a later numerical/runtime effect or a causal contribution to the terminal A/F held-out difference.

## Independent verification

Standard-library primary read-only analysis script, 720 event JSON, independent source-stream verifier, per-event/classical digest recheck, and seven synthetic corruption/relabeling checks completed. Original 18 ZIP byte streams were independently matched to the 39-source preservation ZIP SHA256 `f10e5d18e7b135bf08df9f3d3579c18a37c340e45a09ebaa28171fcf81e551ed`.

- Primary canonical audit SHA256: `8d9f10be8e40790f4beeec1f5f70b1b67d511f7edf33573c1e53501726fc5d1c`
- Independent verification SHA256: `7f0bf18200e073cb3f571c8361a495153086e82c9fda4824d59a820a00c9b459`
- Complete conversation evidence ZIP: `phase2h_h3_original_archive_verified_evidence_20261107.zip`; size **3,481,554 bytes**, SHA256 `eef47515ed4897688c2b28ec03bd2466dedaa6862f0604db1b7048dbc2911374`. Includes 18 original unmodified ZIPs, both scripts, 720-event JSON, independent audit JSON, negative controls and checksums. **User-controlled durable external preservation is not attested.**

The original Phase 2H workflow was independently repaired for missing test dependencies on [PR #121](https://github.com/Chatnoir01/ml/pull/121) and [specialized CI succeeded](https://github.com/Chatnoir01/ml/actions/runs/42311291381); its old H3 reader nonetheless remains scientifically invalid for the stated classical-distortion metric. **Do not promote this exploratory analysis to a confirmatory or causal H3 verdict**, change the Phase 2G freeze, merge into main without review, or execute sealed Phase 2U.
