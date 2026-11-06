# Phase 2H — Original A/F matched-context rank transitions (2026-11-07)

**Pre-locked exploratory, noncausal, original-receipt-only analysis. No neural training or Phase2U.** The [analysis plan](PHASE2H_AF_MATCHED_RANK_TRANSITIONS_PROTOCOL_20261107.md) was committed at `8b9eac10bbe6fe9edaae8117c38b36588acbdde8` **BEFORE** computing these ranks.

## Original immutable evidence

18 unmodified A/F original Phase 2G archival arm ZIPs, official run [35572084785](https://github.com/Chatnoir01/ml/actions/runs/35572084785), source marker `030652489dd489a4705bbf64a12d7e6fa01ca03b`, frozen parent `ba1aec133c50ddac246a54a70bb3ff2f0994df3a`. All ZIP CRC and all **18/18** canonical source `scientific_payload_sha256` values independently checked. The existing 18-ZIP source evidence archive SHA256 is `eef47515ed4897688c2b28ec03bd2466dedaa6862f0604db1b7048dbc2911374`.

Nine original evolution seeds × 20 generations × 2 stages = **360 A/F pairs**. Exact comparability requires identical **selected-before** and **B1 group** *sets* in A and F: only **102/360** meet this gate. **101/102** have two or more original fully scored B1 candidates under both arms; **23,313** actual candidate pairs are comparable on their original neural-score ordering. Unequal-context future events must not be treated as a model-only controlled contrast.

## Independently rechecked candidate-pair ranking result

| Phase2G generation block | Paired stages | Same A/F context | Fully-scored comparable | Candidate pairs | Strict score-rank reversals |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0–4 | 90 | 90 | 89 | 21,515 | **0** |
| 5–9 | 90 | 12 | 12 | 1,798 | **653** |
| 10–14 | 90 | 0 | 0 | 0 | **NOT MEASURABLE** |
| 15–19 | 90 | 0 | 0 | 0 | **NOT MEASURABLE** |
| **Total** | **360** | **102** | **101** | **23,313** | **653** |

There are additionally **22,657 strictly same-direction candidate pairs**, **3** tied in both arms, and **0** one-arm-only tie transitions. All **653** strict inversions are contained in **12** matched/scored events starting at generation 5. At generation-5 **shortlist** alone, the nine source-paired events contain **522** strict inversions across 1,436 candidate pairs; all nine have different `selected_after` sets.

| Original evolution seed | Generation-5 shortlist strict reversals | Candidate pairs |
| ---: | ---: | ---: |
| 726011 | 32 | 190 |
| 726023 | 90 | 190 |
| 726037 | 20 | 105 |
| 726049 | 88 | 190 |
| 726061 | 62 | 190 |
| 726073 | 29 | 105 |
| 726087 | 71 | 190 |
| 726099 | 32 | 105 |
| 726113 | 98 | 171 |
| **Total** | **522** | **1,436** |

Earliest matched-context **rank reversal AND member-selection divergence** is `generation 5 / shortlist` on **9/9** historical seeds. There are **0** strict rank inversions and **0** membership differences in the **90/90** stage comparisons over the first five generations, **including four seeds with differing actual initial 16-state NN SHA receipts**.

## Mechanistic interpretation boundary

These original scores establish *rank-order reconfiguration on identical candidate sets* at the first adaptive-curriculum checkpoint. It is stronger evidence than curriculum Jaccard drift or model-state hash divergence alone, and focuses the subsequent **separately preregistered causal intervention** on rank stability and selection geometry. This does NOT prove the adaptive curriculum *caused* the final heldout inferiority, neural forgetting, cyclic chasing, a BLAS cause, or security of a deployed cipher; post-generation-5 evolutionary context paths rapidly diverge and cannot be compared as controlled model-only conditions.

## Independent verification and reproducibility

- Full **360-event** result JSON canonical SHA-256 `41fbae7a5566fd60c6e07e59708ba2e957de748b44f003ce61c28925f86705a2`.
- Independent verifier reads source ZIPs afresh, recalculates canonical original payload SHA values and all **101 eligible event pair matrices**; verifies **23,313** pair comparisons, **653** strict inversions, **522** first generation-5 shortlist inversions, and **0** before generation 5. Independent verification SHA-256 `826c5e20aaf280bc5c255289ed3e72d0b888606b9928d891b816fa86fab95b08`.
- Complete user-downloaded source package: `phase2h_af_matched_rank_verified_evidence_20261107.zip` **3,498,274 bytes**, SHA-256 `64c51b80b21b14345585943f7b6a62d654cc8a5c0921ba6efb90982b69d20722`. It includes the prior complete original 18-source archive as unchanged nested ZIP, primary executable script, JSON, independent verifier + verification JSON, full report and SHA256SUMS. User-owned externally durable backup not attested.
- Separate engineering repair on this PR updates the real H3 producer-schema reader (`exited` and `max_abs_lat`) and replaces arm-tagged training-receipt comparisons with 16 actual trained-state SHA digests. Synthetic negative tests and GitHub archival parity workflow were added. **Do not report their CI as passed until exact-head run is completed and independently checked.**

**Preserve** frozen Phase2G negative verdict `phase2g_adaptive_coevolution_not_supported`, Phase2U 96 sealed neural fittings, DRAFT status, no main merge.
