# Phase 2H-FORK2 — Native B1 score transplant at the first adaptive fork (2026-11-07)

**Exploratory, exact retrospective operator counterfactual. NO model training, NO GA evolution rerun, NO held-out H access, NO Phase2I launch or Phase2U unseal.** Phase2G verdict stays `phase2g_adaptive_coevolution_not_supported`.

## Preregistered boundary

The replay intervention and full-denominator counting rules were recorded BEFORE new calculations in `research/PHASE2H_FORK2_B1_SCORE_SWAP_REPLAY_PROTOCOL_20261107.md`, commit **`8956b97643c30fcaf07b8dc6dc59f47c4346934e`**.

Source: **18 unchanged original A/F arm ZIPs** from Phase2G original GitHub run [35572084785](https://github.com/Chatnoir01/ml/actions/runs/35572084785), nine original evolution seeds `726011,726023,726037,726049,726061,726073,726087,726099,726113`, 40 original selection events per arm/seed. All 18 ZIP sources are compared **byte-for-byte** against the independently pinned H3 preservation ZIP, SHA256 **`eef47515ed4897688c2b28ec03bd2466dedaa6862f0604db1b7048dbc2911374`**; every source native `scientific_payload_sha256` and ZIP CRC checked. No direct import of September NN weights is possible: they were not archived.

## Exactly identified fixed-context intervention

When A/F have identical `selected_before` and B1 group sets, equal cutoff/classical/reference identities, and the original scores cover every eligible B1 candidate, the exact historical frozen B1 policy chooses `k = |selected_before ∩ B1|` candidates having the smallest score. Native selections were reconstructed **101/101 A** and **101/101 F** with no discrepancies and **zero ambiguous boundary ties**.

Then **ONLY** exchange the scores indexed by the same candidate fingerprints, leaving the candidate pool, classical keys, cutoff, B1 group and `k` fixed. The transplanted scores reconstruct **exactly** the *opposite* native selection in **all 101 comparable scored events**.

| Complete original A/F stage-pair denominator | Events |
| --- | ---: |
| All original events, 9 seeds × 20 generations × 2 stages | 360 |
| Identical A/F preselected and B1 candidate sets | 102 |
| Fully scored, strictly cuttable B1 events | **101** |
| Unavailable / noncomparable, never counted as equal | 259 |
| Changed membership under swap of **only** A/F score maps | **12** |
| Candidate membership exchanges summed over 12 pairs | **38 per arm** |
| Comparable scored events before generation 5 | 89 |
| Changed membership before generation 5 | **0** |
| Comparable scored events starting generation 5 | 12 |
| Changed membership after generation 5 | **12** |
| First generation-5 shortlist events with changed selection | **9/9** |
| Exclusive first-fork candidates in those 9 events | **31 per arm** |

First generation-5 shortlist A-only vs F-only exchanges, by original seed:

| Seed | Candidate exchanges per arm | B1 candidates | B1 kept |
| ---: | ---: | ---: | ---: |
| 726011 | 2 | 20 | 8 |
| 726023 | 5 | 20 | 8 |
| 726037 | 2 | 15 | 3 |
| 726049 | 5 | 20 | 8 |
| 726061 | 3 | 20 | 8 |
| 726073 | 2 | 15 | 3 |
| 726087 | 5 | 20 | 8 |
| 726099 | 2 | 15 | 8 |
| 726113 | 5 | 19 | 7 |
| **TOTAL** | **31** | — | — |

The **12 membership-changing events** consist of these nine first-fork shortlists (31 exchanges) and three later directly comparable stages (7 exchanges). Later A/F candidate populations generally differ; they are unidentifiable as a controlled model-only contrast.

## Two source-independent implementations and corruption controls

An independent verifier reopens all 18 original ZIP bytes, recomputes their canonical original SHA receipts, reconstructs `top-k` source membership **without importing the primary implementation**, and revalidates all 360 denominator classifications and 101 candidate-set transplant identities. Independent totals: **360/102/101/12/38**, **0/89** membership changes before generation 5. Ten fail-closed negative controls passed: missing score, NaN, boundary tie, unmatched preselection, wrong cutoff, unmatched B1, forged selected-after, mismatched classical metric, injected candidate score, tampered scientific payload SHA.

Reproducible original-source ZIP bundle (conversation attachment): **`phase2h_fork2_original_score_swap_verified_20261107.zip`**, **3,653,976 bytes**, SHA256 **`ac55e1f2d3492267c7a5c7bda45aab307bfd5b4eee66cf500694f05afa0d9aae`**. Includes nested preserved 18-source ZIP, an extractor, primary script, independent second verifier, ten negative controls, detailed 360-row JSON, source-bound report, README and SHA256SUMS. On a **clean extracted directory**, running all four commands reproduces both JSON files **byte-for-byte** and passes all 10 tests.

- Canonical primary result SHA (without digest field): `e8698472cb0839ab5c5c29fac1b62cc8d69c88fadc627bcd5ad94c212613d4cc`
- Primary JSON disk SHA: `12a14e44c92555da0d6941bbd82a20306ffad8b09261715b84f8e81200b6ae52`
- Independent JSON disk SHA: `e67707390650b42704e3e3cd1e791f3d2f42ce9cb75cf28b188be23c50f4651f`

## Scope: local counterfactual, not terminal causal treatment

This result establishes the **immediate deterministic selection operator** influence on **fixed original B1 inputs**. It cannot show that curriculum replacement caused the historical A–F terminal held-out performance gap: neither September NN weights nor matched later GA states are available, and proposal-parent RNG paths diverge after the first fork. In Phase2H H3, eight of the nine first-fork exclusive candidate groups have equal four-coordinate classical tuple distributions, the ninth (726113) is A-classically worse. This is not a demonstrated H3 causal penalty, H2 cycling, H1 forgetting, H4 mechanism support, or deployed-cipher improvement.

**Phase2I firewall remains active:** `phase2i_gate.py` authorizes one preregistered intervention family *only* after a frozen Phase2H result supports exactly one mechanism. No "rescue sweep" or new prospective training was run; final Phase2G negative verdict and sealed Phase2U 96 fits remain untouched. Stacked DRAFT PR, do not merge to main without CI/scientific review.
