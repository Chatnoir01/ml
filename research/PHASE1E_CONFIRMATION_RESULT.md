# Phase 1E — frozen hotspot-guided confirmation result

Status: **RED — development success did not replicate; global Gate 1 remains RED; neural phase remains blocked**.

## Frozen protocol and execution

Confirmation protocol commit: `0bc26d04783dd89527b334f42eddd4ddfc978794`.

Frozen confirmation runner/workflow SHA: `8ec80041e817f1e09886891fa79adde1fac7f265`.

GitHub Actions run: `33464705778`.

Frozen configuration:

- guidance: `combined`
- cycle length: `4`
- beam width: `8`
- evaluations per side per seed: `600`
- guided vs equal-budget unguided adaptive comparator
- seeds: `1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051`

All nine jobs completed successfully. Every job reproduced the historical warm-start receipt exactly at `NL=98`, `DU=8`, max correlation `60`, degree `7`, fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`.

## Per-seed confirmation outcomes

| Seed | Rank outcome | Guided target | Unguided target | Guided admissible | Unguided admissible | Guided NL/DU/corr | Unguided NL/DU/corr |
|---:|---|---:|---:|---:|---:|---|---|
| 1009 | unguided | no | no | no | no | 98/8/60 | 98/8/60 |
| 1013 | tie | no | no | no | no | 98/8/60 | 98/8/60 |
| 1019 | tie | no | no | no | no | 98/8/60 | 98/8/60 |
| 1021 | guided | no | no | no | no | 98/8/60 | 98/8/60 |
| 1031 | tie | no | no | no | no | 98/8/60 | 98/8/60 |
| 1033 | guided | no | no | no | no | 98/8/60 | 98/8/60 |
| 1039 | tie | no | no | no | no | 98/8/60 | 98/8/60 |
| 1049 | unguided | no | no | no | no | 98/8/60 | 98/8/60 |
| 1051 | tie | no | no | no | no | 98/8/60 | 98/8/60 |

Rank outcome totals: guided `2`, unguided `2`, ties `5`.

The non-tied exact one-sided sign test is therefore based on `n=4` and yields:

`P[X >= 2 | X ~ Binomial(4, 0.5)] = 11/16 = 0.6875`.

Target totals (`NL>=100` and `DU<=8`): guided `0/9`, unguided `0/9`.

Hard-admissible totals: guided `0/9`, unguided `0/9`.

Median best metrics:

- guided: `NL=98`, `DU=8`, max correlation `60`
- unguided: `NL=98`, `DU=8`, max correlation `60`

The two guided rank wins and two unguided rank wins therefore reflect lower-order rank coordinates rather than any improvement in the three primary structural metrics.

## Artifact receipts

- seed `1009`: artifact `9784470350`, `sha256:73aad8c55454a176af50766e592b9da2a1ecf89512848e79737a4d3c055538b6`
- seed `1013`: artifact `9784469750`, `sha256:a9bacf3de875a207b8cbc9108e0adb3e259237bbd2146ba3b40f9a9791521c5b`
- seed `1019`: artifact `9784472146`, `sha256:62d497213dbd959e6db2c3ea23e08694a3ce326d86cd5f87c9c42aee964a3bb2`
- seed `1021`: artifact `9784470263`, `sha256:55d23fec0b612bbb25687dc77038d7d56a4c884988281d8b22061211ca664b28`
- seed `1031`: artifact `9784468394`, `sha256:60622f0d0e978b1ff590cd186daaad53b6deec54b0bf48612451bab4894ba1ce`
- seed `1033`: artifact `9784462322`, `sha256:e2b8bfbe276cdec4385a2913904f37f1e64802963dd821e0d3fb8f85da482e19`
- seed `1039`: artifact `9784453935`, `sha256:f13de4e0913a655c31a85d5827cd101a28f1794acbfacb2c19c0b575e6a4dbf8`
- seed `1049`: artifact `9784468611`, `sha256:0ed46b78d82b6818774b4fe9b8cafac17fb79dd85e65f8a9ad26c033ec718c9f`
- seed `1051`: artifact `9784469881`, `sha256:50601b8595ade6011742fa7fc4c614011cb038fb48b2a3d80b882583573c9d9d`

## Preregistered criteria

| Criterion | Result |
|---|---|
| 1. exact provenance | PASS |
| 2. guided target successes >=3/9 | **FAIL (0/9)** |
| 3. guided target successes > unguided | **FAIL (0 vs 0)** |
| 4. guided hard-admissible successes >=3/9 | **FAIL (0/9)** |
| 5. guided admissible successes > unguided | **FAIL (0 vs 0)** |
| 6. guided rank superiority with one-sided sign `p<=0.05` | **FAIL (2 vs 2, p=0.6875)** |
| 7. median guided NL non-worse | PASS (98 vs 98) |
| 8. median guided DU non-worse | PASS (8 vs 8) |
| 9. median guided max correlation non-worse | PASS (60 vs 60) |

Because all criteria were required, the frozen Phase-1E confirmation verdict is **RED**.

## Scientific conclusion

The Phase-1E development hit at seed `907` (`NL=100 / DU=8 / corr=56 / degree=7`, fingerprint `7829ea8f4130a2cfd4c93c2337ff04d8373f6d981525eafc19db184dc61bb0c9`) is retained as a valid development observation, but it did not replicate on any of the nine fresh confirmation seeds.

No post-hoc retuning is performed on these confirmation seeds. They are retired from future development/confirmation work.

The evidence therefore supports a conservative interpretation: hotspot-guided combined cycle-4 proposals can occasionally cross the local `NL=98` plateau, but repeated warm-start superiority has not been demonstrated at the frozen budget.

Global Gate 1 remains **RED**, and the neural-oracle phase remains blocked. Any next classical experiment must use a new preregistered hypothesis and fresh seeds; the Phase-1E confirmation seeds must never be reused for tuning.
