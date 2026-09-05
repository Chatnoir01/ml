# Phase 1L — Pre-registered multi-seed comparison

## Status

Pre-registered experimental protocol. Criteria are frozen before result generation. This phase does **not** enable the neural oracle by itself.

## Research question

At matched classical-evaluation budget, does the staged ITO-aware Pareto/NSGA-II search introduced in Phase 1K produce a reproducible improvement over the frozen historical `feasibility_first` GA rather than a seed-specific anecdote?

## Frozen arms

- **Control:** historical GA using the unchanged `feasibility_first` ranking.
- **Treatment:** staged ITO-aware Pareto/NSGA-II search from Phase 1K.

No ranking-rule changes are permitted after results are observed.

## Frozen objective vector

For every final candidate report:

1. nonlinearity — maximize;
2. differential uniformity — minimize;
3. maximum absolute linear correlation — minimize;
4. Improved Transparency Order — minimize;
5. absolute SAC deviation from 0.5 — minimize;
6. algebraic degree — maximize.

No weighted scalar score is allowed.

## Budget and seeds

Use 10 fresh deterministic seeds:

`104729, 130363, 155921, 181081, 206369, 231701, 257053, 282571, 308081, 333271`

For each seed, both arms receive the same classical-evaluation budget. Treatment ITO evaluations are reported separately and must never be silently counted as free work.

The runner records wall-clock time for both arms, but wall-clock time is a cost metric, not the primary quality endpoint.

## Primary endpoint

For each seed, compare the final treatment Pareto set against the final control candidate using strict Pareto relations over the frozen six-objective vector.

Classify the seed as:

- `WIN`: at least one treatment candidate strictly dominates the control and the control dominates no treatment candidate;
- `LOSS`: the control strictly dominates at least one treatment candidate and no treatment candidate dominates the control;
- `MIXED`: both directions of strict dominance occur;
- `INCOMPARABLE`: neither direction occurs.

The primary aggregate result is the pre-registered count of WIN / LOSS / MIXED / INCOMPARABLE across all 10 seeds.

## Secondary endpoints

Report, without collapsing them into one score:

- per-objective treatment-minus-control deltas;
- median and range of each objective by arm;
- treatment Pareto-front size;
- classical evaluation count by arm;
- ITO evaluation count by arm;
- wall-clock seconds by arm;
- unique-candidate count where available.

## Gate interpretation

Phase 1L is considered evidence of a reproducible search improvement only if all of the following hold:

1. at least 6 of 10 seeds are `WIN`;
2. no more than 1 of 10 seeds is `LOSS`;
3. the treatment does not show a systematic regression in any frozen objective, defined as a worse median than control on that objective;
4. all runs complete with the frozen code and seed list;
5. historical regression CI remains green.

Failure of these criteria leaves global Gate 1 RED. Passing them is necessary evidence for the next gate review, not automatic proof of superior cryptographic security and not authorization to enable the neural oracle.

## Evidence requirements

The experiment must emit machine-readable JSON containing:

- repository commit SHA when available;
- Python version;
- frozen seed list;
- complete configuration for both arms;
- per-seed raw metrics and classifications;
- aggregate classifications;
- evaluation counts;
- timing;
- a deterministic digest of the result payload.

The raw JSON artifact is retained by CI. Human-readable summaries must be derivable from that raw artifact.

## Anti-p-hacking boundary

After the first result artifact exists, do not change seeds, primary classification, objective directions, or pass thresholds in this protocol to improve the conclusion. Any later protocol change requires a new phase/version and a new fresh seed set.
