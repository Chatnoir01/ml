# Phase 1H confirmation result — plateau-directed `ties_p96`

## Verdict

**`warm_start_confirm_pass`**

Phase 1H confirmation passed every preregistered criterion on the nine untouched reserved confirmation seeds. This confirms the plateau-directed `ties_p96` operator as a robust warm-start continuation mechanism under the frozen matched evaluation budget.

This is **not** global Gate-1 confirmation. Per the frozen protocol, global Gate 1 remains RED until the mechanism transfers successfully to a fresh-population matched experiment. Neural-oracle work therefore remains blocked.

## Frozen confirmation receipt

- confirmation workflow run: `33525688258`
- frozen confirmation SHA: `f42567f9c0d7a7d861420cef5dfd6984ed108a57`
- job: `99915809977`
- job conclusion: `success`
- artifact ID: `9808391434`
- artifact name: `phase1h-confirmation-f42567f9c0d7a7d861420cef5dfd6984ed108a57`
- artifact digest: `sha256:bff09f0219f88e7cd7e79c507aceeee8c7d965d329517658046d96d22f6051fe`
- artifact size: `9057` bytes

No rerun was used.

## Frozen configuration

- selected development configuration: `ties_p96`
- panel mode: `ties`
- proposal pool: `96`
- cycle length: `4`
- beam width: `8`
- full classical evaluations per arm and seed: `600`
- confirmation seeds: `1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657`
- comparator: frozen strict combined-hotspot cycle-4 continuation search
- provenance start: verified historical Phase-1B frontier candidate `NL=98 / DU=8 / corr=60 / degree=7`, SAC `0.501708984375`, fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

## Aggregate result

Across the nine matched confirmation pairs:

- directed hard-admissible runs: **`7/9`**
- comparator hard-admissible runs: **`0/9`**
- directed structural-target runs: **`7/9`**
- comparator structural-target runs: **`0/9`**
- directed wins: **`7`**
- comparator wins: **`0`**
- ties: **`2`**
- non-tied pairs: **`7`**
- exact one-sided sign-test: **`p = 0.0078125`**
- median directed nonlinearity: **`100`**
- median directed differential uniformity: **`8`**
- median directed max linear correlation: **`56`**

## Frozen checks

All ten preregistered checks passed:

1. directed hard-admissible runs `>=5/9`: **PASS** (`7/9`)
2. directed structural-target runs `>=5/9`: **PASS** (`7/9`)
3. directed admissible count strictly greater than comparator: **PASS** (`7 > 0`)
4. directed target count strictly greater than comparator: **PASS** (`7 > 0`)
5. directed wins strictly greater than comparator wins: **PASS** (`7 > 0`)
6. exact one-sided sign-test `p < 0.05`: **PASS** (`0.0078125`)
7. median directed NL `>=100`: **PASS** (`100`)
8. median directed DU `<=8`: **PASS** (`8`)
9. median directed max correlation `<=56`: **PASS** (`56`)
10. exact budgets and historical provenance: **PASS**

## Scientific interpretation

The Phase-1H result is materially stronger than the earlier one-off Phase-1E development hit. The improvement now reproduced in a blinded reserved-seed confirmation set: seven of nine independent continuation runs reached both the structural target and full hard admissibility, while the equal-budget comparator reached neither on any of the nine seeds.

The mechanism-level conclusion supported by this experiment is narrow and positive: explicitly pre-ranking cycle-4 mutations by their exact local effect on the current tied worst LAT/DDT plateau can reliably cross the historical `NL≈98` continuation plateau under this warm-start setting.

The result does **not** establish that a fresh population can discover and exploit the same route reliably. Therefore:

- Phase 1H warm-start operator confirmation: **GREEN**
- global Gate 1: **RED**
- neural oracle: **BLOCKED**

## Required next step

Per the frozen confirmation protocol, the next experiment must test **fresh-population transfer** of the confirmed `ties_p96` mechanism using newly preregistered development and reserved confirmation seeds. No Phase-1H development or confirmation seed may be reused for that experiment.
