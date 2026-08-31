# Phase 1B development result

Status: **development evidence only — not confirmatory**.

## Frozen execution

- workflow run: `33347279320`
- head SHA: `3a8b3d5a5920e992a552bca59ab9da13302b9aa3`
- fresh development seeds: `307, 311, 313, 317, 331`
- exact budget: `252` unique GA evaluations and `252` unique random evaluations per seed
- ranking mode: `feasibility_first`
- comparison mode: `primary`

## Results

| Configuration | Primary GA / random / ties | Admissible GA / random | Median NL GA / random | Median DU GA / random | Median max corr GA / random |
|---|---:|---:|---:|---:|---:|
| `f1_local1_noimm` | 3 / 1 / 1 | 0 / 0 | 98 / 96 | 10 / 10 | 60 / 64 |
| `f1_local3_noimm` | **5 / 0 / 0** | 0 / 0 | **98 / 96** | 10 / 10 | **60 / 64** |
| `f1_local5_noimm` | 3 / 1 / 1 | 0 / 0 | 98 / 96 | 10 / 10 | 60 / 64 |
| `f1_local3_20imm` | **5 / 0 / 0** | 0 / 0 | **98 / 96** | 10 / 10 | **60 / 64** |
| `f1_local3_40imm` | 4 / 0 / 1 | 0 / 0 | 98 / 96 | 10 / 10 | 60 / 64 |

The preregistered development selection rule leaves `f1_local3_noimm` and
`f1_local3_20imm` exactly tied through all numerical selection coordinates.
The protocol therefore selects the first declaration-order configuration:
**`f1_local3_noimm`**.

The strongest single development candidate occurred for seed `307` under
`f1_local3_noimm`: `NL=98`, `DU=8`, `max linear correlation=60`. It reaches the
DU hard gate but remains two NL points below the `NL>=100` gate, so it is **not
admissible**.

## Artifact receipts

- `f1_local1_noimm`: artifact `9742461236`, `sha256:0796f8cb5dc21c3b1e6a89ba3c3cb521498e8b31db3aa31dc531f4efa8c96d65`
- `f1_local3_noimm`: artifact `9742460601`, `sha256:9ead1a3caddafa20e9273b711dc7c72dcfa08faa3b4e5deee687a6f990b92e2a`
- `f1_local5_noimm`: artifact `9742458137`, `sha256:3bcf00f38894cdf0a8b5af5214d46d0ccb06f1faee8d535982a90d50eb3924d5`
- `f1_local3_20imm`: artifact `9742460494`, `sha256:4a0cdf854e22c528e927b1267b48d921f8916049783431b795fbcbc8efa10783`
- `f1_local3_40imm`: artifact `9742460587`, `sha256:88a83c181265cebd4286264f00c728c6c1742df24b6739827dced18816d05572`

## Scientific conclusion

The V2 ranking produces a clean structural development signal and, for one seed,
reaches `DU=8`. It still found zero fully admissible candidates. No Gate-1 claim
is made from this sweep. The selected configuration must now be frozen and tested
only on the separately reserved V2 confirmation seeds.
