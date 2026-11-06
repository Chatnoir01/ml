# Phase 2H — First frozen-artifact inspection

This note records only facts derived from the official Phase-2G workflow artifacts
(run `35572084785`). It is **not** the Phase-2H final verdict.

## Evidence recovered

All 18 primary A/F arm artifacts (nine paired seeds) remain available. Their
`arm.json` payloads contain substantially more diagnostic evidence than the
terminal freeze alone:

- exact curriculum fingerprints at each checkpoint;
- population-before and population-after fingerprints;
- score receipts and selection events;
- score-caused entrants/exits;
- classical evaluation ledger;
- generation trace and parent map.

This means H2 and H3 can be investigated from frozen evidence without rerunning
Phase 2G.

## Strong structural observation: A curriculum replacement

Across seeds 726011 through 726099, successive A checkpoint curricula at
0→5, 5→10, and 10→15 have Jaccard overlap **0.0**.

For seed 726113, the first two transitions are also 0.0 and the final transition
has Jaccard overlap about **0.026** (one shared item out of the union).

By construction and as independently visible in the artifacts, F's curriculum
has Jaccard overlap **1.0** at every checkpoint transition for all nine seeds.

Therefore the adaptive curriculum in 2G was not making small incremental
updates: it was effectively replacing the 20-item curriculum at each checkpoint.

This is evidence of very high curriculum drift. It is **not by itself evidence
of cycling**, because movement alone does not demonstrate recurrence or
direction reversal.

## Population turnover is not unique to A

Checkpoint population-after sets also have extremely low successive overlap in
both A and F (mostly zero, with occasional overlaps around 0.026–0.053).

Therefore high population turnover alone cannot explain the A-vs-F terminal
difference. The diagnostically distinctive fact visible so far is that A couples
that moving population to a nearly completely replaced training curriculum,
whereas F holds the training curriculum invariant.

This makes H4 (stability advantage of F) a serious hypothesis, but not yet a
causal conclusion.

## Selection events

A has score-caused entry events throughout the run: 38–40 such events per seed
in this first inspection. The classical ledger and entrant/exit fingerprints
are present, so H3 can now be tested directly rather than marked unavailable.

The initial implementation conservatively marked candidate-level classical
distortion unavailable before the official arm artifacts were recovered. That
availability flag must now be upgraded in the next code revision.

## H1 remains separated

The arm artifacts contain checkpoint model receipts/hashes, but the committed
artifact does not directly contain a ready-made cross-checkpoint immutable-probe
forgetting matrix. H1 must therefore remain unclaimed until a leakage-free
evaluation path is established from frozen model/probe evidence.

## Current interpretation boundary

The strongest fact at this stage is:

`A: moving population + near-total curriculum replacement`

versus

`F: moving population + invariant curriculum`.

Given that F beat A on held-out H on 9/9 seeds, this sharply focuses the next
diagnostic on whether the moving training target introduces instability,
forgetting, or selection distortion. It does not yet establish which mechanism
is causal.
