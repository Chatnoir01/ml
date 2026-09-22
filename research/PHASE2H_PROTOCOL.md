# Phase 2H — Mechanistic diagnosis of Phase 2G

Status: **PREREGISTERED DIAGNOSTIC ONLY — NO 2G MUTATION, NO CLAIM OF IMPROVEMENT**

## Immutable parent evidence

Phase 2H is based on the frozen Phase-2G result at parent commit
`ba1aec133c50ddac246a54a70bb3ff2f0994df3a`.

Phase-2G aggregate SHA-256:
`1df1812bc58e088c6a639d7ccbb94e1f3a02feb0ebd9f8b04e4ac81b1ea983d2`.

Phase 2G remains immutable. 2H must not alter its cells, seeds, held-out H,
support thresholds, aggregate, verdict, or artifacts.

Observed trigger for 2H:
- adaptation activity: 9/9 seeds;
- cross-key mechanism activity: 9/9;
- A beats C: 9/9;
- A beats S: 7/9;
- A beats F: 0/9;
- mean A = 0.2844938666599919;
- mean F = 0.24243693462748478;
- F-A = -0.04205693203250708;
- classical non-degradation: 7/9.

## Scientific question

Why does adaptive arm A lose to fixed-retraining arm F on every Phase-2G
evolution seed despite demonstrably active adaptation and cross-key feedback?

2H is explanatory, not an optimization sweep.

## Frozen hypotheses

H1 — **forgetting / stability-plasticity cost**:
checkpoint models in A increasingly specialize to the current adaptive
curriculum and lose performance/ranking stability on earlier fixed probes.

H2 — **chasing / cycling**:
successive A curricula, score orderings, and selected populations repeatedly
move away from and/or return toward prior states rather than accumulating
monotonic progress.

H3 — **selection distortion**:
NN information is real, but score-caused boundary membership changes displace
candidates that are preferable under the frozen classical geometry.

H4 — **stability advantage of F**:
F wins because its invariant curriculum supplies a more stable reference,
not because A lacks adaptation activity.

No additional causal hypothesis may be promoted after inspecting 2H outputs.
Unexpected observations must be labelled exploratory and deferred.

## Analysis populations

Primary paired unit: the nine frozen Phase-2G evolution seeds.

Primary contrast: A versus F.

C and S are contextual controls only. They may not replace A-vs-F as the
primary diagnostic contrast.

No new evolution seed may be added to 2H after analysis starts.

## Required checkpoint diagnostics

For generations 0, 5, 10, 15, derive where existing Phase-2G receipts permit:

1. curriculum identity and pairwise checkpoint drift;
2. model-state identity/drift;
3. candidate score/rank order and rank turnover;
4. selection-event boundary opportunities;
5. score-caused entrants/exits and cross-protected-key changes;
6. population/candidate fingerprint turnover;
7. frozen classical metrics for affected candidates;
8. A/F divergence point per seed.

All diagnostics must be deterministic and receipt-bound.

## Immutable probe rule

A diagnostic probe set must be fixed before any comparative result is consumed.
It may be constructed only from information available at or before the
corresponding Phase-2G freeze boundary and must never adapt to a later A
population.

The same probe identities and scoring seeds must be used for A and F.

If the existing artifacts are insufficient to construct a leakage-free probe,
2H must report that metric as unavailable rather than invent or reconstruct
unrecorded scientific evidence.

## Forgetting matrix

When model states and leakage-free historical probes are available, construct:

`M[t, u] = performance/ranking of checkpoint model t on immutable probe u`

for t,u in {0,5,10,15}.

Predeclared H1 signatures:
- later A checkpoints degrade on earlier probes while F is materially more
  stable; and/or
- A current-probe improvement co-occurs with historical-probe degradation.

Report the full matrix. Do not reduce it to a hand-selected checkpoint.

## Cycling/chasing diagnostics

For A and F report checkpoint-to-checkpoint:
- curriculum Jaccard overlap;
- candidate/ranking overlap where comparable;
- rank correlation where a common candidate set exists;
- recurrence to earlier curriculum/candidate fingerprints;
- direction reversals in comparable score/rank deltas.

H2 is supported only by predeclared recurrence/reversal evidence. Mere movement
is not cycling.

## Selection-distortion diagnostics

For every fully scored B1 boundary event, identify score-caused membership
changes and compare frozen classical tuples of entrants/exits.

H3 evidence requires a repeated paired pattern in which A's neural intervention
causes a membership change followed by worse frozen classical geometry than the
corresponding non-neural/fixed reference. Raw neural-score movement alone is
insufficient.

## F-stability diagnostics

Quantify A-vs-F curriculum drift, model-state drift, rank turnover, and terminal
held-out difference by seed.

H4 evidence requires F to be materially more stable on the preregistered
stability measures and that stability to covary in the expected direction with
the paired A-F terminal gap. This is diagnostic association, not a causal claim.

## Multiple-hypothesis discipline

2H has exactly four confirmatory hypotheses: H1-H4.

Report every preregistered metric for all nine seeds, including null/adverse
results. No metric may be silently dropped because it weakens an explanation.

Where inferential tests are valid, report exact paired tests and effect sizes.
Small-n uncertainty must remain explicit. 2H does not reuse the Phase-2G
support threshold as a discovery threshold.

## Outputs

Required deterministic artifacts:
- `research/PHASE2H_PROTOCOL.md` (this file);
- `research/phase2h-diagnostics.json`;
- `research/PHASE2H_RESULT.md`;
- machine tests for determinism, parent-binding, no-H mutation, and complete
  reporting.

The diagnostics JSON must bind:
- parent Phase-2G commit;
- Phase-2G aggregate SHA-256;
- exact input artifact SHA-256 values;
- implementation commit;
- all metric outputs;
- availability/missing-evidence flags;
- a deterministic aggregate SHA-256.

## Hard separation from Phase 2I

2H may diagnose but must not implement replay, Hall-of-Fame, EMA/target models,
changed NN pressure, altered checkpoint cadence, new selection geometry, or any
other performance intervention.

Any corrective mechanism belongs to a separately preregistered Phase 2I on new
validation seeds/holdout.

## Stop rule

2H ends when all preregistered diagnostics are emitted or explicitly marked
unavailable with a reason. It does not continue until a preferred explanation
becomes significant.
