# Phase 1L — Fresh ITO-aware Pareto development result

## Frozen verdict

`phase1l_dev_fail`

Phase 1L does **not** proceed to confirmation. The reserved confirmation seeds remain unused and quarantined. Global Gate 1 remains **RED** and the neural oracle remains **blocked**.

The experiment nevertheless produced a clear secondary signal: the ITO-aware arm lowered the median minimum Improved Transparency Order from **6.857107843137255** in the neutral-ITO ablation to **6.8361519607843135**. That preregistered ITO criterion passed. The full Phase-1L gate failed because Pareto set coverage did not improve robustly and neither staged arm produced a hard-admissible or structural-target terminal candidate.

## Frozen provenance

- Phase 1K base merged on `main`: `5c6700e50b72fd1665485e0e8fe62aa8cbe6e732`
- Development protocol committed before scientific execution: `a344d51c0d3c774d2fc35c5171d7cad5377fb5f4`
- Red-first contract commit: `250122b56ef75b8a94e15ddca1928bbecf3f08a2`
- Red evidence: Phase 0 CI run `33948619373` failed before `phase1l.py` existed
- Implementation commit: `744e84db7a4c2c65106e534ad5c074a063e9259a`
- Green implementation evidence: Phase 0 CI run `33948702768` passed on Python 3.10, 3.11 and 3.12
- Frozen scientific SHA: `b766af168ece9e82dcae26bca0bb8ed178e5c231`
- Scientific workflow run: `33948768213`
- Preflight: GREEN
- All five development seed jobs: GREEN
- Aggregate job: GREEN
- Aggregate artifact ID: `9964176625`
- Aggregate artifact digest: `sha256:a072677ee1366a3b66b725fa8d6640d126070b15e1d654d792203f87c3efa9df`

Per-seed evidence artifacts:

| Seed | Artifact ID | SHA-256 |
|---:|---:|---|
| 1901 | 9964173532 | `5922db39c0c71b1c8f32222f93ebdbb2e848cdc661ed93efdf565599b49dc12c` |
| 1907 | 9964173145 | `78e53f77528e38457038336dd17414a44f7c759ff55a81c120ca6e8be6c60bfd` |
| 1913 | 9964172259 | `ed7b222fbe004ee4eaf4253185451993dd7917c2ed7dad76634d949c4ec26e01` |
| 1931 | 9964173809 | `08af6cc7d808c330cf408337173c604d27f29e8d280cc3458edca5409949b6ff` |
| 1933 | 9964174281 | `2aec26e7cb3b988110fc888f3db7d1c1f8a6128ec12030bbd30a879b3cc7021f` |

## Frozen design

Fresh development seeds:

`1901, 1907, 1913, 1931, 1933`

Reserved confirmation seeds remain unused:

`2003, 2011, 2017, 2027, 2029, 2039, 2053, 2063, 2069`

Three arms were compared from the same fresh initial population per seed:

1. Arm A — ITO-aware staged Pareto / NSGA-II.
2. Arm B — identical staged Pareto machinery with the ITO selection signal neutralized.
3. Arm C — historical `feasibility_first` GA.

Every arm consumed exactly **340 unique full classical CryptoShield evaluations per seed**. ITO work was reported separately because it is an experimental signal and adds wall-clock cost.

Frozen hard constraints remained:

- nonlinearity >= 100;
- differential uniformity <= 8;
- max absolute linear correlation <= 64;
- algebraic degree >= 6;
- |SAC - 0.5| <= 0.05.

The structural target excludes SAC and requires the first four conditions.

## Aggregate result

| Metric | Arm A: ITO-aware | Arm B: neutral-ITO ablation |
|---|---:|---:|
| Coverage wins | **1** | 1 loss for A |
| Coverage ties | **3** | — |
| Median directed coverage | **0.0** | **0.0** |
| Median minimum ITO | **6.8361519607843135** | 6.857107843137255 |
| Hard-admissible terminal candidates | 0 | 0 |
| Structural-target terminal candidates | 0 | 0 |

Frozen development checks:

| Check | Result |
|---|---|
| Arm A coverage wins > losses | **FAIL** — 1 win / 1 loss / 3 ties |
| Median C(A,B) > median C(B,A) | **FAIL** — 0.0 vs 0.0 |
| Median minimum ITO A < B | **PASS** |
| Hard-admissible count A >= B | **PASS** — 0 >= 0 |
| Structural-target count A >= B | **PASS** — 0 >= 0 |
| Exact 340 classical evaluations for every A/B/C run | **PASS** |
| Fresh seed registry exact | **PASS** |
| Neural oracle blocked | **PASS** |

Because every preregistered condition was required, the two coverage failures force the overall verdict to `phase1l_dev_fail`.

## Per-seed compact receipts

| Seed | C(A,B) | C(B,A) | Outcome | Min ITO A | Min ITO B | Hard A/B | Structural A/B |
|---:|---:|---:|---|---:|---:|---:|---:|
| 1901 | 0.0 | 0.0 | tie | 6.836642156862745 | 6.857107843137255 | 0 / 0 | 0 / 0 |
| 1907 | 0.0 | 0.25 | A loss | 6.832230392156863 | 6.8443627450980395 | 0 / 0 | 0 / 0 |
| 1913 | 0.0 | 0.0 | tie | 6.850122549019607 | 6.8665441176470585 | 0 / 0 | 0 / 0 |
| 1931 | 0.0 | 0.0 | tie | 6.8361519607843135 | 6.860661764705882 | 0 / 0 | 0 / 0 |
| 1933 | 1.0 | 0.0 | A win | 6.817156862745098 | 6.8561274509803924 | 0 / 0 | 0 / 0 |

## Interpretation

The Phase-1L result supports a narrow claim: **feeding ITO into selection pushed the terminal search toward lower ITO values under the frozen 340-classical-evaluation budget**. The median minimum ITO improved on the five fresh development seeds.

It does **not** support the stronger claim that ITO-aware selection produces a better overall six-objective Pareto frontier. Directed Pareto coverage was tied on three seeds, won once and lost once, so the preregistered coverage gate failed.

It also did not solve the dominant classical bottleneck: no terminal candidate in either staged arm reached the hard-admissible or structural target. Differential uniformity remained a recurring limiter around DU 10 in the best classical candidates.

Accordingly:

- no Phase-1L confirmation is run;
- confirmation seeds remain quarantined;
- Phase 1L parameters are not tuned after seeing these results;
- Global Gate 1 remains RED;
- the neural oracle remains blocked;
- any changed follow-up design must be registered as a new experiment with new development seeds before execution.
