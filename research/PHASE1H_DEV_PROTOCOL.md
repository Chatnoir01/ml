# Phase 1H development protocol — plateau-directed cycle selection

## Scope

Phase 1H is a **warm-start operator-mechanism development experiment**, not global Gate-1 evidence.

Phase 1G showed that relaxing the strict-frontier acceptance rule did not solve the `NL≈98` plateau: 2,762 off-frontier states were accepted across the four preregistered configurations, but only three returns to the strict frontier were recorded and no development run reached the structural target or hard admissibility.

Phase 1H therefore changes the **proposal-selection mechanism**, not the acceptance rule. The hypothesis is that previous hotspot-guided cycle mutations were still too weakly directed: one hotspot anchor was used, but the remaining positions were largely random. Phase 1H generates a pool of permutation-preserving cycle-4 proposals and cheaply ranks them by their **exact local effect on the current LAT/DDT plateau cells** before spending one full classical evaluation on the selected proposal.

No neural component is introduced. Global Gate 1 remains RED unless a later fresh-population matched protocol passes.

## Provenance gate

Before accepting any Phase-1H result, the runner must reproduce the exact historical Phase-1B frontier candidate through the existing receipt function and assert:

- nonlinearity: `98`
- differential uniformity: `8`
- max linear correlation: `60`
- algebraic degree: `7`
- SAC: `0.501708984375`
- fingerprint: `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

Any mismatch aborts the experiment.

## Seeds

Development seeds, declared before any Phase-1H implementation result:

`1501, 1511, 1523, 1531, 1543`

Reserved confirmation seeds, quarantined during development:

`1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657`

The reserved seeds MUST NOT be used in development. They remain unused if the development prerequisite fails.

## Shared start, acceptance rule, and comparator

Both arms begin from the exact verified historical frontier candidate.

The adaptive archive is frozen to the strict structural frontier used previously:

- differential uniformity `<= 8`;
- max linear correlation `<= 64`;
- algebraic degree `>= 6`.

Only frontier candidates may enter the beam. Beam width is `8`.

The comparator is the existing Phase-1E strict guided adaptive search:

- guidance: `combined` DDT + LAT hotspot indices;
- permutation-preserving cycle rotation;
- cycle length: `4`;
- beam width: `8`;
- exact budget: `600` unique full classical evaluations per seed.

The Phase-1H arm receives the same `600` unique full classical evaluations per seed. Cheap proposal scoring does **not** count as a full fitness evaluation; therefore this experiment compares equal full classical evaluation budgets, not equal CPU time.

## Plateau diagnostics

For each selected parent, construct exact current diagnostics before proposing children.

### LAT panel

The full current LAT is computed once per cached parent. Non-trivial cells are ordered by descending absolute correlation.

Two panel modes are preregistered:

- `ties`: all cells whose absolute correlation equals the current maximum;
- `band4`: all cells whose absolute correlation is at least `current_max - 4`.

For every panel cell `(a,b,C)`, a proposed cycle changes only four S-box output positions. Its projected new correlation is computed **exactly for that cell** by adding the contribution deltas of only those changed positions. No full LAT is needed for proposal scoring.

The primary LAT surrogate is the projected maximum absolute correlation across the selected panel. Secondary LAT diagnostics are the number of current maximum cells that are strictly reduced and the sum of projected absolute correlations across the panel.

### DDT panel

The full current DDT is computed once per cached parent. Non-trivial cells are ordered by descending count.

Two panel modes are preregistered together with the LAT mode:

- `ties`: all cells whose count equals the current differential uniformity;
- `band2`: all cells whose count is at least `current_DU - 2`.

For a panel cell `(dx,dy,count)`, changing four S-box positions can affect only terms involving a changed input position or that position XOR `dx`. The projected count is computed **exactly for that DDT cell** from those affected terms.

The primary DDT surrogate is the projected maximum count across the selected panel. Secondary DDT diagnostics are the number of current maximum cells strictly reduced and the sum of projected counts across the panel.

These are exact local projections for the frozen panel cells, but they are **not** treated as substitutes for full CryptoShield metrics: every selected proposal still receives a complete classical evaluation, which is the only value used for archive admission and scientific outcomes.

## Plateau-directed proposal generation

For each full-evaluation slot:

1. choose one parent uniformly from the current beam archive;
2. build/cache its LAT and DDT panels;
3. construct the union of input indices participating in the current worst LAT and DDT cells;
4. generate `proposal_pool` distinct cycle-4 permutations, each forced to contain at least one index from that hotspot union;
5. compute exact panel-local projections for each proposal;
6. rank proposals lexicographically by the frozen surrogate key below;
7. spend one full classical evaluation on the highest-ranked unseen proposal only.

Frozen surrogate ranking, best first:

1. lower projected maximum absolute LAT-panel correlation;
2. lower projected maximum DDT-panel count;
3. more current-max LAT cells strictly reduced;
4. more current-max DDT cells strictly reduced;
5. lower sum of projected absolute LAT-panel correlations;
6. lower sum of projected DDT-panel counts;
7. deterministic proposal order generated from the seeded RNG.

Permutation preservation is mandatory. Duplicate full candidates are discarded before the fitness budget is charged.

## Frozen development configurations

Declaration order is part of the final tie-break.

1. `ties_p32`: LAT `ties`, DDT `ties`, proposal pool `32`;
2. `ties_p96`: LAT `ties`, DDT `ties`, proposal pool `96`;
3. `band_p32`: LAT `band4`, DDT `band2`, proposal pool `32`;
4. `band_p96`: LAT `band4`, DDT `band2`, proposal pool `96`.

Shared settings:

- cycle length: `4`;
- beam width: `8`;
- plateau-directed arm: exactly `600` unique full classical evaluations per seed;
- existing combined-cycle4 strict comparator: exactly `600` unique full classical evaluations per seed;
- development seeds: exactly the five registered Phase-1H development seeds.

No configuration, panel definition, score coordinate, budget, or seed may be changed after the first Phase-1H development result is observed.

## Recorded diagnostics

Per run record at minimum:

- historical warm-start receipt and fingerprint;
- exact full evaluation count;
- best metrics and fingerprint;
- target and hard-admissible success, with first full-evaluation index;
- number of frontier candidates admitted;
- proposal pools generated;
- duplicate proposals skipped;
- distribution of selected proposals' projected LAT maximum deltas;
- distribution of selected proposals' projected DDT maximum deltas;
- count of selected proposals predicted to reduce at least one current-max LAT cell;
- count of selected proposals predicted to reduce at least one current-max DDT cell;
- actual best NL/DU/max-correlation metrics after full evaluation.

## Target definitions

Structural target:

- nonlinearity `>= 100`;
- differential uniformity `<= 8`;
- max linear correlation `<= 64`;
- algebraic degree `>= 6`.

Hard admissibility additionally requires the existing SAC gate.

## Frozen selection rule

Choose one configuration lexicographically by:

1. plateau-directed hard-admissible runs;
2. plateau-directed structural-target runs;
3. hard-admissible success margin over the strict comparator;
4. structural-target success margin over the strict comparator;
5. plateau-directed wins minus comparator wins on the existing continuation rank;
6. higher median plateau-directed nonlinearity;
7. lower median plateau-directed differential uniformity;
8. lower median plateau-directed max linear correlation;
9. higher count of selected proposals with a strictly lower projected LAT-panel maximum;
10. declaration order.

## Development stop rule

**If no Phase-1H configuration produces at least one hard-admissible development success, Phase-1H confirmation MUST NOT be executed.**

In that case:

- all reserved Phase-1H confirmation seeds remain unused;
- the negative result is retained;
- global Gate 1 remains RED;
- neural-oracle work remains blocked.

If one or more configurations produce a hard-admissible development success, select exactly one using the frozen rule above. A separate confirmation protocol with fixed criteria must be committed before any reserved confirmation seed is used.

## Interpretation constraint

A positive Phase-1H warm-start result would establish only that exact plateau-local proposal selection improves continuation from the verified historical frontier candidate under the frozen evaluation budget. It would not by itself establish global Gate 1. Fresh-population matched evidence and repeated hard admissibility would still be required before unblocking the neural-oracle stage.
