# Phase 1C — DU-frontier development result

Status: **development evidence only — negative result; no confirmation executed**.

## Frozen execution

- workflow run: `33349768637`
- head SHA: `f7b8f33ebdf65ebf83ff4aff553fa5c09fde35cf`
- development seeds: `503, 509, 521, 523, 541`
- population: 14
- generations: 10
- elite count: 2
- tournament size: 3
- crossover: 0.0
- offspring multiplier: 4
- exact budget: 494 unique GA evaluations and 494 equal-budget random evaluations per seed
- ranking: `du_frontier_v1`

## Results

| Configuration | Primary GA/random/ties | GA DU<=8 runs | GA near-frontier runs | GA admissible | Median NL GA/random | Median DU GA/random | Median max corr GA/random |
|---|---:|---:|---:|---:|---:|---:|---:|
| `local1_noimm` | 3 / 0 / 2 | 0 | 0 | 0 | 98 / 96 | 10 / 10 | 60 / 64 |
| `local2_noimm` | 3 / 1 / 1 | 0 | 0 | 0 | 98 / 96 | 10 / 10 | 60 / 64 |
| `local3_noimm` | 4 / 0 / 1 | 0 | 0 | 0 | 98 / 96 | 10 / 10 | 60 / 64 |
| `local5_noimm` | 4 / 0 / 1 | 0 | 0 | 0 | 98 / 96 | 10 / 10 | 60 / 64 |
| `local3_10imm` | 4 / 0 / 1 | 0 | 0 | 0 | 98 / 96 | 10 / 10 | 60 / 64 |
| `local3_20imm` | 4 / 1 / 0 | 0 | 0 | 0 | 98 / 96 | 10 / 10 | 60 / 64 |

The preregistered selection rule would choose `local3_noimm`: all configurations
tie on admissibility, near-frontier count, DU-frontier count and structural
medians, while `local3_noimm` is the first declaration-order configuration among
those with four primary GA wins.

However, **zero of 30 GA development runs reached `DU<=8`**. Confirmation is
therefore intentionally not executed. Consuming reserved confirmation seeds would
not test a development-supported hypothesis.

## Artifact receipts

- `local1_noimm`: artifact `9743348728`, `sha256:d29d86c4eac07ba11ed4edc13728d56d6b9ed8424f6ab28f62a69ca35a493b2e`
- `local2_noimm`: artifact `9743326448`, `sha256:d4038a8f6e52e7e3c261b079a1f85f998bf0eb9c018ccef3061d7e75a379b410`
- `local3_noimm`: artifact `9743298612`, `sha256:ec21e6f8684413baebdedad3f9ad6fd54694d920f36f53d6654af14578b16bf8`
- `local5_noimm`: artifact `9743325213`, `sha256:b609fa19eff42f22ab11eaa511946bd244896c2bdb742d8259358d956dd9c50a`
- `local3_10imm`: artifact `9743322029`, `sha256:c8296ac0528e20a7b251a7820ef9feb961c87cf7bb4c239e53052ee56f27a75d`
- `local3_20imm`: artifact `9743322449`, `sha256:6c41fa53c6306b8c9770f97937b9d59bbf67e364fb4e18c94c0b49e469311354`

## Scientific conclusion

The `du_frontier_v1` ranking improves the same primary medians seen in Phase 1B
(`NL=98`, max correlation `60`) but does not make entry into `DU<=8` reproducible
from fresh random populations. Merely prioritizing the DU gate is insufficient.

The next development question is narrower and different: starting from the
previously discovered Phase-1B `NL=98, DU=8, max-correlation=60` candidate, can a
frontier-preserving local operator increase NL to at least 100 without leaving
`DU<=8`? Such a continuation experiment must be labelled warm-start development
and cannot by itself establish global GA-vs-random Gate 1.
