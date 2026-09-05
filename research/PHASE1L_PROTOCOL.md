# Phase 1L — Fresh ITO-aware Pareto development protocol

## Status

Preregistered development experiment. This protocol is committed before any Phase-1L scientific execution.

Phase 1L tests whether the Phase-1K ITO-aware Pareto mechanism improves the terminal multi-objective set on genuinely fresh populations. It does **not** enable the neural oracle and cannot turn global Gate 1 green by itself.

## Fresh seed split

Development seeds:

- 1901
- 1907
- 1913
- 1931
- 1933

Reserved confirmation seeds, quarantined during development:

- 2003
- 2011
- 2017
- 2027
- 2029
- 2039
- 2053
- 2063
- 2069

The central seed registry must reject every overlap with earlier experiments.

## Frozen hard constraints

Unchanged from prior Phase-1 work:

- nonlinearity >= 100
- differential uniformity <= 8
- max absolute linear correlation <= 64
- algebraic degree >= 6
- |SAC - 0.5| <= 0.05

The structural target excludes SAC and requires the first four conditions.

## Three frozen arms

All arms start from the same seed-driven fresh initial population and consume exactly 340 unique full classical CryptoShield evaluations per development seed.

### Arm A — ITO-aware staged Pareto

`StagedParetoConfig`:

- population size: 20
- generations: 20
- shortlist size: 8
- parent count: 4
- mutation swaps: 3
- crossover rate: 0.0
- seed: development seed

Exact classical budget:

`20 + 20 * (20 - 4) = 340`

Every current candidate is classically ranked with the frozen `feasibility_first` policy. Only the top 8 receive actual Improved Transparency Order evaluation. Parent selection inside that shortlist uses six-objective Pareto dominance plus deterministic NSGA-II crowding:

1. nonlinearity — maximize;
2. differential uniformity — minimize;
3. max absolute linear correlation — minimize;
4. Improved Transparency Order — minimize;
5. |SAC - 0.5| — minimize;
6. algebraic degree — maximize.

### Arm B — staged Pareto ITO ablation

Uses the exact same `StagedParetoConfig`, seed, initial population, operators, shortlist size, parent count and classical budget as Arm A.

During selection only, the ITO evaluator is replaced by a constant neutral value. This preserves the same staged/Pareto machinery while removing the ITO selection signal. Actual ITO is measured post hoc on terminal Pareto candidates for comparison and is never fed back into this arm.

This is the primary causal comparator for the ITO objective.

### Arm C — historical feasibility-first GA

`EvolutionConfig`:

- population size: 20
- generations: 10
- elite count: 4
- tournament size: 3
- mutation swaps: 3
- crossover rate: 0.0
- immigrant fraction: 0.10
- offspring multiplier: 2
- seed: development seed

Ranking mode: `feasibility_first`.

Exact classical budget:

`20 + 10 * (20 - 4) * 2 = 340`

This arm is a historical external comparator, not the primary isolation test for ITO.

## Budget interpretation

Classical CryptoShield evaluations are exactly matched at 340 per arm per seed.

ITO computation is deliberately **not** counted as a classical evaluation. Arm A pays extra ITO wall-clock cost because ITO is the experimental signal. Arm B pays only post-hoc ITO measurement on its terminal front. Arm C pays one post-hoc ITO measurement on its final best candidate.

Therefore Phase 1L claims equal classical evidence budget, not equal CPU time.

## Terminal-set comparison

No weighted scalar objective is allowed.

For each terminal candidate, actual six-objective metrics are constructed. Between Arm A and Arm B, compute directed Pareto set coverage:

`C(A,B) = fraction of B terminal candidates dominated by at least one A terminal candidate`

`C(B,A) = fraction of A terminal candidates dominated by at least one B terminal candidate`

A seed is an Arm-A coverage win when `C(A,B) > C(B,A)`, a loss when the reverse holds, and a tie otherwise.

Also report:

- size of each terminal Pareto set;
- minimum actual ITO on each terminal set;
- hard-admissible candidate count per terminal set;
- structural-target candidate count per terminal set;
- best feasibility-first classical metrics per arm;
- ITO of the best feasibility-first candidate per arm;
- exact classical and ITO evaluation counts;
- fingerprints of all reported terminal candidates.

Arm C is compared descriptively against each staged arm using the frozen feasibility-first classical key and post-hoc ITO.

## Frozen development prerequisite for confirmation

All of the following must hold on the five development seeds:

1. Arm A coverage wins over Arm B > Arm A coverage losses;
2. median `C(A,B)` > median `C(B,A)`;
3. median minimum actual ITO of Arm A < median minimum actual ITO of Arm B;
4. Arm A hard-admissible terminal-set count across seeds >= Arm B count;
5. Arm A structural-target terminal-set count across seeds >= Arm B count;
6. every Arm A, B and C run consumes exactly 340 unique full classical evaluations;
7. every development seed is fresh and the reserved confirmation seeds remain unused;
8. no neural model, neural fitness or neural oracle is executed.

If any prerequisite fails, Phase 1L development is negative, confirmation seeds remain unused, global Gate 1 remains RED, and the neural oracle remains blocked.

If all prerequisites pass, exactly one separate confirmation protocol must be committed **before** any reserved confirmation seed is executed. No Phase-1L parameter may be tuned between development and confirmation.

## Interpretation boundary

A positive Phase-1L development result would mean the ITO objective adds measurable value to the terminal six-objective Pareto set under this frozen development design. It would not prove hardware DPA resistance, superiority to AES, cryptographic deployment readiness, or neural co-evolution success.
