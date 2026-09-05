# Phase 1N — joint DU / nonlinearity bridge development result

## Frozen verdict

`phase1n_dev_fail`

Phase 1N does **not** proceed to confirmation. The reserved confirmation seeds remain unused and quarantined. Global Gate 1 remains **RED** and the neural oracle remains **blocked**.

The experiment produced a strong but partial mechanism result. The joint DDT+Walsh-guided arm crossed the DU<=8 frontier on **3/5 development seeds**, versus **1/5** for the frozen Phase-1M hotspot-only ablation. Its median terminal best DU was **8 versus 10**, with **2 best-DU wins, 0 losses and 3 ties**. Across all five seeds, all **1,600** Arm-A proposals (320 per seed) were genuinely Walsh-guided and **0** used the hotspot-only fallback.

However, the preregistered primary target was not DU alone. It required terminal candidates satisfying the JOINT classical target:

- DU <= 8
- NL >= 100
- max |LAT| <= 64
- algebraic degree >= 6

Arm A produced **0** JOINT-target candidates, exactly the same as Arm B. It therefore failed both mandatory JOINT gates: aggregate JOINT count A > B and JOINT success on at least 2/5 seeds. The overall frozen verdict is `phase1n_dev_fail`.

## Frozen provenance

- Phase 1M base merged on `main`: `3960e2bbc5431b1f77333c1096327cfe66fc6626`
- Public preregistration issues: #43 through #47
- Phase 1N branch: `research/phase1n-du-nl-bridge`
- Seed registry commit: `c03a15d79445abd751bff8e17b4f225678cc2efe`
- Frozen protocol commit: `55a369a44a9abce3ad4c83fbc46e9265510255e1`
- Red-first contract commit: `90effceccd1d13bf25dcd374a133790922592f3a`
- Red evidence: Phase 0 CI run `33977035554` failed because `adversarial_sbox.phase1n` did not yet exist; historical Phase 1 benchmark run `33977035598` remained green
- Implementation commit: `703316aa78dfa7bfe3e6872c2c212ad789ba30ef`
- Locked workflow commit: `9bf65cd566a72116ae50b254a1d74b726a86aafe`
- Green engineering evidence on locked workflow commit: Phase 0 CI run `33977172687` passed Python 3.10, 3.11 and 3.12; Phase 1 benchmark run `33977172616` passed
- Full PR #48 diff inspected before scientific execution
- Frozen scientific SHA: `7b7744ec46a26b392579ddb4e083bbaafda300da`
- Scientific workflow run: `33977209924`
- Preflight: GREEN
- All five development seed jobs: GREEN
- Aggregate job: GREEN
- Aggregate artifact ID: `9972772580`
- Aggregate artifact digest: `sha256:bfe7fde6bf03af83cca6249967442d66c9a2aa53c6a498fc8a69b3bc83549e28`

Per-seed evidence artifacts:

| Seed | Artifact ID | ZIP SHA-256 | Scientific payload SHA-256 |
|---:|---:|---|---|
| 2309 | 9972769142 | `92890635c55c004afcf585bae438329009246bd7e8c10f445296b8fdc26924dc` | `afb690c225babc77f62e2eb7ce624a648628723f3a69ea7e1b25ea385bfd5115` |
| 2311 | 9972769133 | `3dcf8cfa761a8a77cf85af91fe475fcb315d903730066697f009e4e47d984d84` | `d1c0888da758516ff2882f48ce33b549fbd764d1e398bce4cd84c59602da5d56` |
| 2333 | 9972766259 | `42a85613872d9e9f4c92c303d69edce9da55461a910b86ddf4bebd5c40deb61e` | `a8bde0a5f3de11f78200799b01a27e3f566ad840bd4f804814d3382dbe65a8fc` |
| 2339 | 9972730280 | `862f4e4c724ade299a002e671149097122216cfed13909183835f95123022749` | `fbe0fbc02af6a87b79d2fe78654066ee684fbec4ccdff2335ebaa87686cadecf` |
| 2341 | 9972753699 | `87ea46e0b7ba97cc62f5aa562c0b258c4864df43d93addded06f18429bd62cb1` | `4ccf5c611913ad3f84bc6675cc681d3fd498bdeddd0fd1ce2b2a31eb019eac55` |

## Frozen design

Fresh development seeds:

`2309, 2311, 2333, 2339, 2341`

Reserved confirmation seeds remain unused:

`2401, 2411, 2417, 2423, 2437, 2441, 2447, 2459, 2467`

Three arms were compared from the same fresh initial population per seed:

1. Arm A — joint maximum-DDT-hotspot + worst-Walsh-guided one-swap proposals + staged ITO-aware Pareto/NSGA-II selection.
2. Arm B — frozen Phase-1M DDT-hotspot-only one-swap proposals + the same staged ITO-aware Pareto/NSGA-II selection.
3. Arm C — historical `feasibility_first` GA reference.

Every arm consumed exactly **340 unique full classical CryptoShield evaluations per seed**. Every inspected unique proposal was charged. ITO work was counted separately. Every seed was executed twice and required an identical canonical scientific payload.

Frozen hard constraints remained:

- nonlinearity >= 100;
- differential uniformity <= 8;
- max absolute linear correlation <= 64;
- algebraic degree >= 6;
- |SAC - 0.5| <= 0.05.

## Aggregate result

| Metric | Arm A: DDT+Walsh | Arm B: hotspot-only |
|---|---:|---:|
| JOINT-target terminal candidates | 0 | 0 |
| Seeds with JOINT-target candidate | 0/5 | 0/5 |
| Seeds with any terminal DU<=8 | **3/5** | 1/5 |
| Best-DU wins / losses / ties for A | **2 / 0 / 3** | — |
| Median terminal best DU | **8** | 10 |
| Median minimum ITO | **6.846200980392156** | 6.85453431372549 |
| Protected classical count (`NL>=100 ∧ max|LAT|<=64 ∧ degree>=6`) | 0 | 0 |
| Guided Arm-A proposals | **1600/1600** | — |
| Arm-A fallback proposals | **0** | — |

Frozen development checks:

| Check | Result |
|---|---|
| Aggregate JOINT count A > B | **FAIL** — 0 > 0 is false |
| Arm A has JOINT success on at least 2/5 seeds | **FAIL** — 0/5 |
| DU bridge non-regression | **PASS** — DU<=8 seed successes 3/5 vs 1/5; best-DU wins/losses 2/0 |
| Median best DU non-regression | **PASS** — 8 <= 10 |
| Classical protection A >= B | **PASS** — 0 >= 0 |
| ITO non-inferiority within +0.02 | **PASS** — 6.846200980392156 <= 6.85453431372549 + 0.02 |
| Exact 340 classical evaluations for every A/B/C run | **PASS** |
| Same initial population within each seed | **PASS** |
| Deterministic fixed-seed rerun | **PASS** |
| Fresh Phase-1N seed registry exact | **PASS** |
| Neural oracle blocked | **PASS** |

Because every preregistered condition was mandatory, the two failed JOINT conditions force the overall verdict to `phase1n_dev_fail`.

## Per-seed compact receipts

| Seed | Best DU A | Best DU B | DU<=8 A/B | JOINT A/B | Min ITO A | Min ITO B | Protected A/B |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2309 | 10 | 10 | 0 / 0 | 0 / 0 | 6.838112745098039 | 6.829779411764706 | 0 / 0 |
| 2311 | **8** | 10 | **1 / 0** | 0 / 0 | 6.857352941176471 | 6.869240196078431 | 0 / 0 |
| 2333 | **8** | **8** | 2 / 3 | 0 / 0 | 6.840563725490196 | 6.85453431372549 | 0 / 0 |
| 2339 | 10 | 10 | 0 / 0 | 0 / 0 | 6.858946078431373 | 6.862377450980392 | 0 / 0 |
| 2341 | **8** | 10 | **3 / 0** | 0 / 0 | 6.846200980392156 | 6.839705882352941 | 0 / 0 |

## What Phase 1N actually learned

Phase 1N gives stronger evidence than Phase 1M that directed proposal geometry can cross the DU=10 plateau under the frozen 340-evaluation budget. Phase 1M reached DU<=8 on only one of five fresh seeds. Phase 1N reached DU<=8 on three of five fresh seeds, and its median best DU moved from the comparator's 10 to 8 without losing a paired best-DU seed.

But the Walsh guidance did **not** raise the terminal vectorial nonlinearity threshold to 100. The best-feasibility Arm-A candidate on every development seed had NL=98. The six Arm-A terminal DU<=8 candidates observed across seeds 2311, 2333 and 2341 had NL values of 98 or 96, so none satisfied the frozen JOINT target.

This matters scientifically: the next bottleneck is no longer evidence that DU<=8 is unreachable. Under the Phase-1N mechanism it became reproducible enough to appear on a majority of fresh development seeds. The unresolved bottleneck is preserving or repairing **NL>=100 while holding DU<=8**.

A plausible mechanism hypothesis for a future separately preregistered phase is that reducing one currently worst Walsh coefficient is insufficient when several component/mask pairs share or rapidly exchange the maximum absolute coefficient. A future experiment should therefore test a **multi-hotspot Walsh plateau repair / lexicographic preservation mechanism** around DU<=8 candidates rather than simply adding more weight to a single Walsh coefficient. That is a follow-up hypothesis, not a Phase-1N result.

Accordingly:

- no Phase-1N confirmation is run;
- Phase-1N confirmation seeds remain quarantined;
- Phase-1N parameters are not tuned after observing these results;
- Global Gate 1 remains RED;
- the neural oracle remains blocked;
- any follow-up mechanism must use a newly preregistered phase and fresh development seeds.
