# Phase 2E — artifact-only diagnosis of bounded-persistence failure modes

## Frozen status

- Machine status: `phase2e_artifact_diagnostics_valid`
- Scientific source SHA: `7f8250ed75721997e63a89faea0d9bf82a4044d4`
- Official workflow run: `34202069140`
- Official artifact ID: `10046212900`
- Artifact ZIP SHA-256: `4e4ad9c57679280030338a57a8c339211ca666851cfc7bc6c72b1564267044fa`
- Phase 2E payload SHA-256: `3a5504e1ab33e04f4b2da0e8b47c12ebd30bfc96a3cc784b0fa2f714ab75a37f`
- Frozen source: 36 exact Phase 2D arm receipts from run `34147455097`
- No neural training, scorer call, candidate regeneration, evolution replay, or held-out validation-artifact download occurred in Phase 2E.
- Forward and reverse traversal analyses were required to be byte-identical before the artifact was uploaded.

Phase 2E is descriptive/forensic only. It has no `supported`/`not_supported` efficacy verdict and does not alter the frozen Phase 2D result `phase2d_bounded_persistence_not_supported`.

## D1 — tag opportunity and utilization

### OP1

- Score-caused entrant occurrences: **62**
- Tags created: **62** — creation rate **100%**
- Active-tag appearances at the next corresponding stage: **62**
- Ordering changed by an active tag: **12/62 = 19.35%**
- Selected membership changed by an active tag: **6/62 = 9.68%**
- Active tags expiring without changing ordering or membership: **50/62 = 80.65%**

By stage, OP1 membership changes were 3/30 at shortlist and 3/32 at survival. The mechanism therefore usually created and carried the tag correctly, but most tags had no realized selection effect at the next allowed stage.

### SP1

- Score-caused entrant occurrences: **66**
- Tags created: **66** — creation rate **100%**
- Active-tag appearances: **66**
- Ordering changes: **6/66 = 9.09%**
- Membership changes: **3/66 = 4.55%**
- Expired without order/membership effect: **60/66 = 90.91%**

The persistence machinery itself was therefore active in both OP1 and SP1. OP1 produced more order and membership effects than the shuffled association, but utilization remained low in absolute terms.

## D2 — fate of score-caused entrants

Aggregate unique-fingerprint cell-sum descendant persistence:

| Arm | +1 descendant | +2 descendant | +5 descendant | terminal descendant |
|---|---:|---:|---:|---:|
| O0 | 16/56 = 28.57% | 9/56 = 16.07% | 4/56 = 7.14% | 4/56 = 7.14% |
| OP1 | 14/52 = 26.92% | 9/52 = 17.31% | 4/52 = 7.69% | 4/52 = 7.69% |
| SP1 | 9/59 = 15.25% | 4/59 = 6.78% | 2/59 = 3.39% | 2/59 = 3.39% |

OP1 shows higher descriptive persistence than SP1, but its +2 descendant rate is close to O0 (17.31% vs 16.07%). The artifact therefore does **not** show a large additional +2 transmission gain attributable to the one-generation OP1 persistence rule over the fresh O0 control.

Direct self-persistence was short lived: direct +5 was 0 for O0, OP1 and SP1, and terminal self ancestry was 0 for all three arms.

## D3 — classical replacement pressure

For score-caused entrant occurrences at the next corresponding stage:

| Arm | entrant occurrences | retained | better protected key | same key not selected | lineage absent | not reconstructible |
|---|---:|---:|---:|---:|---:|---:|
| O0 | 69 | 0 | 38 | 12 | 19 | 0 |
| OP1 | 62 | 6 | 30 | 6 | 20 | 0 |
| SP1 | 66 | 3 | 27 | 10 | 26 | 0 |

A large fraction of entrant loss was associated with a strictly better protected classical key or with the lineage no longer being present. The protected classical rule was therefore a major observed constraint on persistence. This classification does not use neural score to redefine the protected comparison.

For active OP1 tags specifically, 6 occurrences were retained; the remaining loss classifications were 20 lineage absent, 6 same-key not selected, 8 behind a stricter protected boundary, and 22 not reconstructible from the fields available at that exact active-tag event. These unknowns remain explicitly unknown rather than being reassigned to a favorable mechanism explanation.

## D4 — budget closure geometry

Across all nine seeds:

| Arm | boundary opportunities | pre-closure | scored | scored fraction | post-closure observational-only |
|---|---:|---:|---:|---:|---:|
| C | 365 | 47 | 38 | 10.41% | 318 |
| O0 | 364 | 47 | 38 | 10.44% | 317 |
| OP1 | 364 | 47 | 38 | 10.44% | 317 |
| SP1 | 364 | 46 | 37 | 10.16% | 318 |

Only about one tenth of recorded boundary opportunities were scored before budget closure. This identifies score-budget closure as an important part of the observed geometry, but Phase 2E **does not** authorize or claim that a larger future budget would improve efficacy.

## D5 — OP1 versus SP1 specificity

The real-score OP1 association was descriptively more active than shuffled SP1 on several mechanism metrics:

- membership utilization: **9.68% OP1 vs 4.55% SP1**;
- order utilization: **19.35% vs 9.09%**;
- +2 descendant persistence: **17.31% vs 6.78%**;
- terminal descendant ancestry: **7.69% vs 3.39%**;
- entrant retention: **6/62 vs 3/66**.

This is evidence that real versus shuffled score association did not behave identically inside the bounded persistence machinery. It is **not** an efficacy result and does not rescue Phase 2D: OP1 remained close to O0 on the preregistered +2 transmission quantity and Phase 2D's held-out support gates remain negative.

## D6 — matched per-seed table

The frozen nine-seed C/O0/OP1/SP1 table, including exact source receipt SHA-256 values, is committed separately in `research/PHASE2E_D6.md`. The official workflow artifact retains the full machine D6 payload.

## Narrow interpretation

The artifact supports a limited mechanism diagnosis: tag creation was not the main failure point; **realized tag utilization was rare**, many entrants were removed by protected classical pressure or vanished from the lineage, and the score budget closed while most later boundary opportunities were observational-only. OP1 also showed some real-vs-shuffled specificity, but the one-generation rule did not create a large aggregate +2 transmission increase over O0.

No conclusion is authorized about longer persistence, a larger neural budget, adaptive retraining, bidirectional GA↔NN, AES, deployed ciphers, or operational key recovery. Any next mechanism requires a separate preregistration after this diagnostic result is frozen.
