# Phase 1F — fresh-population guided bridge development result

Status: **development negative; confirmation not executed; global Gate 1 remains RED; neural phase remains blocked**.

## Frozen protocol and run

Phase 1F was preregistered before execution in `research/PHASE1F_DEV_PROTOCOL.md`.

Frozen experiment/workflow SHA:

`452bde6b9ac01cbb7f4549c1db402910d2f35a56`

GitHub Actions run:

`33472235753`

Development seeds:

`1103, 1109, 1117, 1123, 1129`

Reserved confirmation seeds:

`1201, 1213, 1217, 1223, 1229, 1231, 1237, 1249, 1259`

The reserved confirmation seeds were not used by this development run.

Every memetic, continued-GA, and random-search arm consumed exactly `788` unique full classical S-Box evaluations per seed. The memetic arm always started from a fresh random population; no historical Phase-1B/1D/1E candidate was injected.

## Frozen configurations

| Configuration | Discovery | Guided repair | Total per arm |
|---|---:|---:|---:|
| `bridge10_c4` | 340 | 448 | 788 |
| `bridge13_c4` | 436 | 352 | 788 |
| `bridge16_c4` | 532 | 256 | 788 |

The guided repair operator was fixed to combined DDT+LAT hotspot guidance, cycle length 4 and beam width 8.

## Results

| Configuration | Memetic hard-admissible | Memetic structural target | GA hard-admissible | Random hard-admissible | Memetic vs GA | Memetic vs random | Median memetic NL/DU/corr |
|---|---:|---:|---:|---:|---|---|---|
| `bridge10_c4` | 0/5 | 0/5 | 0/5 | 0/5 | 0 win / 0 loss / 5 ties | 4 wins / 0 losses / 1 tie | 98/10/60 |
| `bridge13_c4` | 0/5 | 0/5 | 0/5 | 0/5 | 0 win / 0 loss / 5 ties | 4 wins / 0 losses / 1 tie | 98/10/60 |
| `bridge16_c4` | 0/5 | 0/5 | 0/5 | 0/5 | 1 win / 0 losses / 4 ties | 4 wins / 0 losses / 1 tie | 98/10/60 |

For all three configurations, the continued-GA and random-search median best structural metrics were also `NL=98 / DU=10 / corr=60`.

Across the 15 preregistered configuration-seed memetic development runs:

- hard-admissible successes: `0/15`;
- structural-target successes (`NL>=100`, `DU<=8`, max correlation `<=64`, degree `>=6`): `0/15`.

The primary-key wins against random search therefore do not constitute entry into the hard-admissible region and do not satisfy the preregistered advancement condition. In particular, SAC cannot create these primary comparisons, and the median structural metrics remained unchanged.

## Artifact receipts

- `bridge10_c4`: artifact `9787291581`, `sha256:f0794bfee344ef2935bd8e399cad1971cfb15db401cadb14e44566f853152567`
- `bridge13_c4`: artifact `9787255030`, `sha256:36780f561a19741c1520bc2626e71d92b20f678298d00536a0784b95756eb39f`
- `bridge16_c4`: artifact `9787299804`, `sha256:0cbfe320039b39a3307029c32ee5e342bcdb20bb5da700d133eed2d2c8366c5d`

All three matrix jobs completed successfully.

## Preregistered stop rule

The protocol states that if no Phase-1F memetic configuration produces a hard-admissible candidate on any development seed, confirmation is not executed.

Observed maximum hard-admissible count for every configuration: `0/5`.

Therefore the stop rule is triggered exactly as preregistered:

- **Phase 1F confirmation: NOT EXECUTED**;
- confirmation seeds `1201, 1213, 1217, 1223, 1229, 1231, 1237, 1249, 1259`: **UNUSED**;
- no Phase-1F configuration is selected for confirmation;
- no post-hoc budget increase, operator retuning, or seed substitution is performed.

## Scientific interpretation

Phase 1F tested a stronger and more globally relevant hypothesis than the Phase-1D/1E warm-start continuation experiments: fresh random populations first underwent feasibility-first evolutionary discovery, then the frozen Phase-1E `combined_cycle4` hotspot operator received a substantial local-repair budget.

At the frozen 788-evaluation budget, this bridge did not reproduce the historical `DU=8` frontier from fresh populations and did not produce any hard-admissible candidate. The repeated `NL=98 / DU=10 / corr=60` medians indicate that the main remaining bottleneck is still entry into the differential-uniformity frontier, not merely allocation of local-repair budget after ordinary discovery.

The next classical hypothesis, if pursued, should change the mechanism for entering or constructing the `DU<=8` region from fresh populations rather than simply re-splitting the same 788-evaluation budget or retuning `combined_cycle4` on these development seeds.

Global Gate 1 remains **RED**, and the neural-oracle phase remains **blocked**.
