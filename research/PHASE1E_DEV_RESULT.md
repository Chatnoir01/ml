# Phase 1E — hotspot-guided operator development result

Status: **development success for one warm-start operator; confirmation required; global Gate 1 remains RED**.

## Frozen run

Workflow run: `33463880389`.

Frozen experiment SHA: `35e08060b9cbf7b44303a5e7d827962f1b94d7a1`.

Development seeds: `907, 911, 919, 929, 937`.

Reserved confirmation seeds remain unused at the time of this result: `1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051`.

Every guided/unguided side used 600 unique evaluations, beam width 8, and the exact verified historical start `NL=98 / DU=8 / corr=60 / degree=7`, fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`.

## Results

| Configuration | Guided target | Unguided target | Guided admissible | Unguided admissible | Guided wins | Unguided wins | Ties | Median guided NL/DU/corr |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `ddt_cycle2` | 0/5 | 0/5 | 0/5 | 0/5 | 0 | 0 | 5 | 98/8/60 |
| `ddt_cycle3` | 0/5 | 0/5 | 0/5 | 0/5 | 0 | 0 | 5 | 98/8/60 |
| `lat_cycle2` | 0/5 | 0/5 | 0/5 | 0/5 | 0 | 0 | 5 | 98/8/60 |
| `lat_cycle3` | 0/5 | 0/5 | 0/5 | 0/5 | 0 | 1 | 4 | 98/8/60 |
| `combined_cycle3` | 0/5 | 0/5 | 0/5 | 0/5 | 0 | 0 | 5 | 98/8/60 |
| `combined_cycle4` | **1/5** | **0/5** | **1/5** | **0/5** | 2 | 1 | 2 | 98/8/60 |

No hotspot fallback occurred in any guided run.

## Selected configuration

The preregistered selection rule selects `combined_cycle4`, because it is the only configuration with any guided `NL>=100, DU<=8` success and its unguided comparator has none.

Successful development seed: `907`.

First target and hard-admissible hit: evaluation `580`.

Selected candidate metrics:

- nonlinearity: `100`
- differential uniformity: `8`
- maximum linear correlation: `56`
- algebraic degree: `7`
- SAC: `0.5009765625`
- fingerprint: `7829ea8f4130a2cfd4c93c2337ff04d8373f6d981525eafc19db184dc61bb0c9`

This is the first observed candidate in the current research line to cross the `NL>=100` hard threshold while preserving `DU<=8` under the frozen structural gates.

## Artifact receipts

- `ddt_cycle2`: artifact `9784351786`, `sha256:ae7017b5ccf7241321c5ad7758b79803befc06f72d42f351d4b39b461162c80d`
- `ddt_cycle3`: artifact `9784322482`, `sha256:09644fe5b5439fd716f8107d4c28afecf55a1fb7e76ac7942b51ae6d65f3f59d`
- `lat_cycle2`: artifact `9784265501`, `sha256:6a1e6a4a8f7aed5f83c99fc57b309f64b5c2dded39b11bec299b41e9762a3538`
- `lat_cycle3`: artifact `9784307726`, `sha256:d9df52e25edd83e39a3aa87b48bcc608b8ad6b03b60ac7b0c915ec1abba66336`
- `combined_cycle3`: artifact `9784344956`, `sha256:e2e26d9d444ec94542f6a665e401156b32c2326db9bdbd3c8c0e0cb60d855db7`
- `combined_cycle4`: artifact `9784331441`, `sha256:699ee821bf86efea7c24ef82c54d606aeea76ad997bbe2045ec4440fd5580a6b`

## Scientific interpretation

This development result is promising but insufficient by itself. `combined_cycle4` must now be frozen and tested on the nine already-reserved confirmation seeds. No further operator tuning is allowed before that confirmation.

Even a successful Phase-1E confirmation would establish only warm-start operator feasibility. It would not make global Gate 1 green, because global Gate 1 still requires fresh-population GA superiority over equal-budget random search with repeated hard-admissible candidates.
