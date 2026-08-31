# Phase 1B V2 confirmation result

Status: **confirmatory evidence — Gate 1 remains RED**.

## Frozen execution

- workflow run: `33349080847`
- head SHA: `fa823af5d9cb63d1f4db2aaad27b76b27fc1ab4f`
- reserved confirmation seeds: `401, 409, 419, 421, 431, 433, 439, 443, 449`
- selected configuration: `f1_local3_noimm`
- exact budget: `252` unique GA evaluations and `252` unique random evaluations per seed
- ranking mode: `feasibility_first`
- comparison mode: `primary`

## Preregistered verdict

- primary outcomes: **GA 4 / random 0 / ties 5**
- non-tied comparisons: `4`
- exact one-sided sign-test: **p = 0.0625**
- median constraint violation: `0.29` GA / `0.29` random
- median nonlinearity: **98 GA / 96 random**
- median differential uniformity: `10 GA / 10 random`
- median maximum linear correlation: **60 GA / 64 random**
- fully admissible runs: `0 GA / 0 random`
- Gate 1A primary search superiority: **FAIL**
- Gate 1B repeated hard admissibility: **FAIL**
- Full Gate 1: **FAIL / RED**

The structural medians improve in NL and maximum linear correlation and are non-worse in differential uniformity. However, the preregistered superiority gate also required `p < 0.05` and a strictly lower median constraint violation; neither condition was met. No fully hard-admissible S-Box was found, so Gate 1B also fails independently.

## Artifact receipt

- artifact ID: `9743093430`
- artifact digest: `sha256:29381fff6284539ff76e9aad32d6a01d98ea6d2128ee404092633e80060ad401`
- retention: 90 days

## Scientific interpretation

V2 confirms that the feasibility-first search has a reproducible structural advantage over equal-budget random search on NL and max linear correlation, but it does **not** yet establish Gate-1 search superiority under the frozen statistical criterion and it still does not enter the full hard-admissible region. This confirmation must remain frozen and must not be recycled as tuning data.
