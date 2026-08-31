# Phase 1 preregistered confirmation — result

## Provenance

- frozen experiment commit: `d225a970592cc3c73c5b830af1622c59610ba53c`
- GitHub Actions run: `33346715978`
- archived artifact ID: `9742286753`
- artifact SHA-256: `423157b296c1c5dc056ca118478badf9c03026dca3a1a4af06eaa5506d28fbcf`
- protocol: `research/PHASE1_CONFIRMATION_PROTOCOL.md`
- configuration: `local_3swap_x3`
- confirmatory seeds: `211, 223, 227, 229, 233, 239, 241, 251, 257`
- unique evaluation budget: 154 GA + 154 random per seed
- CI on the frozen experiment: green on Python 3.10, 3.11, and 3.12

## Preregistered verdict

**`gate1_red`**

The relative-search-advantage criterion did not pass the preregistered exact
one-sided sign test, and no independent GA run reached all hard admissibility
gates.

- GA primary wins: **5**
- random primary wins: **2**
- primary ties: **2**
- exact one-sided sign-test p-value: **0.2265625** (`alpha=0.05`)
- admissible GA candidates: **0 / 9**
- admissible random candidates: **0 / 9**

## Aggregate metrics

| Metric | GA median | Random median | Direction |
|---|---:|---:|---|
| Nonlinearity | **98** | 96 | GA better |
| Differential uniformity | 10 | 10 | tie |
| Maximum linear correlation | **60** | 64 | GA better |

The trend is therefore favorable to the GA but is **not statistically confirmed**
under the preregistered criterion and does **not** satisfy full Gate 1.

## Seed-by-seed primary results

| Seed | Outcome | GA NL | GA DU | GA max-LAT | Random NL | Random DU | Random max-LAT |
|---:|---|---:|---:|---:|---:|---:|---:|
| 211 | GA | 98 | 10 | 60 | 96 | 10 | 64 |
| 223 | GA | 98 | 10 | 60 | 96 | 10 | 64 |
| 227 | GA | 98 | 10 | 60 | 96 | 10 | 64 |
| 229 | Random | 98 | 12 | 60 | 98 | 10 | 60 |
| 233 | Tie | 96 | 10 | 64 | 96 | 10 | 64 |
| 239 | Random | 96 | 10 | 64 | 98 | 12 | 60 |
| 241 | GA | 98 | 10 | 60 | 96 | 10 | 64 |
| 251 | GA | 98 | 10 | 60 | 96 | 10 | 64 |
| 257 | Tie | 96 | 10 | 64 | 96 | 10 | 64 |

## Diagnostic conclusion

The GA is no longer stagnant: each confirmatory trajectory improved its current
best multiple times, and five runs converged to the recurring region
`NL=98, DU=10, max-LAT=60`. The remaining bottleneck is crossing the hard region
`NL>=100` and `DU<=8` simultaneously.

The confirmatory seeds above are now retired from tuning. Any next optimization
iteration must use new development seeds and, if promoted, another fresh set of
confirmation seeds.
