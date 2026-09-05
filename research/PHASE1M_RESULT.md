# Phase 1M — DU-hotspot bridge development result

## Frozen verdict

`phase1m_dev_fail`

Phase 1M does **not** proceed to confirmation. The reserved confirmation seeds remain unused and quarantined. Global Gate 1 remains **RED** and the neural oracle remains **blocked**.

The experiment produced one narrow positive signal: the DU-hotspot arm reached a terminal **DU = 8** candidate on seed **2131**, while the ordinary-swap ablation reached no DU<=8 candidate on any development seed. Across all five seeds Arm A therefore had **1 best-DU win, 0 losses and 4 ties**, with aggregate DU<=8 count **1 vs 0**.

That was not sufficient for the preregistered reproducibility requirement. The frozen gate required Arm A to reach at least one terminal DU<=8 candidate on **at least 3/5 seeds**; it succeeded on only **1/5**. Median terminal best DU remained **10 vs 10**. Therefore the overall verdict is `phase1m_dev_fail`.

## Frozen provenance

- Phase 1L base merged on `main`: `f8954bf2a19c7314504a84a762dc1e21b7739d9e`
- Public preregistration issues: #27 through #41, with exact budget freeze in #38
- Phase 1M branch: `research/phase1m-du-hotspot-bridge`
- Seed registry commit: `3662ff64af1e28f5e9b3928aac89b395bdf4fd0d`
- Frozen protocol commit: `7cca08c01112c8b2016ad2653180a83174010bd8`
- Red-first contract commit: `4bc93959a5635dccfb70aec0ef431d20554cdaee`
- Strengthened red contract commit: `c4d3b73e082a1ded8e8812b7cb93809ffee7e017`
- Red evidence: Phase 0 CI run `33966711545` failed before `phase1m.py` existed; historical Phase 1 benchmark run `33966711504` remained green
- Implementation commit: `01abac525cad1109e77417ca7607b390de2057b6`
- Locked workflow commit: `fb465f9850f3b7206d184bbb15e88f1b1d2517f4`
- Green engineering evidence on locked workflow commit: Phase 0 CI run `33966894353` passed Python 3.10, 3.11 and 3.12; Phase 1 benchmark run `33966894348` passed
- Full PR #42 diff inspected before scientific execution
- Frozen scientific SHA: `bbf40afc8d25f754f2db465c12da16ce0dff9527`
- Scientific workflow run: `33966950797`
- Preflight: GREEN
- All five development seed jobs: GREEN
- Aggregate job: GREEN
- Aggregate artifact ID: `9969878651`
- Aggregate artifact digest: `sha256:5886dcad80935d725f2a518f2dda899f6ef5cd3d118f0e09129541ed0e4a5295`

Per-seed evidence artifacts:

| Seed | Artifact ID | ZIP SHA-256 | Scientific payload SHA-256 |
|---:|---:|---|---|
| 2111 | 9969806920 | `3ddc7beb86aa702f0c887de23c88cd9af4ab2a9693495193be5f28122cc627a1` | `464a97156a97a38580c9590fddd175fecc37feaa51399a02f12775ac3e86ec19` |
| 2113 | 9969831019 | `43e678223aa727ac21e69d8dc8597218cdd2952f87281ec02f6e8a80e8bd9cbd` | `dd9508eb452fe94dbbb94c99799c97c830fc6e5e0921c09525991b16e4dd2437` |
| 2129 | 9969827753 | `47df5e9ffa923b79e1bf1bfaec075dcdc7d1059886369047ee595117f7018005` | `02759c0a2e82446c5a3747b6e2a105bfda52521e8de3a3707a2df2e5f741b1bf` |
| 2131 | 9969835084 | `7cc23e0d1c856377042c71b13632a2f7a704737e0568c82469dd25f3a12bd035` | `0d760bba189f75b8fa529386432f049583aebd7591626cc86c6ec690d2870f44` |
| 2137 | 9969835770 | `13b786b518f1b3b9cb2940742e7bd60153e571b96272579adb4912f7c7e6abac` | `b8c54999ecb680f1236aed377b6739c7c54fca76ee1f17fe2dff12a36f7c88ec` |

## Frozen design

Fresh development seeds:

`2111, 2113, 2129, 2131, 2137`

Reserved confirmation seeds remain unused:

`2203, 2207, 2213, 2221, 2237, 2239, 2243, 2251, 2267`

Three arms were compared from the same fresh initial population per seed:

1. Arm A — DDT maximum-cell DU-hotspot-directed swap proposals + staged ITO-aware Pareto/NSGA-II selection.
2. Arm B — ordinary random one-swap proposals + the same staged ITO-aware Pareto/NSGA-II selection.
3. Arm C — historical `feasibility_first` GA reference.

Every arm consumed exactly **340 unique full classical CryptoShield evaluations per seed**. Every inspected unique hotspot proposal was charged to Arm A's classical ledger. ITO work was counted separately. Each Phase-1M seed was executed twice and required an identical canonical scientific payload.

Frozen hard constraints remained:

- nonlinearity >= 100;
- differential uniformity <= 8;
- max absolute linear correlation <= 64;
- algebraic degree >= 6;
- |SAC - 0.5| <= 0.05.

The structural target excludes SAC and requires the first four conditions.

## Aggregate result

| Metric | Arm A: DU-hotspot | Arm B: ordinary swap |
|---|---:|---:|
| Terminal DU<=8 candidates | **1** | 0 |
| Seeds with a terminal DU<=8 candidate | **1/5** | 0/5 |
| Best-DU wins / losses / ties for A | **1 / 0 / 4** | — |
| Median terminal best DU | **10** | **10** |
| Median minimum ITO | 6.850245098039216 | **6.840196078431372** |
| Protected classical count (`NL>=100 ∧ max|LAT|<=64 ∧ degree>=6`) | 0 | 0 |

Frozen development checks:

| Check | Result |
|---|---|
| Aggregate DU<=8 count A > B | **PASS** — 1 > 0 |
| Arm A has DU<=8 success on at least 3/5 seeds | **FAIL** — 1/5 |
| Best-DU robustness | **PASS** — medians tie at 10, but A has 1 win / 0 losses / 4 ties |
| Classical protection A >= B | **PASS** — 0 >= 0 |
| ITO non-inferiority within +0.02 | **PASS** — 6.850245098039216 <= 6.840196078431372 + 0.02 |
| Exact 340 classical evaluations for every A/B/C run | **PASS** |
| Same initial population within each seed | **PASS** |
| Deterministic fixed-seed rerun | **PASS** |
| Fresh Phase-1M seed registry exact | **PASS** |
| Neural oracle blocked | **PASS** |

Because every preregistered condition was required, the single failed reproducibility condition forces the overall verdict to `phase1m_dev_fail`.

## Per-seed compact receipts

| Seed | Best DU A | Best DU B | DU<=8 A/B | Min ITO A | Min ITO B | Protected A/B |
|---:|---:|---:|---:|---:|---:|---:|
| 2111 | 10 | 10 | 0 / 0 | 6.842401960784313 | 6.8457107843137255 | 0 / 0 |
| 2113 | 10 | 10 | 0 / 0 | 6.855637254901961 | 6.825367647058823 | 0 / 0 |
| 2129 | 10 | 10 | 0 / 0 | 6.846200980392156 | 6.8383578431372545 | 0 / 0 |
| 2131 | **8** | 10 | **1 / 0** | 6.850245098039216 | 6.840196078431372 | 0 / 0 |
| 2137 | 10 | 10 | 0 / 0 | 6.8617647058823525 | 6.856004901960784 | 0 / 0 |

## Seed 2131 DU=8 candidate

Arm A's sole DU<=8 terminal candidate has fingerprint:

`3da7a51a6ddcd8f56dd725b55f0142d188a564770c57ea7c98a972f3b3cf1dc5`

Metrics:

- differential uniformity: **8**
- nonlinearity: **98**
- max absolute linear correlation: **60**
- algebraic degree: **7**
- SAC: **0.5**
- Improved Transparency Order: **6.850245098039216**

This candidate crosses the targeted DU frontier while keeping the LAT, degree and SAC gates, but it misses the frozen nonlinearity requirement `NL >= 100`. Therefore it is neither a protected-classical terminal candidate under the Phase-1M definition nor hard-admissible/structural-target evidence.

## Interpretation

Phase 1M supports a narrow mechanism observation: **under the frozen 340-evaluation matched budget, the DDT-hotspot proposal mechanism produced one DU<=8 terminal event where the ordinary-swap ablation produced none, and it never lost the per-seed best-DU comparison**.

It does **not** support the stronger claim that the mechanism reliably crosses the DU<=8 frontier. Four of five seeds remained at DU=10, and the preregistered 3/5 reproducibility threshold failed.

The seed-2131 result also exposes the next joint bottleneck more precisely: when the mechanism did reach DU=8, the candidate's nonlinearity was 98 rather than the required >=100. Thus the next experiment, if pursued, should be registered as a new phase and test a mechanism for preserving or repairing nonlinearity while retaining DU<=8. Phase 1M itself must not be retuned after observing this result.

The ITO non-inferiority guard passed, but Arm A's median minimum ITO was slightly higher/worse than Arm B by about 0.01005. This is within the preregistered +0.02 tolerance and should not be described as an ITO improvement.

Accordingly:

- no Phase-1M confirmation is run;
- Phase-1M confirmation seeds remain quarantined;
- Phase-1M parameters are not tuned after seeing these results;
- Global Gate 1 remains RED;
- the neural oracle remains blocked;
- any follow-up mechanism must use a newly preregistered phase and fresh development seeds.
