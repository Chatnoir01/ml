# Phase 2H-FORK1 — Original generation-5 A/F first-selection fork and realized lineage (2026-11-07)

**PRE-ANALYSIS LOCK**. Commit this protocol *before* calculating this study's outcomes. This is a read-only, exploratory secondary mechanistic characterization of existing preregistered Phase 2H H2/H3 hypotheses, not a new confirmatory test, causal experiment or Phase 2I/2U execution.

## Immutable source and denominator

Use all 18 original source GitHub `phase2g-arm-{A,F}-SEED-030652489dd489a4705bbf64a12d7e6fa01ca03b.zip` source artifacts, available in the independently authenticated 39-source archive or 18-source preservation ZIP. Require original `arm.json` canonical SHA256 (`scientific_payload_sha256`) validation, ZIP CRC, A/F arm and seed agreement. Nine evolution seeds `726011,726023,726037,726049,726061,726073,726087,726099,726113`. No new train/fit/evolution, no original artifact mutation, no opening heldout H; record each consumed original ZIP SHA256, software source commit and analysis implementation SHA256.

## First-fork event registration

Select exactly generation `5`, stage `shortlist`, in each A and F arm. Require 40 unique `(generation,stage)` event pairs per arm, `selected_before` A/F identical as **sets**, `b1_group` A/F identical as **sets**, A/F `cutoff` equal and `selected_after` size equals cutoff. Confirm sets `entered=selected_after-selected_before`, `exited=selected_before-selected_after` and identical `score_caused_entered` in eligible A/F events. Confirm `scored_candidate_count` equals B1 group size and finite full `assigned_scores` mappings. Fail closed otherwise.

For every seed, `A_only = A.selected_after - F.selected_after`, `F_only = F.selected_after - A.selected_after`. Require equal cardinality. Report cardinalities including zero. Calculate cross-arm strict score-rank inversions for every unordered identical B1 candidate pair using original lower-is-better scores; exact ties tracked separately. Separately report whether at least one strict rank inversion **crosses first-fork membership boundary**, defined as a pair `(a in A_only, f in F_only)` with A ranking a strictly ahead of f and F ranking f strictly ahead of a. This is the directly decision-relevant subset, no causal interpretation.

## Frozen classic ledger effect

Use ONLY saved `classical_evaluation_ledger` of each arm. For an exact common candidate require A/F four historical columns `nonlinearity,differential_uniformity,max_abs_lat,algebraic_degree` match, else fail closed. Use favorable-direction tuple `(nonlinearity,-differential_uniformity,-max_abs_lat,algebraic_degree)`. Compare lexicographically sorted **multisets** of classical tuples for A_only vs F_only, report better/worse/equal/mixed order statistics and four-coordinate mean-Pareto relation. Report event-level classical comparisons and original `cross_protected_key_membership_change` flags, without treating lexicographic order as proof of Pareto security or equating a difference with benefit in H.

## Population descendants and terminal participation

Use immutable `generation_trace[g].next_population` as the observed population **after generation g**. For each A-only candidate follow only its **own A history**; for F-only only its **own F history**. Prespecified observation population generations (post-processing) = `5,6,7,9,14,19` (corresponding to populations entering generations 6,7,8,10,15,20). Track direct original-candidate membership; separately descendant membership through the same-arm immutable `parent_map` chain without loops (if the ancestor is the candidate itself, direct membership only). For each arm, report 0–N counts surviving directly and with a non-self descendant on these observation generations; also whether candidate equals terminal fingerprint or is ancestor of terminal. Do NOT treat these evolving A/F futures as controlled intervention outcome because populations and proposals become noncomparable after the first fork.

Validate all 20 generation trace rows per arm, population size 20 and unique fingerprint identities, and all map references traversed without cycles. Whenever original `lineage_diagnostics` includes a first-fork `score_caused_entered` fingerprint, crosscheck available stored `direct_plus_1, +2, +5`, `descendant_plus_1, +2,+5` fields to their literal documented `generation+offset` population indexing; report any disagreements without silently overriding source.

## Full report / falsification gates

All nine seed rows, all first-fork candidate sets, all 20-rank traces where comparable, all directional counts and nulls. Count matched initial model SHA discrepancy per seed by original 16 `model_receipts.state_sha256`; treat model identity as historical provenance, not as a posthoc subgroup yielding significance. No p-values; no posthoc subset, no inferred causality; no crypto security claims. Independent verifier recomputes chosen metrics directly from unchanged original ZIP bytes and hashes. Preserve executable script, canonical JSON, original 18 ZIP evidence, original payload/ZIP digests, independent verification summary, README and SHA256SUMS in a downloadable evidence ZIP.

No change to frozen Phase2G verdict `phase2g_adaptive_coevolution_not_supported`; zero Phase 2U sealed 96 neural trainings. DRAFT stacked PR only, do not merge main.
