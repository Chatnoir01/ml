# Phase 1H confirmation protocol — frozen `ties_p96`

## Scope

This is a **warm-start operator confirmation**, not global Gate-1 confirmation.

Development selected `ties_p96` using the preregistered Phase-1H selection rule. Confirmation tests that exact operator configuration on nine untouched reserved seeds. No tuning, alternate panel, alternate pool size, budget increase, seed substitution, or post-hoc retry is permitted.

Even a passing Phase-1H confirmation leaves global Gate 1 RED until the mechanism transfers to a fresh-population matched experiment. The neural-oracle phase therefore remains blocked.

## Frozen provenance gate

Every confirmation pair must first reproduce the exact historical Phase-1B frontier candidate and assert:

- NL `98`
- DU `8`
- max linear correlation `60`
- algebraic degree `7`
- SAC `0.501708984375`
- fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

Any mismatch aborts the run and cannot be counted as evidence.

## Confirmation seeds

Use exactly the nine Phase-1H reserved confirmation seeds:

`1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657`

No development or earlier-phase seed is allowed.

## Frozen directed configuration

- panel mode: `ties`
- LAT panel: every non-trivial cell at current maximum absolute correlation
- DDT panel: every non-trivial cell at current differential uniformity
- proposal pool: `96`
- permutation mutation: cycle rotation
- cycle length: `4`
- beam width: `8`
- strict archive frontier: DU `<=8`, max linear correlation `<=64`, degree `>=6`
- full classical evaluations: exactly `600` unique candidates per seed
- proposal ranking: exactly the Phase-1H development surrogate frozen in `research/PHASE1H_DEV_PROTOCOL.md`

No Phase-1H configuration parameter is exposed as a confirmation tuning knob.

## Frozen comparator

For the same seed, start, and full-evaluation budget, run the existing strict Phase-1E comparator:

- guidance: combined DDT + LAT hotspot indices
- cycle length: `4`
- beam width: `8`
- full classical evaluations: exactly `600` unique candidates per seed
- comparator RNG seed: deterministic fixed XOR from the registered confirmation seed

The comparison remains matched on full CryptoShield evaluations, not CPU time.

## Outcome definitions

Structural target:

- NL `>=100`
- DU `<=8`
- max linear correlation `<=64`
- algebraic degree `>=6`

Hard admissibility additionally requires the existing SAC gate.

Pairwise outcome uses the existing Phase-1D continuation rank of each arm's best fully evaluated candidate. Ties are excluded from the sign-test denominator.

## Exact sign test

Let `W` be directed wins and `L` comparator wins among non-tied pairs, `n=W+L`.

Under the null `p=0.5`, use the exact one-sided tail:

`P[X >= W] = sum(C(n,k), k=W..n) / 2^n`

If `W <= L` or `n=0`, the one-sided p-value is defined as `1.0` for this confirmation gate.

## Frozen pass criteria

Phase-1H warm-start confirmation passes **only if all** of the following hold across the nine seeds:

1. directed hard-admissible runs `>=5/9`;
2. directed structural-target runs `>=5/9`;
3. directed hard-admissible count is strictly greater than comparator hard-admissible count;
4. directed structural-target count is strictly greater than comparator structural-target count;
5. directed wins are strictly greater than comparator wins;
6. exact one-sided sign-test `p < 0.05` on non-tied pair outcomes;
7. median directed nonlinearity `>=100`;
8. median directed differential uniformity `<=8`;
9. median directed max linear correlation `<=56`;
10. every directed and comparator arm consumed exactly `600` full classical evaluations and passed the historical provenance gate.

There is no partial-pass status. The verdict is either:

- `warm_start_confirm_pass`, or
- `warm_start_confirm_fail`.

## Evidence requirements

Record per seed:

- historical receipt metrics/fingerprint;
- directed best metrics/fingerprint;
- comparator best metrics/fingerprint;
- directed/comparator target status;
- directed/comparator hard-admissible status;
- first target/admissible evaluation where available;
- exact full evaluation counts;
- pairwise outcome.

Aggregate:

- target/admissible counts per arm;
- directed/comparator wins and ties;
- exact sign-test p-value;
- medians NL/DU/max-correlation;
- all ten frozen checks and final verdict;
- workflow run, frozen confirmation SHA, artifact ID, SHA-256 digest.

## No-rerun rule

A scientific failure is retained. Confirmation seeds are not recycled or substituted. A workflow/infrastructure failure may only be rerun if the failure occurred before the affected scientific arm produced a usable result and the rerun executes the exact same frozen code/configuration; such a rerun must be documented explicitly.

## Interpretation constraint

A `warm_start_confirm_pass` confirms only that plateau-directed `ties_p96` robustly improves continuation from the verified historical `98/8/60` frontier under this matched full-evaluation budget. It does **not** turn global Gate 1 green.

After a pass, the next scientific step must be a fresh-population transfer experiment with newly preregistered development/confirmation seeds. Neural-oracle work remains blocked until global Gate 1 passes.
