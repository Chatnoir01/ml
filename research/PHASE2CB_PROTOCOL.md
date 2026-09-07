# Phase 2C-B — Frozen-score instrumented replay protocol

## Status

**PREREGISTERED / IMPLEMENTATION ONLY / REAL REPLAY NOT YET AUTHORIZED**

Governing issues:

- #106 — preregistration
- #107 — execution lock

Phase 2C-B is a deterministic forensic replay of Phase 2B. It is not a new optimizer, not a retry of the Phase 2B support hypothesis, and not adaptive GA↔NN co-evolution.

## Frozen source

- Phase 2B scientific SHA: `59066ad943fc85f24a21b4c2941cbcee4d23aeae`
- Phase 2B workflow run: `34064310593`
- Phase 2C-A merge on `main`: `fc66ac5d5dde2763d64873cf794d6a2b18e122fa`
- Phase 2C-A source manifest SHA: `875452613c9a9dca6e119a46b872e628f26223470c3eb9ccc351f97d048cf50c`
- Phase 2C-A diagnostic SHA: `185efeb156ba3c2a75cbe9f27375ec795c15e6dc6db208dfd79931d04596c432`

The real replay, once authorized, must use exactly the 27 frozen Phase 2B `arm.json` payloads from run `34064310593`.

## Frozen-score rule

Each replay cell receives its own original Phase 2B `oracle_receipts` as a read-only score cache.

The replay must never call a neural scorer. A first-use candidate fingerprint that is absent from the original frozen receipt set is a hard provenance failure.

The cache must preserve historical candidate-score budget semantics:

- total historical score cap: 32 unique candidate scores per arm/seed;
- repeated use of an already-consumed candidate score costs zero additional slots;
- the sequence of newly consumed **selection-role** fingerprints must exactly match the original receipt sequence restricted to `role == "selection"`;
- padding receipts are audit history only and must not affect replay evolution;
- after historical selection-budget closure, later boundary opportunities may be observed but remain scoreless and cannot alter ordering.

`new_neural_trainings` is always 0 in Phase 2C-B.

## Exact replay identity gate

Before instrumentation may be interpreted, every one of the 27 arm/seed cells must match the original Phase 2B artifact on all of:

1. initial population digest;
2. classical evaluation count (340);
3. selection-role score fingerprint consumption sequence;
4. legacy Oracle-event projection;
5. proposal audit SHA-256;
6. terminal fingerprint;
7. terminal S-box;
8. terminal classical metrics;
9. final `oracle_selection_closed` state.

Overall replay status is limited to:

- `phase2cb_replay_valid`
- `phase2cb_replay_provenance_failure`
- `phase2cb_inconclusive_prerequisites`

Any identity failure blocks interpretation of persistence or ancestry diagnostics.

## Instrumented boundary record

For every selection call, record:

- generation;
- stage: `shortlist`, `survival`, or `terminal_shortlist`;
- cutoff;
- whether an exact protected-key group straddled the cutoff;
- protected key;
- group start/end indices in classical base order;
- group fingerprints in classical base order;
- group fingerprints after the historical arm rule;
- score budget remaining before/after;
- selection closed before/after;
- group score eligibility;
- whether the no-partial-group rule blocked scoring;
- selected membership before/after;
- entered/exited fingerprints;
- whether order changed;
- whether membership changed;
- whether the event is observational-only because selection pressure was already closed.

The legacy event stream used for identity comparison remains a separate exact Phase 2B-compatible projection.

## Generation and ancestry record

For each of the 20 generations record:

- population before shortlist;
- selected shortlist;
- selected parent fingerprints;
- each generated proposal fingerprint and its direct parent fingerprint;
- next population.

Phase 1O global proposal uniqueness allows a unique realized parent map. The replay may therefore compute ancestry chains for generated candidates without counterfactual reconstruction.

For candidates that **enter** a selected set because of an Oracle membership flip, report:

- direct presence at +1, +2, +5 generations where defined;
- whether any realized descendant is present at +1, +2, +5;
- whether the final terminal candidate is the candidate itself or a realized descendant.

These are realized-trajectory diagnostics only. They do not estimate what the excluded candidate would have produced under a counterfactual RNG trajectory.

## Descriptive outputs

Without outcome-driven thresholds, report:

- membership-flip event counts by arm/seed/stage;
- ordering-only event counts;
- opportunity counts before and after budget closure;
- score-budget utilization;
- entered/exited candidate counts;
- direct and lineage persistence at +1/+2/+5;
- terminal ancestry from Oracle-entered candidates;
- cells where ordering changes but membership never changes;
- cells where membership changes but no entered lineage persists;
- full 27-cell replay identity table.

No Phase 2D rule may be selected or implemented inside Phase 2C-B.

## Execution marker

Real replay remains blocked until a future commit adds exactly:

`research/PHASE2CB_EXECUTE.md`

containing the single line:

`AUTHORIZED_PHASE2CB_FROZEN_SCORE_REPLAY`

Before that marker, only implementation and synthetic/unit testing are authorized.

## Pre-marker gates

Before the marker may be created:

- synthetic cache-miss test must fail closed;
- synthetic instrumentation must leave legacy selection unchanged;
- post-closure observation must not affect evolution;
- replay code must have no neural scorer import/call path;
- replay workflow must install without neural extras;
- Phase 0 CI Python 3.10/3.11/3.12 must be green;
- historical Phase 1 Benchmark must be green;
- branch diff must not modify Phase 2B result, seeds, thresholds, budgets, Oracle datasets, or Block-V definitions.

## Scope

Educational/defensive ToySPN research only. No AES/deployed-cipher claim, operational key recovery, or adaptive attack deployment is authorized.
