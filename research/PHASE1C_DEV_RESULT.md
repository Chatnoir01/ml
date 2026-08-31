# Phase 1C development result — balanced feasibility

Status: **development evidence only — not confirmatory**.

## Frozen execution

- workflow run: `33349831153`
- head SHA: `0db9986f167d0e5baabefcb11a8d83ec386a7b07`
- fresh development seeds: `503, 509, 521, 523, 541`
- exact budget: `252` unique GA evaluations and `252` unique random evaluations per seed
- comparison key: `balanced_primary_key_v1`
- search rank: `balanced_feasibility_v1`

## Results

| Configuration | GA / random / ties | Admissible GA/random | NL+DU gate GA/random | Median NL GA/random | Median DU GA/random | Median max corr GA/random |
|---|---:|---:|---:|---:|---:|---:|
| `balanced_swap1` | 1 / 2 / 2 | 0 / 0 | 0 / 0 | 96 / 98 | 10 / 10 | 64 / 60 |
| `balanced_swap2` | 2 / 1 / 2 | 0 / 0 | 0 / 0 | 98 / 98 | 10 / 10 | 60 / 60 |
| `balanced_swap3` | **2 / 0 / 3** | 0 / 0 | 0 / 0 | 98 / 98 | 10 / 10 | 60 / 60 |
| `balanced_swap4` | **2 / 0 / 3** | 0 / 0 | 0 / 0 | 98 / 98 | 10 / 10 | 60 / 60 |
| `balanced_swap5` | 2 / 2 / 1 | 0 / 0 | 0 / 0 | 98 / 98 | 10 / 10 | 60 / 60 |

Every configuration has zero fully admissible runs, zero structural-admissible
runs and zero simultaneous `NL>=100` + `DU<=8` runs. `balanced_swap3` and
`balanced_swap4` are exactly tied on every preregistered numerical selection
coordinate, so declaration order selects **`balanced_swap3`**.

## Selected configuration seed-level result

`balanced_swap3` converged to the same GA endpoint on every development seed:

| Seed | Outcome | GA NL | GA DU | GA max corr | Random NL | Random DU | Random max corr |
|---:|---|---:|---:|---:|---:|---:|---:|
| 503 | GA | 98 | 10 | 60 | 96 | 10 | 64 |
| 509 | GA | 98 | 10 | 60 | 96 | 10 | 64 |
| 521 | tie | 98 | 10 | 60 | 98 | 10 | 60 |
| 523 | tie | 98 | 10 | 60 | 98 | 10 | 60 |
| 541 | tie | 98 | 10 | 60 | 98 | 10 | 60 |

This removes the Phase-1B failure mode where `NL=98, DU=12` could outrank a
more balanced candidate, but it exposes a stable **98/10/60 plateau**. The V3
ranking did not reproduce the earlier development-only `98/8/60` point and did
not enter the `NL>=100, DU<=8` region.

## Artifact receipts

- `balanced_swap1`: artifact `9743277676`, `sha256:e82d76cf6e80544b8420580d08d7c6c6286b13a3c725ce42c827fd3944d583fc`
- `balanced_swap2`: artifact `9743276381`, `sha256:442bf0f85ff0c9f5e666d61f030e0cd845cdff62a1bc2d8f7f73fa4659e334ac`
- `balanced_swap3`: artifact `9743277504`, `sha256:3220a93d9866c12b2d0d0f2e63ad10175a891ab5fcbcd27f4024d30b52c278f3`
- `balanced_swap4`: artifact `9743277591`, `sha256:573c6d12d54fe4d2adebf78e4cce95109f31975e7ebd4833039af820070dd380`
- `balanced_swap5`: artifact `9743277705`, `sha256:5ac448f5dc4864d640e00dbb5a55d5b8715f185cd1c76477eb4faa946376257c`

## Scientific conclusion

Phase 1C is a useful negative development result. The balanced rank prevents a
large DU regression from being hidden by NL, but with the current local-swap
operators and 252-evaluation budget it does not break the `98/10/60` plateau.
No Gate-1 claim is made. Per the preregistered protocol, the selected
`balanced_swap3` configuration must still be frozen and tested once on the V3
confirmation seeds already reserved before this sweep.
