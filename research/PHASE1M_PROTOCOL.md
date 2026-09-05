# Phase 1M — Fresh-population DDT-first repair protocol

## Status

Preregistered development experiment. This protocol is committed before `phase1m.py`, before any Phase-1M scientific run, and before any Phase-1M result is inspected.

Phase 1M tests one narrow mechanistic hypothesis suggested by Phase 1I: the fresh transfer search often reached NL 100 / DU 10 / max correlation 56, while the historical local proposal selector ranked projected LAT maximum before projected DDT maximum. Phase 1M asks whether making DDT reduction the primary local objective, subject to a non-regressing LAT guard, improves reliable entry into DU <= 8 without sacrificing the classical frontier or post-hoc ITO.

It does **not** enable the neural oracle. It cannot make global Gate 1 green by itself.

## Fresh seed split

Development seeds:

- 2111
- 2113
- 2129
- 2131
- 2137

Reserved confirmation seeds, quarantined during development:

- 2203
- 2207
- 2213
- 2221
- 2237
- 2239
- 2243
- 2251
- 2267

The central seed registry must reject every overlap with all earlier development, confirmation, reserved, or historical seeds.

## Frozen hard constraints

Unchanged:

- nonlinearity >= 100
- differential uniformity <= 8
- max absolute linear correlation <= 64
- algebraic degree >= 6
- |SAC - 0.5| <= 0.05

The structural target excludes SAC and requires the first four conditions.

## Frozen common search budget

Every arm is charged exactly **1,620 unique full classical CryptoShield evaluations per development seed**.

For the two repair arms, the first 532 evaluations are an identical deterministic fresh `feasibility_first` GA discovery prefix:

- population size: 20
- generations: 16
- elite count: 4
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- immigrant fraction: 0.10
- offspring multiplier: 2
- seed: development seed

Exact discovery budget:

`20 + 16 * (20 - 4) * 2 = 532`

The repair stage then spends exactly 1,088 new full evaluations, for a total of 1,620.

Repair constants for Arm A and Arm B:

- archive width: 8
- proposal pool: 96
- cycle mutation length: 4
- hotspot source: union of current maximum-LAT and maximum-DDT supports
- LAT/DDT diagnostic panel: exact `ties` panel
- repair RNG seed: `development_seed XOR 0x2D2D2D2D`

Cheap exact local projections over the 96 proposals are not counted as full CryptoShield evaluations. Therefore the experiment claims equal full classical evidence budget, not equal CPU time.

## Arm A — DDT-first under LAT guard

Arm A differs from Phase 1I only in local proposal ordering.

For each evaluated parent, generate 96 unseen hotspot-anchored cycle-4 proposals. For every proposal compute the existing exact local projection over the parent diagnostic panel.

The frozen lexicographic proposal key is:

1. LAT guard violation `max(0, projected_LAT_max - current_LAT_max)` — minimize;
2. projected DDT maximum — minimize;
3. number of current DDT-maximum cells reduced — maximize;
4. projected DDT panel sum — minimize;
5. projected LAT maximum — minimize;
6. number of current LAT-maximum cells reduced — maximize;
7. projected LAT panel sum — minimize;
8. deterministic proposal order — minimize.

This means a proposal that does not worsen the current LAT maximum is preferred over one that does. Inside the non-regressing LAT class, DDT pressure is primary.

Exactly one proposal per pool receives a full CryptoShield evaluation. Archive update, feasibility ranking, mutation operator, panel construction, proposal pool size, and budget accounting otherwise remain identical to Arm B.

## Arm B — historical balanced plateau selector

Arm B is the direct causal comparator and reproduces the Phase-1I repair selector from the same discovery prefix.

Its proposal ranking remains the historical `ProposalScore.ranking_key()` order:

1. projected LAT maximum;
2. projected DDT maximum;
3. current LAT-max cells reduced;
4. current DDT-max cells reduced;
5. projected LAT panel sum;
6. projected DDT panel sum;
7. deterministic proposal order.

Everything else is matched to Arm A.

## Arm C — continued fresh GA

Arm C is the external historical comparator:

- population size: 20
- generations: 50
- elite count: 4
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- immigrant fraction: 0.10
- offspring multiplier: 2
- seed: development seed
- ranking: `feasibility_first`

Exact budget:

`20 + 50 * (20 - 4) * 2 = 1620`

## ITO handling

Improved Transparency Order is **not** used to generate proposals, rank proposals, update the archive, or choose parents in Phase 1M.

After each arm completes, compute ITO exactly once on that arm's final best `feasibility_first` candidate. This is a frozen non-regression diagnostic and is reported separately from the classical budget.

No Phase-1L terminal candidate is loaded into the search. No historical S-box is used as a parent, archive member, immigrant, or warm-start.

## Per-seed outputs

For every arm report:

- best S-box fingerprint;
- NL, DU, max linear correlation, algebraic degree, SAC;
- post-hoc ITO of the final best candidate;
- whether a structural target was found anywhere in the charged evaluations;
- whether a hard-admissible candidate was found anywhere in the charged evaluations;
- first charged evaluation index reaching DU <= 8;
- first charged evaluation index reaching the structural target;
- first charged evaluation index reaching hard admissibility;
- unique full classical evaluation count.

For Arm A and B additionally report proposal-selector diagnostics, including how often the selected proposal reduced projected DDT maximum, reduced a current DDT-max cell, violated the LAT guard, and the distribution of selected projected DDT/LAT deltas.

## Frozen development prerequisites for confirmation

All conditions below must pass on the five development seeds:

1. Arm A hard-admissible runs >= 3/5;
2. Arm A structural-target runs >= 3/5;
3. Arm A hard-admissible runs > Arm B hard-admissible runs;
4. Arm A structural-target runs > Arm B structural-target runs;
5. Arm A wins over Arm B by frozen `feasibility_first` terminal rank > losses;
6. median final DU of Arm A <= 8;
7. median final NL of Arm A >= 100;
8. median final max linear correlation of Arm A <= 60;
9. median post-hoc ITO of Arm A <= median post-hoc ITO of Arm B;
10. every A, B, and C run consumes exactly 1,620 unique full classical evaluations;
11. every development seed is fresh and every reserved Phase-1M confirmation seed remains unused;
12. no neural model, neural fitness, neural oracle, historical warm-start, or Phase-1L terminal S-box is executed or loaded.

If any prerequisite fails, Phase 1M development is negative, confirmation seeds remain unused, global Gate 1 remains RED, and the neural oracle remains blocked.

If every prerequisite passes, exactly one separate confirmation protocol must be committed before any reserved confirmation seed is executed. No Phase-1M parameter may be tuned between development and confirmation.

## Interpretation boundary

A positive Phase-1M development result would support the narrow claim that DDT-first local proposal ordering, under the frozen LAT guard and equal full-evaluation budget, makes DU <= 8 materially more reproducible than the historical balanced selector on fresh populations while preserving the monitored ITO diagnostic.

It would not prove superiority to AES, deployment readiness, practical side-channel resistance, or neural co-evolution success.
