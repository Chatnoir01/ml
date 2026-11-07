# Phase 2H-FORK2 — Frozen B1 score-swap decision replay, preregistered exploratory audit (2026-11-07)

**LOCK BEFORE ALL NEW REPLAY CALCULATIONS.** Source evidence has already been inspected in Phase2H; this is retrospective exploratory software-causal identifiability at a single ranking decision, *not* prospective/randomized evidence of terminal effect. Do not train any neural model, mutate original Phase2G, access Phase2U sealed work or touch any held-out oracle.

## Inputs

Use every unchanged original Phase2G A/F archived ZIP for all nine historical evolution seeds `726011,726023,726037,726049,726061,726073,726087,726099,726113`; prove ZIP CRC and canonical embedded scientific receipt integrity before analysis. Verify original arm identity and all 40 unique `(generation,stage)` events per arm. The baseline independent archives and results already have known original SHA256 digests. Record exact source SHA and code digest in derived output. Read only `selection_events` and `classical_evaluation_ledger` needed for membership check (no H).

## Intervention definition

For every `(seed,generation,stage)` exactly matched on `selected_before` **set**, `b1_group` **set**, `cutoff`, original `cutoff_reference_fingerprint`, `boundary_opportunity`, and every frozen candidate's four classical metrics, require 2 or more B1 candidates, B1 crosses the cutoff, `scored_candidate_count == len(B1)`, and full finite unique candidate `assigned_scores` for each A/F event. Missing/partial/contradictory data must fail closed; record unscored events as unavailable with reason, not equivalent.

Let `B` be the frozen B1 candidate set and `S` the common historical classical `selected_before` set. `k = |B ∩ S|`. The B1 cutoff algorithm may change only `B` membership. For any admissible score map X on B, define:

`replay(X) = (S \\ B) ∪ lowest_k(B, X)`.

Rank lower-is-better, stable ties follow original frozen historical B1 order rather than an arbitrary fingerprint sort. **If any score tie at the decision boundary whose native historical order is not derivable unambiguously from archived evidence, mark that event unavailable instead of fabricating an order.** Require no outside-B1 crossings. Compare `replay(A_scores)` and `replay(F_scores)` to the original A and F `selected_after` sets, respectively, to reproduce the actual native decisions before doing any score-swap claim. If any disagreement, mark the experiment invalid (never silently drop that seed). Then exchange score maps while leaving S, B, cutoff and k **unchanged**; quantify `do(A_event.score <- F_scores)`, `do(F_event.score <- A_scores)` and their symmetric membership differences, and require exact reconstruction of the opposite originally selected set.

## Comparators and report

Full denominator: 360 historical A/F stage-event pairs, not just the 9 known interesting rows. Partition: directly comparable B1/selected contexts; score-comparable; actual membership changes; score-swap changed selected membership; ties; exact reproduction; non-comparable unavailable. Predefine negative control `generations 0..4` where no strict A/F rank reversals were observed in the pre-registered earlier analysis; compare all comparable events there. Primary focus `generation=5,stage=shortlist` for all nine seeds, but report all eligible generation-5+ pairs. Preserve all nine per-seed original fingerprints and swapped selections. Compare exact 4-coordinate classical multiset distributions for sets exclusive to A/F; report relative classical quality separately without using H.

## Interpretation firewall

This is an exact *local deterministic operator* counterfactual from archival scores: if the exact historical B1 inputs are replayed and swapped, the candidate-set change at this node is mechanically attributable to score assignment. It does **not** identify any terminal heldout causal effect, train-data cause, hardware cause or cipher security improvement; later GA parent/proposal RNG paths diverge and original neural weights are not archived. No Phase2I intervention can run until an independently frozen Phase2H verdict selects exactly one H1/H2/H3/H4 family under `phase2i_gate.py`; do NOT bypass the existing `PHASE2I_DESIGN_ENVELOPE.md`.

## Outputs / falsification

Canonical complete JSON rows and totals; 18 source SHA identities; 18 original scientific SHA checks; zero-score-tie checks; deterministic reverse-input-order invariant; independent second verifier recomputing score-swap memberships from ZIP source and standalone code, and negative tests: missing candidate, duplicate score, wrong cutoff, changed selected_before, corrupt ZIP/payload and rank tie. Keep original source ZIPs and scripts in downloadable ZIP, with checksum manifest. No scientific p-values, no main merge, DRAFT stacked PR.
