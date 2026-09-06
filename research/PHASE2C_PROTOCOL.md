# Phase 2C-A — Oracle pressure transmission diagnostics

## Status

PREREGISTERED / ARTIFACT-ONLY / NO REPLAY

Governing issues:

- #103 — preregistration
- #104 — execution lock

## Scientific question

Phase 2B was a valid negative experiment: the frozen one-way GA ← Neural Oracle pressure mechanism did not satisfy the held-out support criteria while classical non-degradation remained intact.

Phase 2C-A asks a narrower diagnostic question:

> Using only the already-frozen Phase 2B artifacts, what can be measured about the amount, location, and persistence of Oracle pressure, and where does the existing evidence become structurally insufficient?

Phase 2C-A does not test a new optimizer and cannot rescue Phase 2B.

## Frozen source

- Phase 2B scientific SHA: `59066ad943fc85f24a21b4c2941cbcee4d23aeae`
- Phase 2B workflow run: `34064310593`
- Phase 2B result: `research/PHASE2B_RESULT.md`
- Phase 2B merge commit: `7080f50150dc2feaeb0df7c2193ed880992a39d8`
- arms: `control`, `oracle`, `shuffled`
- evolution seeds: `(326011, 326023, 326033, 326047, 326051, 326063, 326071, 326087, 326099)`
- expected arm cells: `27`
- exact Oracle score budget: `32` candidates per arm/seed

## Inputs

Allowed inputs are only the frozen `arm.json` records and final frozen aggregate produced by Phase 2B run `34064310593`.

No Phase 2B arm or neural scorer may be rerun. No new neural training, evolution, candidate generation, or Block-V scoring is permitted in Phase 2C-A.

## Measurable fields from the frozen schema

The Phase 2B runner records:

- `oracle_events`;
- `oracle_cutoff_tie` events with cutoff, protected key, base-order fingerprints, and assigned scores;
- `oracle_selection_budget_closed` events with cutoff, group size, and remaining budget;
- Oracle receipts with `role` equal to `selection` or `padding`;
- exact candidate-score and training budgets;
- terminal candidate and terminal classical metrics;
- proposal audit digest.

Therefore Phase 2C-A will deterministically measure, for every arm/seed where available:

1. number of cutoff-tie events;
2. number at shortlist cutoff `8`;
3. number at survival cutoff `20`;
4. number of budget-close events;
5. number of Oracle candidate scores used during selection;
6. number used only for post-terminal audit padding;
7. fraction of the 32-score budget that participated in selection;
8. for Oracle/shuffled tie events, whether the recorded assigned-score order differs from the recorded classical base order;
9. group-size distributions and remaining budget at closure.

## Explicitly non-inferable fields unless present in the frozen artifacts

The analyzer must not invent information that Phase 2B did not record. In particular, source inspection shows that the frozen event payload does not explicitly contain:

- generation index for each tie event;
- boundary-group `start` and `end` indices in the full ranked pool;
- selected membership before and after the reorder;
- parent/descendant lineage identifiers across generations;
- terminal ancestry.

If these fields are absent in the actual frozen artifacts, the following questions are non-measurable in Phase 2C-A:

- exact number of candidate membership flips across each cutoff;
- persistence of an Oracle-caused membership change for 1/2/5 generations;
- descendant survival to terminal selection;
- whether the Phase-1O terminal rule erased a particular earlier Oracle intervention.

Absence must yield an explicit `non_measurable` record; it must not be reconstructed from assumptions.

## Diagnostic categories

Exactly one final Phase 2C-A classification is allowed:

- `phase2c_pressure_sparse`
- `phase2c_pressure_active_no_fitness_alignment`
- `phase2c_fitness_alignment_no_persistence`
- `phase2c_pressure_active_no_heldout_support`
- `phase2c_artifacts_insufficient`

Because categories involving causal persistence require fields that may not exist, `phase2c_artifacts_insufficient` is the mandatory classification if the frozen schema cannot distinguish the required alternatives without replay or new instrumentation.

## Determinism and integrity

The analyzer must:

- require exactly one record for each of the 27 arm/seed cells;
- reject duplicate cells;
- reject unknown arms, seeds, event types, or receipt roles;
- require Phase `2B` and expected schema version;
- validate exact 32-score / 512-training budgets;
- count selection versus padding receipts from frozen records only;
- serialize output canonically;
- produce a SHA-256 payload receipt;
- produce byte-identical output across two executions on the same inputs.

## Interpretation boundary

Block V remains the already-frozen Phase 2B endpoint. Phase 2C-A may quote the frozen verdict but must not use per-seed Block-V outcomes to choose a mechanism, threshold, subset, or rule.

If Phase 2C-A ends in `phase2c_artifacts_insufficient`, any deterministic replay with richer instrumentation becomes Phase 2C-B and requires a new preregistration before execution.

Any new optimization mechanism becomes Phase 2D and requires fresh validation seeds and its own preregistration.

## Scope

Educational/defensive ToySPN research only. No deployed-cipher or operational cryptanalytic claim is authorized.
