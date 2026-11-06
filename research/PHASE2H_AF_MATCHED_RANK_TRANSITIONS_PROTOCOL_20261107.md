# Phase 2H — Prespecified exploratory matched-context A/F rank transition audit

Date: 2026-11-07. **Analysis choices recorded before this new ranking computation.** This is an exploratory *read-only* secondary characterization of the already preregistered Phase 2H H2/H3 checkpoint rank dynamics, NOT a new confirmatory causal hypothesis, not a Phase 2G modification and not a Phase 2U neural fit.

## Frozen inputs
Use all 18 unchanged, receipt-verified original A/F `arm.json` archives from official Phase2G GitHub run 35572084785, nine evolution seeds and all 40 events per arm. No prospective samples, no re-estimation of neural scores, no heldout H opening, no neural model fitting.

## Unit and comparison gate
For each paired seed, generation 0..19 and stage `shortlist`/`survival`, mark the A/F contexts directly comparable only if their **sets** of `selected_before` AND their **sets** of `b1_group` exactly match, and each original selection event passes set-difference validity checks. Even when a context is not comparable, report whether `selected_after` sets match; do not treat that as a controlled model comparison.

A score-ranking comparison is *eligible* only when the comparable B1 group contains at least two distinct fingerprints, each arm has `scored_candidate_count == len(b1_group)` and has one finite `assigned_scores` entry for every group fingerprint. Reject corrupted/contradictory score receipts rather than quietly ignore them.

For every eligible comparable context, compare each unordered pair of group fingerprints under both arms' original neural advantage scores (smaller is better). Classify pair comparisons as **both strict same direction**, **both strict reversed direction**, **tie in both**, **tie transition (one tied, one strict)**. These are candidate-level *ranking* changes, not selected-member changes or classical dominance. Report every eligible event including zero-discordance events. Record the number of such pairs and maximum absolute cross-arm score difference across the matched candidates. Secondary labels may not be turned into an inferential or causal conclusion.

Report, for all nine seeds and each checkpoint-relevant generation, exact counts of comparable contexts, eligible scored contexts, rank-reversal and tie-transition pairs, matching selected-after contexts, first A/F selection divergence and first eligible rank divergence. Explicitly report 0–4, 5–9, 10–14, 15–19 blocks. For first generation-5 `shortlist`, record whether selected candidate sets differ and how many strict ranking reversals occur. Do not select seeds after inspecting outcomes.

## Constraints
Only descriptive counts and per-seed full records. No new p-values, no generalizable security claim, no attribution to an OpenBLAS CPU backend, no model performance enhancement, no automatic Phase 2I intervention. Frozen negative Phase2G verdict remains `phase2g_adaptive_coevolution_not_supported`. Independently verify original 18 ZIP SHA and JSON scientific receipts plus computed canonical output SHA, preserve a downloadable source/JSON evidence package; report unavailable cells explicitly.
