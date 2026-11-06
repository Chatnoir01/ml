# Phase 2H-H3 — Frozen archival ledger schema repair / exploratory analysis protocol

Date: 2026-11-07. **This protocol must be committed before computing H3 repair outcome statistics.** This is a diagnostic implementation repair within pre-existing Phase 2H H3; it is **not** a new confirmatory hypothesis, retroactive Phase 2G experiment, causal claim, or authorization for Phase 2I/2U.

## Immutable input, hard scope

Use only the **18 original frozen Phase 2G A/F `arm.json` payloads** from official run `35572084785`, exactly nine evolution seeds `726011,726023,726037,726049,726061,726073,726087,726099,726113`, two arms A and F, and exactly 40 selection events/cell. Verify all ZIP CRC, source JSON scientific payload SHA-256 (canonical sorted compact JSON excluding `scientific_payload_sha256`), uniqueness and event identities. No neural training, inferred original initial weights, reconstructed historical ciphertext, changed holdout, GA run, main merge, or Phase2U seal release.

## Observed schema inconsistency requiring repair

Historical frozen `phase2g_ga_adapter.py` records `score_caused_entered`, `entered`, `exited` and the two actual set-valued selection lists `selected_before` and `selected_after`. It does not record `score_caused_exited`. Historical `phase2g_experiment.py` stores classical `max_linear_correlation` under `max_abs_lat` in `classical_evaluation_ledger`. The current 2H reader uses the two wrong keys, so its candidate-level classical metrics are structurally uncomputed despite a true availability flag. These schema issues were discovered **before** comparing candidate quality outcomes.

## Locked validity checks

For each event, check both selected sets are unique, have length `cutoff`, and that `entered` equals `selected_after - selected_before`, `exited` equals `selected_before - selected_after`. Require `score_caused_entered == entered` only where the historical A/F event explicitly declares neural selection active and a valid boundary opportunity. Check entrant/exit equal cardinality, every referenced fingerprint appears exactly once in that arm's immutable 340-row classical ledger and required four fields are finite. Missing/contradictory values invalidate the entire candidate-level analysis, never count as zero effect.

## Locked order-independent descriptive comparisons

For each nonzero score-caused event, transform each candidate's historical security coordinates into the favorable-direction tuple **(nonlinearity, -differential_uniformity, -max_abs_lat, algebraic_degree)**. Sort the *tuple multiset* for entrants and exits separately in descending lexicographic order (NOT arbitrary fingerprint pairing). For each corresponding order statistic report `better`, `worse`, `equal` by lexicographic tuple comparison. Event classification: `all_better_or_equal` if at least one better and none worse; `all_worse_or_equal` if at least one worse and none better; `all_equal` if all equal; `mixed` otherwise. Report every arm/seed including both positive and negative outcomes, totals and all individual event records.

As a separate, less-order-dependent sensitivity summary, compute strictly multivariate Pareto dominance between the four-coordinate **mean vectors** of entrant/exit sets (higher is preferable on every component). Count Pareto-better, Pareto-worse, mixed and equal, without conflating these with the lexicographic primary order.

A/F same-context comparison is permitted only for events with identical `generation`, `stage`, `b1_group` and `selected_before`, in which the two arms' baseline selection opportunity matches. Otherwise report incomparability; do not attribute differences to curriculum or BLAS numerics. Do not run significance tests, choose a favorable metric post hoc, or claim these results prove H3 causally.

## Required products / gates

Produce a deterministic JSON report recording input archive SHA-256, each original payload SHA, source commit and immutable parent, per-arm/seed/event outcome rows and completeness counters. Independently verify the output's aggregate SHA-256 plus source hashes. Add synthetic negative tests for tampered receipts, missing exit sets, missing max_abs_lat, mismatched entrants and arbitrary fingerprint relabeling. This audit stays DRAFT until reviewed. The original Phase 2G verdict remains `phase2g_adaptive_coevolution_not_supported`.
