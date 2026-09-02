# Phase 1I — Fresh-population plateau-transfer development protocol

## Status

Preregistered development protocol. This file is committed before any Phase-1I scientific execution.

Phase 1I is a classical S-box search experiment only. It does **not** enable the neural oracle and does not turn global Gate 1 green by itself.

## Question

Can the plateau-directed proposal selector that succeeded from the verified Phase-1H warm-start be transferred to a genuinely fresh population, with no historical S-box loaded into the run, and produce hard-admissible 8x8 S-boxes more often than an equal-full-evaluation fresh GA?

## Frozen seed split

Development seeds:

- 1709
- 1721
- 1723
- 1733
- 1741

Reserved confirmation seeds, quarantined during development:

- 1801
- 1811
- 1823
- 1831
- 1847
- 1861
- 1871
- 1873
- 1877

The central seed registry must reject any overlap with prior experiments.

## Hard constraints

Unchanged:

- nonlinearity >= 100
- differential uniformity <= 8
- max absolute linear correlation <= 64
- algebraic degree >= 6
- |SAC - 0.5| <= 0.05

The structural target excludes SAC and requires the first four conditions only.

## No warm-start rule

The transfer arm must not call, import for execution, deserialize, or seed itself from any historical Phase-1B/1D/1E/1H S-box candidate.

Every Phase-1I run begins from a fresh pseudorandom population generated only from its declared seed.

Historical candidates may appear in documentation or unit-test fixtures, but never as a search parent, archive member, immigrant, or comparator seed in the scientific run.

## Common fresh GA configuration

The discovery GA and continued-GA comparator use the Phase-1F feasibility-first configuration:

- population size: 20
- elite count: 4
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- immigrant fraction: 0.10
- offspring multiplier: 2
- ranking mode: `feasibility_first`

For this configuration the exact full-evaluation budget is `20 + 32 * generations`.

## Exact budgets

Single frozen configuration; there is no development grid.

### Transfer arm

1. Fresh GA discovery: 16 generations = 532 unique full classical evaluations.
2. Plateau-directed repair: 1088 additional unique full classical evaluations.
3. Exact total: 1620 unique full classical evaluations.

### Continued-GA comparator

- 50 generations = 1620 unique full classical evaluations.

### Random comparator

- 1620 unique fresh random permutations.

Budget equality refers to full CryptoShield classical evaluations. Plateau proposal projection is deliberately cheap pre-screening and is not counted as a full evaluation, so CPU time is not claimed to be equal.

## Frozen transfer operator

After the 532-evaluation discovery prefix:

1. Build an archive from the eight highest feasibility-ranked discovery candidates.
2. Repeatedly choose one archive parent uniformly with the seeded RNG.
3. Build the exact Phase-1H `ties` LAT/DDT plateau diagnostics for that parent.
4. Generate 96 unique cycle-4 permutation proposals, with at least one changed position anchored in the current hotspot union.
5. Rank the 96 proposals with the frozen Phase-1H local projection key:
   - lower projected LAT-panel maximum,
   - lower projected DDT-panel maximum,
   - more current-max LAT cells reduced,
   - more current-max DDT cells reduced,
   - lower projected LAT sum,
   - lower projected DDT sum,
   - deterministic proposal order.
6. Fully evaluate only the best unseen proposal.
7. Re-rank the archive by `feasibility_first` and retain the best eight fully evaluated candidates.
8. Continue until exactly 1088 repair evaluations have been charged.

No post-hoc switch of panel mode, proposal pool, cycle length, archive width, discovery length, or total budget is allowed.

## Primary scientific comparison

For each development seed, compare the transfer arm against the continued-GA arm using the frozen feasibility-first rank of the best fully evaluated S-box. Random search is a calibration control, not the primary comparator.

Report per arm:

- whether any structural target was found,
- whether any hard-admissible S-box was found,
- first target/admissible evaluation if present,
- best classical metrics and fingerprint,
- exact unique full-evaluation count.

Report transfer-vs-GA wins/losses/ties and transfer-vs-random wins/losses/ties.

## Frozen development prerequisite for confirmation

All of the following must hold on the five development seeds:

1. transfer hard-admissible runs >= 2/5;
2. transfer structural-target runs >= 2/5;
3. transfer hard-admissible count > continued-GA hard-admissible count;
4. transfer structural-target count > continued-GA structural-target count;
5. transfer wins vs continued GA > transfer losses vs continued GA;
6. median transfer nonlinearity >= 98;
7. median transfer differential uniformity <= 8;
8. median transfer max linear correlation <= 60;
9. every arm consumes exactly 1620 unique full classical evaluations with provenance.

If any prerequisite fails, Phase 1I development is negative, confirmation seeds remain unused, global Gate 1 stays RED, and the neural oracle stays blocked.

If all prerequisites pass, exactly one separate confirmation protocol must be committed **before** any reserved confirmation seed is executed. That protocol must reuse this single frozen transfer configuration without tuning.

## Interpretation boundary

A positive Phase-1I development result is only evidence that the Phase-1H mechanism can transfer away from the historical warm-start on development seeds. It is not sufficient by itself to green global Gate 1 or enable neural fitness.
