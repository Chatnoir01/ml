# Phase 1H development result — plateau-directed cycle selection

## Status

**Development prerequisite PASSED.**

Phase 1H is a warm-start operator-mechanism experiment, not global Gate-1 evidence. The preregistered plateau-directed proposal selector repeatedly crossed the historical `NL=98` plateau and produced hard-admissible candidates under the frozen 600-evaluation budget.

Global Gate 1 remains **RED** and the neural-oracle phase remains **BLOCKED** until fresh-population matched evidence passes the separate Gate-1 criteria.

## Frozen provenance

- protocol commit: `95096df7172ebe992f335646d4de623d2444d9fa`
- frozen experimental SHA: `508e1537123ac763f0e7cef2793dbba46a5abbeb`
- development workflow run: `33523847410`
- Phase-0 CI on the frozen SHA: Python 3.10 / 3.11 / 3.12 all green
- development seeds: `1501, 1511, 1523, 1531, 1543`
- reserved confirmation seeds: `1601, 1607, 1609, 1613, 1619, 1621, 1627, 1637, 1657`

Every accepted result reproduced the historical warm start before execution:

- NL `98`
- DU `8`
- max linear correlation `60`
- algebraic degree `7`
- SAC `0.501708984375`
- fingerprint `d0260bcfbff19b1d43c1e2f41d923c6096d48ef0e3e4e1e78c088f81e02a1bcc`

## Frozen comparison

Each Phase-1H directed arm and the existing strict Phase-1E combined-cycle4 comparator received exactly `600` unique full classical evaluations per seed. Cheap local LAT/DDT proposal scoring was not counted as a full fitness evaluation; therefore the comparison is matched on full CryptoShield evaluations, not CPU time.

The comparator produced `0/5` structural targets and `0/5` hard-admissible candidates in every configuration and retained median `NL=98 / DU=8 / corr=60`.

## Development matrix

| Configuration | Hard-admissible | Structural target | Directed / comparator / ties | Median directed NL / DU / corr | Selected proposals lowering projected LAT-panel max |
|---|---:|---:|---:|---:|---:|
| `ties_p32` | 2/5 | 2/5 | 2 / 0 / 3 | 98 / 8 / 60 | 276 |
| `ties_p96` | **4/5** | **4/5** | **4 / 0 / 1** | **100 / 8 / 56** | **404** |
| `band_p32` | **4/5** | **4/5** | **4 / 0 / 1** | **100 / 8 / 56** | 21 |
| `band_p96` | **4/5** | **4/5** | **4 / 0 / 1** | **100 / 8 / 56** | 24 |

No proposal-pool shortfalls occurred and no duplicate full candidates were charged to the fitness budget.

## Frozen selection

The preregistered selection rule ties `ties_p96`, `band_p32`, and `band_p96` through criteria 1–8:

- 4/5 hard-admissible runs;
- 4/5 structural-target runs;
- +4 hard-admissible margin over comparator;
- +4 target margin over comparator;
- 4 directed wins, 0 comparator wins, 1 tie;
- median NL `100`;
- median DU `8`;
- median max correlation `56`.

Criterion 9 breaks the tie using the number of selected proposals whose local projection strictly lowers the current LAT-panel maximum:

- `ties_p96`: `404`
- `band_p96`: `24`
- `band_p32`: `21`

Therefore the frozen rule selects **`ties_p96`** for confirmation.

## Selected configuration per-seed evidence

`ties_p96` uses the exact-current-max LAT/DDT panels, proposal pool `96`, cycle length `4`, beam width `8`, and `600` full evaluations per arm.

- seed `1501`: directed `100 / 8 / 56 / degree 7 / SAC 0.5`; first hard-admissible at evaluation `240`; fingerprint `9585484c52192a1e65ee6ca99c4e768e1f29e7b55f709e20e376a8490381f466`.
- seed `1511`: directed `100 / 8 / 56 / degree 7 / SAC 0.5`; first hard-admissible at evaluation `299`; fingerprint `0abc96421f328f8a8c885f463b50da04f1dca5e35b0cf0a2ba5a0aa5ebe01ca6`.
- seed `1523`: no target; directed best `98 / 8 / 60 / degree 7 / SAC 0.5`; fingerprint `7c6994424c4e74b827ff541726ac3a023c77e3304e67bdfe2919e4ecfcdc5ae8`; outcome tie.
- seed `1531`: directed `100 / 8 / 56 / degree 7 / SAC 0.5`; first hard-admissible at evaluation `352`; fingerprint `170cb8356a3cf2d259da7ae37535cd1a1614c03a05596539e3a9f2154da00054`.
- seed `1543`: directed `100 / 8 / 56 / degree 7 / SAC 0.5`; first hard-admissible at evaluation `77`; fingerprint `4495c13476d491d7317800533ad447946fa918f05c09ab5c36be206337252c2b`.

## Artifact receipts

- `ties_p32`: artifact `9807244152`, `sha256:16dad088605d5650fd6ba37f7fcfa6fe9092c6c0a34a895a56b97a9c02def532`
- `ties_p96`: artifact `9807184190`, `sha256:281e542370acd876c77991427ff54a064338470d1935d2b8ca58db3bf9e09ef7`
- `band_p32`: artifact `9807327642`, `sha256:0bc3fd45efe0338b6144e4270c9afe33a96d98c3dacebd9bb07628dfa4e122e2`
- `band_p96`: artifact `9807309151`, `sha256:034763d7785584f02ae03e933985e6ffa9a064b0fbb02424fc5ae7cb538683f6`

Artifacts expire 2026-11-30.

## Scientific interpretation

The result strongly supports the specific mechanism hypothesis: the earlier plateau was not merely caused by strict acceptance or by the cycle-4 family itself. Selecting cycle-4 proposals by exact local LAT/DDT plateau effects materially changes the search trajectory and repeatedly yields `NL=100 / DU=8 / corr=56` hard-admissible candidates from the verified historical frontier.

This is still a **warm-start** result. It does not establish that fresh random populations can discover and exploit the same mechanism often enough to satisfy global Gate 1.

The next allowed step is a separately preregistered Phase-1H confirmation using only the reserved Phase-1H confirmation seeds and the frozen `ties_p96` configuration.
