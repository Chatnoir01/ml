# Phase 2I — Intervention design envelope (DRAFT, NON-EXECUTABLE)

Status: **design work only**. Phase 2I is not authorized to execute until Phase
2H has emitted its frozen diagnostic result.

This document exists so engineering work can proceed while 2H CI/analysis is
pending without contaminating the scientific decision.

## Parent rule

2I must branch from the final frozen 2H result, not from a preferred
interpretation written during development.

No intervention may be selected because it happened to look good on the nine
Phase-2G seeds.

## Mechanism → intervention map

The intervention is selected mechanically from the 2H verdict:

### If H1 forgetting is supported

Candidate intervention family: **historical replay/archive**.

The NN curriculum combines current informative cases with a preregistered,
bounded historical buffer. Buffer capacity, replacement policy, current/history
ratio, and sampling seeds must be frozen before new scientific execution.

### If H2 chasing/cycling is supported

Candidate intervention family: **lagged/slow target**.

Permitted designs include a one-checkpoint lag or a preregistered EMA/target
model. Exactly one primary design must be chosen before execution; 2I is not a
hyperparameter sweep.

### If H3 selection distortion is supported

Candidate intervention family: **bounded neural influence**.

Classical geometry remains the arbiter. Neural information may break ties or
prioritize information gathering only inside a frozen protected band. It may not
silently widen B1 or override hard constraints.

### If H4 stability advantage is supported without H1-H3

Candidate intervention family: **partial curriculum retention**.

The adaptive curriculum keeps a preregistered stable core and replaces only a
bounded fraction at each checkpoint. The retained fraction is frozen before new
seeds are opened.

### If multiple mechanisms are supported

Do not combine fixes automatically. Select the smallest intervention that tests
one causal prediction. Combination belongs to a later separately preregistered
phase unless 2H itself preregistered an interaction prediction.

### If no mechanism is supported

2I must not run a rescue sweep. Report the diagnostic failure and design a new
measurement phase.

## Scientific controls

Minimum controls remain:
- C: classical control;
- F: fixed-retraining reference;
- A2: one mechanism-targeted intervention;
- S2: a falsification/shuffled control appropriate to the intervention.

Exact arm semantics must be frozen before execution.

## Freshness firewall

Phase-2G evolution seeds are development/diagnostic evidence only.

2I requires:
- a newly reserved evolution-seed block;
- newly reserved checkpoint training/scoring seeds where required;
- a physically isolated held-out block;
- no opening of held-out values before terminal freeze;
- exact budget identity checked in code.

No Phase-2G held-out score may be used to tune the intervention.

## Primary scientific question

Does the single mechanism-targeted intervention improve the A2-vs-F comparison
while preserving classical non-degradation and retaining evidence that the
intended GA↔NN mechanism is active?

The primary comparator remains F. Beating C alone is insufficient.

## Required evidence before execution

1. final Phase-2H result and aggregate hash;
2. exact mechanism selected by the frozen decision rule above;
3. arm semantics;
4. exact seed registries;
5. exact training budget;
6. exact support checks and statistical tests;
7. terminal-freeze/held-out procedure;
8. deterministic unit/integration tests;
9. execution-lock marker.

Until all nine exist, 2I remains non-executable.

## Phase 2J firewall

A positive 2I result is not a replication. Phase 2J must use another fresh,
independent seed/held-out block and reproduce the frozen 2I mechanism without
retuning it.
