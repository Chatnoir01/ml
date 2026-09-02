# Phase 1I — Fresh-population plateau-transfer development result

## Frozen verdict

`fresh_transfer_dev_fail`

Phase 1I does **not** proceed to confirmation. Global Gate 1 remains **RED** and the neural oracle remains **blocked**.

This is nevertheless the first experiment in this sequence to produce a fully hard-admissible S-box from a genuinely fresh population with the plateau-directed mechanism: development seed `1741` reached an admissible candidate at charged full evaluation `682`, without any warm-start.

## Frozen provenance

- Development protocol committed before execution: `266a5bccfb0140523bb7c0d376c652a011b4db75`
- Frozen experimental SHA: `9ee48fa65c63a51c7ec9f09741aad64b0e87c3b4`
- Scientific workflow run: `33655252936`
- Independent Phase 0 CI on the frozen SHA: `33655252987` — Python 3.10/3.11/3.12 all GREEN
- Aggregate artifact: `9856767969`
- Aggregate artifact digest: `sha256:ae7a2256cc6ca850e25f39f759be388418848f9314f2646808ed2219c6b857c7`

The workflow preflight, all five development seed jobs, and the deterministic aggregate job completed successfully.

## Frozen configuration

No historical S-box was loaded as a search parent, archive member, immigrant, or warm-start.

Development seeds:

`1709, 1721, 1723, 1733, 1741`

Reserved confirmation seeds remain unused and quarantined:

`1801, 1811, 1823, 1831, 1847, 1861, 1871, 1873, 1877`

Each arm consumed exactly 1,620 unique full classical evaluations per development seed.

Transfer arm:

- fresh feasibility-first GA discovery: 16 generations = 532 evaluations
- plateau-directed repair: 1,088 evaluations
- archive width: 8
- LAT/DDT panel mode: `ties`
- proposal pool: 96
- mutation: cycle-4, hotspot anchored
- total: 1,620 full evaluations

Controls:

- continued fresh GA: 50 generations = 1,620 evaluations
- fresh random search: 1,620 evaluations

The cheap exact local projection of 96 proposals was not counted as a full CryptoShield evaluation; therefore the comparison is equal full-evaluation evidence budget, not equal CPU time.

## Aggregate result

| Metric | Transfer | Continued GA | Random |
|---|---:|---:|---:|
| Hard-admissible runs | **1/5** | 0/5 | 0/5 |
| Structural-target runs | **1/5** | 0/5 | 0/5 |
| Median nonlinearity | **100** | 98 | 98 |
| Median differential uniformity | **10** | 10 | 10 |
| Median max linear correlation | **56** | 60 | 60 |
| Transfer wins | — | **5/5** | **5/5** |
| Transfer losses | — | 0/5 | 0/5 |
| Ties | — | 0/5 | 0/5 |

The transfer mechanism therefore improved the best feasibility-ranked result on every development seed relative to both controls, but it did not reduce differential uniformity reliably enough to satisfy the preregistered transfer gate.

## Per-seed receipts

| Seed | Transfer best | Target / admissible | First admissible eval | Transfer fingerprint | vs GA | vs random |
|---:|---|---|---:|---|---|---|
| 1709 | NL 100 / DU 10 / corr 56 / deg 7 / SAC 0.5 | no / no | — | `cf63b5f103b9f7e77e2db7c274b2c7d85a509ef8cc4b47fadc9173b492a62c33` | win | win |
| 1721 | NL 100 / DU 10 / corr 56 / deg 7 / SAC 0.5 | no / no | — | `26f690da77399456444ff25d966731af1b8a84a565f12b1454a8cbd1a0093190` | win | win |
| 1723 | NL 100 / DU 10 / corr 56 / deg 7 / SAC 0.5 | no / no | — | `3258924f99f2038780ebafd97a489bdea0b40a830656c86a75a557a473192eb3` | win | win |
| 1733 | NL 100 / DU 10 / corr 56 / deg 7 / SAC 0.5 | no / no | — | `2925d0af0465c674d6129f530c341dda79eefe0b2037e967130a206ee203b081` | win | win |
| 1741 | **NL 100 / DU 8 / corr 56 / deg 7 / SAC 0.5** | **yes / yes** | **682** | `68a0d5e83ec41e799f80dfa5d535007c9062f2e0a27fd8b074433b23b6deb9f8` | win | win |

Per-seed artifact receipts:

- 1709: artifact `9856624220`, `sha256:4e072790196d6bb90597209882e67b16747e1f81096964c9d682a0d6931557e2`
- 1721: artifact `9856691925`, `sha256:3e9dc995ec2d628f1c7c284170cec5393a4ef7b00bfd165578ee2f8d190f4a3c`
- 1723: artifact `9856620105`, `sha256:9c3dd800db4c5845e81b643110cee7f4e6a49bfeb18c4fbfd8d081068a125156`
- 1733: artifact `9856753388`, `sha256:436ead7987209fb6dc6ae057a74b631a74f0ca323d3835df74cee270f15d16f9`
- 1741: artifact `9856755710`, `sha256:78dfd5f44fe7c1e8a68bdf41ff541a93ceda21171d717aad1645d1d019bffa70`

## Preregistered development checks

| Frozen prerequisite | Result |
|---|---|
| transfer hard-admissible >= 2/5 | **FAIL — 1/5** |
| transfer structural-target >= 2/5 | **FAIL — 1/5** |
| transfer admissible > continued GA admissible | PASS — 1 > 0 |
| transfer target > continued GA target | PASS — 1 > 0 |
| transfer wins vs GA > losses | PASS — 5 > 0 |
| median transfer NL >= 98 | PASS — 100 |
| median transfer DU <= 8 | **FAIL — 10** |
| median transfer max corr <= 60 | PASS — 56 |
| exact 1,620-evaluation budget on every arm | PASS |

Because the development rule required **all** prerequisites, the final verdict is `fresh_transfer_dev_fail`.

## Scientific interpretation

The Phase-1H proposal selector clearly transfers useful search pressure away from the historical warm-start: on all five fresh populations it reached NL 100 and max correlation 56, while the continued-GA comparator had medians NL 98 and correlation 60. It also produced one fresh hard-admissible candidate, demonstrating that the previously observed admissible region is reachable without seeding from the historical frontier.

The remaining reliability bottleneck is differential uniformity. Four of five transfer runs plateaued at DU 10 even after reaching NL 100 / corr 56. The next justified mechanism study should therefore target DU reduction specifically rather than relaxing this result, increasing the same budget post hoc, reusing the reserved confirmation seeds, or enabling neural fitness prematurely.

## Gate consequence

- Phase 1I confirmation: **not executed**
- Phase 1I confirmation seeds: **unused / quarantined**
- Global Gate 1: **RED**
- Neural oracle: **BLOCKED**
