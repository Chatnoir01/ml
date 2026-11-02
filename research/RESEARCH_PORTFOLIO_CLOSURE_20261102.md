# Research portfolio closure register — 2 November 2026

**Status: BASELINED INVENTORY, NOT EXPERIMENTAL CLOSURE. NO MERGE, REBASE, DELETE, DEPLOY OR TEST SUPPRESSION AUTHORIZED.**

Source of snapshot: GitHub open pull requests for `Chatnoir01/ml` inspected on 2026-11-02. **38 draft PRs** were open before the creation of the *new* registry PR. They represent **15** distinct research/engineering workstreams, many stacked; this registry does **not** claim there are 38 independent experiments. Later PRs must be added in a new dated snapshot, preserving this snapshot unchanged.

The machine-readable source of truth is [the frozen PR manifest](RESEARCH_PORTFOLIO_CLOSURE_MANIFEST_20261102.json). The standard-library validator `scripts/validate_research_portfolio_closure.py` and 18 synthetic tamper unit tests prevent silent omission, double allocation, wrong dependency and false promotion of unresolved scientific/security gates. A passing registry CI means **the snapshot is internally consistent**, not that its science has been independently replicated.

## 1. Completion semantics

- **Scientific closed:** preregistered protocol executed, raw original outputs preserved, independent checks done, result accepted *positive, negative, or inconclusive*. Do not rerun a frozen negative until it becomes positive.
- **Engineering closed:** precise code/ABI/model state, versions, CI and regression traces exist, including proper fail-closed negative tests. Green CI does NOT establish attack resistance.
- **Security closed:** authenticated threat model, actual trust boundary, hostile tests, persistence, key life cycle, and external review suitable for its intended deployment. Research toy models typically do **not** qualify.
- **Administrative closed:** original PR's evidence and dependencies are accounted for, a disposition is reviewed and recorded. Draft status is preserved until explicit decision; no automated merging or deletion.

## 2. Snapshot and priorities

| Workstream | Priority | Baseline status | PRs |
|---|---|---|---|
| `phase1_sbox_search` | P2 | Frozen result; old draft disposition open | [#25](https://github.com/Chatnoir01/ml/pull/25), [#26](https://github.com/Chatnoir01/ml/pull/26) |
| `phase2_replication` | P2 | Frozen result; old draft disposition open | [#81](https://github.com/Chatnoir01/ml/pull/81) |
| `phase2_adaptive_repro` | P0 | Blocked on reproducibility | [#120](https://github.com/Chatnoir01/ml/pull/120), [#121](https://github.com/Chatnoir01/ml/pull/121), [#123](https://github.com/Chatnoir01/ml/pull/123), [#124](https://github.com/Chatnoir01/ml/pull/124), [#125](https://github.com/Chatnoir01/ml/pull/125), [#126](https://github.com/Chatnoir01/ml/pull/126), [#127](https://github.com/Chatnoir01/ml/pull/127), [#129](https://github.com/Chatnoir01/ml/pull/129), [#131](https://github.com/Chatnoir01/ml/pull/131), [#152](https://github.com/Chatnoir01/ml/pull/152) |
| `phase2s_mechanisms` | P1 | Exploratory; prospective confirmation open | [#156](https://github.com/Chatnoir01/ml/pull/156) |
| `phase2t_original_blocked` | P2 | Frozen blocked source protocol | [#157](https://github.com/Chatnoir01/ml/pull/157) |
| `phase2u_prospective` | P0 | Source panel complete; predictions not frozen | [#158](https://github.com/Chatnoir01/ml/pull/158) |
| `tpm_security_attack` | P1 | Frozen result; old draft disposition open | [#143](https://github.com/Chatnoir01/ml/pull/143), [#144](https://github.com/Chatnoir01/ml/pull/144), [#145](https://github.com/Chatnoir01/ml/pull/145), [#146](https://github.com/Chatnoir01/ml/pull/146), [#147](https://github.com/Chatnoir01/ml/pull/147), [#148](https://github.com/Chatnoir01/ml/pull/148), [#149](https://github.com/Chatnoir01/ml/pull/149), [#150](https://github.com/Chatnoir01/ml/pull/150), [#151](https://github.com/Chatnoir01/ml/pull/151) |
| `raven_continuity` | P1 | Model-level results; durable protocol open | [#155](https://github.com/Chatnoir01/ml/pull/155) |
| `secure_core` | P0 | Security CI failed | [#122](https://github.com/Chatnoir01/ml/pull/122), [#132](https://github.com/Chatnoir01/ml/pull/132), [#133](https://github.com/Chatnoir01/ml/pull/133), [#153](https://github.com/Chatnoir01/ml/pull/153), [#154](https://github.com/Chatnoir01/ml/pull/154) |
| `cryptowall_envelope` | P1 | Prototype CI green; security validation open | [#136](https://github.com/Chatnoir01/ml/pull/136) |
| `cryptowall_hybrid` | P1 | Prototype CI green; security validation open | [#139](https://github.com/Chatnoir01/ml/pull/139) |
| `fhe_bfv` | P2 | Original demonstrator scope complete | [#140](https://github.com/Chatnoir01/ml/pull/140) |
| `bb84_simulation` | P2 | Original demonstrator scope complete | [#141](https://github.com/Chatnoir01/ml/pull/141) |
| `neural_crypto_lab` | P1 | Smoke only; full experiment open | [#138](https://github.com/Chatnoir01/ml/pull/138) |
| `ci_infrastructure` | P1 | Research CI / evidence archiving pending | [#134](https://github.com/Chatnoir01/ml/pull/134), [#135](https://github.com/Chatnoir01/ml/pull/135) |

**Blocking research priority P0**: (1) independent neural provenance diagnosis Phase 2H/2R; (2) Phase 2U's source-bound classical prediction receipt followed by a *separate* blinded prospective neural study; (3) the five failed Secure Core hardware-boundary CI tests. These are not interchangeable. The Phase 2G adaptive failure is valid and frozen even while its mechanistic explanation remains open.

**Secondary P1**: Phase 2S causal controls; TPM raw receipt retention and PR disposition; RAVEN durable witness memory/epoch safety; CryptoWall protocol review and hybrid interop; full Alice/Bob/Eve run; evidence/CI hygiene.

**Narrow P2 terminal scope**: preserve Phase 1O and Phase 2A frozen results, close the original failed Phase 2T-v1 source-generation study as *blocked*, and preserve BFV/BB84 as demonstrators rather than unsupported production claims.

## 3. Concrete closure gates for every original workstream

### Recherche classique S-Box Phase 1 — P2

**Verified:** Phase 1O classical objective confirmed on reserved seeds; old Phase 1L/1M PRs remain drafts.

**Still unproven:** Legacy experimental branch disposition, historical artifact preservation and direct comparison beyond the original target.

**Evidence anchors:** research/PHASE1O_CONFIRM_RESULT.md (main); Phase 1O confirmation held-out, 340 classical evaluations/seed.

**Next experiments / actions:**
- [ ] Inventory Phase 1L and 1M negative/partial findings and attach their frozen result files.
- [ ] Classify legacy PRs as superseded research without deleting raw evidence.
- [ ] Do not insert evolutionary S-Boxes into any production cipher.

**Exit criteria:**
- [ ] Frozen reports and exact source refs catalogued
- [ ] Legacy draft dispositions recorded
- [ ] No production-security claim

**Prerequisites:** none within this portfolio.

### Réplication neuronale Phase 2A et Oracle U2 — P2

**Verified:** Depth-four S-Box heterogeneity replicated in the frozen ToySPN; U2 qualified one pinned neural oracle, not interchangeable architectures.

**Still unproven:** Broader cipher/key/representation generalization and disposition of legacy Phase 2A-U draft.

**Evidence anchors:** research/PHASE2AT_RESULT.md (main); research/PHASE2AU2_RESULT.md (main).

**Next experiments / actions:**
- [ ] Preserve frozen artifacts and exact null hypotheses.
- [ ] Document where model-specific qualification stops and what Phase 2S/2U may reuse.
- [ ] Record legacy PR disposition independently of prospective Phase 2U.

**Exit criteria:**
- [ ] Historical results indexed immutable
- [ ] No claim of universal neural oracle
- [ ] Open legacy PR disposition chosen

**Prerequisites:** `phase1_sbox_search`.

### Adaptive GA↔NN Phase 2G–2R and initialization anomaly — P0

**Verified:** The adaptive superiority claim FAILED in frozen Phase 2G (2,880 trainings); Phase 2R synthetic input-preflight tests passed.

**Still unproven:** Resolve reported 4/9 A/F initial model-state mismatches, independently replay same model/data state on actual runner and train with pinned inputs. H1 forgetting matrix lacks required frozen evidence.

**Evidence anchors:** research/PHASE2G_RESULT.md on research/phase2g-adaptive-coevolution; PR #152 preflight CI success.

**Next experiments / actions:**
- [ ] Preserve negative Phase 2G result untouched.
- [ ] Freeze actual checkpoint-zero state bytes and provenance for matching A/F arms.
- [ ] Replay identical dataset/model-seed/initial-state in real runner; compare hashes before new training.
- [ ] If provenance cannot be recovered, publish a bounded inconclusive diagnosis and create independent new preregistration.

**Exit criteria:**
- [ ] Full reproducibility gate on actual runner passes OR explicit unable-to-reproduce verdict
- [ ] No retrospective reinterpretation of frozen 2G failure
- [ ] H1 missing-data condition documented

**Prerequisites:** `phase2_replication`.

### Mechanistic one-bit, rotation, keys and features Phase 2S — P1

**Verified:** Retrospective, six-S-Box classical one-bit and rotation/key exploratory signals; PR Phase 0 and Phase 1 CI success.

**Still unproven:** Causal mechanism, independently registered rotation test, bit-vs-byte representation and new-key generalization.

**Evidence anchors:** research/PHASE2S_DEPTH_MECHANISM_RETROSPECTIVE.md (PR #156); research/PHASE2S_INDEPENDENT_CONTROL_PRELIMINARY.md (PR #156).

**Next experiments / actions:**
- [ ] Prespecify a blinded diffusion/rotation ablation on untouched seeds or cipher configurations.
- [ ] Compare single-bit baseline with higher-order/multibit classical distinguishers and null controls.
- [ ] Do not choose predictive feature after inspecting Phase 2U neural labels.

**Exit criteria:**
- [ ] Independent reproduction and uncertainty intervals
- [ ] Predeclared causal comparison completed or negative result archived
- [ ] No posthoc feature promotion to confirmatory claim

**Prerequisites:** `phase2_replication`.

### Phase 2T original source design—terminated with blocker — P2

**Verified:** Seed 31013 source generation crashed before valid 340-evaluation receipt; original contiguous source study cannot be completed as originally registered.

**Still unproven:** Administrative closeout as invalid source protocol without treating it as a neural-test failure.

**Evidence anchors:** research/PHASE2T_PROSPECTIVE_PREDICTION_PROTOCOL.md (PR #157); research/PHASE2T_SOURCE_GENERATION_LEDGER.md (PR #157).

**Next experiments / actions:**
- [ ] Mark v1 source protocol blocked and immutable.
- [ ] Preserve both accepted v1 S-Boxes as reference exclusions only.
- [ ] Never mix old v1 accepted seeds with versioned 2U panel.

**Exit criteria:**
- [ ] Blocker incident and original receipts linked
- [ ] V1 source failure is not mislabeled as negative neural prediction
- [ ] No in-place edits to v1 scientific rules

**Prerequisites:** `phase2s_mechanisms`.

### Phase 2U 12-S-Box prospective blind prediction — P0

**Verified:** 19 consecutive source seeds, 12 selected permutations, 6460 classical evaluations, exact metrics and 20 distinct global DDT spectra when including eight older sources; 2U original source admission and one full replay passed.

**Still unproven:** Freeze source-bound classical prediction SHA in durable reviewed commit, validate provenance on more than one seed, preregister independent 2U neural evaluation, run outcome model and independent statistical audit.

**Evidence anchors:** research/PHASE2U_SOURCE_RESULTS_FINAL_19_SEEDS_20261102.md (PR #158); GitHub Actions 41460802079 official source admission success; GitHub Actions 41460158043 seed 41003 source replay success.

**Next experiments / actions:**
- [ ] Freeze exact final source panel artifact and its SHA; protect original ZIP receipts from expiry.
- [ ] Run phase2u_predict.py only on complete raw 19-seed prefix and archive immutable prediction receipt BEFORE any neural labels.
- [ ] Independently verify no new neural label has been observed; choose one predeclared 2U evaluation design with sufficient power and actual input/model initialization hashes.
- [ ] Run neural comparison separately with an evaluation that can fail without retuning.

**Exit criteria:**
- [ ] Published source and prediction digests with temporal ordering
- [ ] Independent holdout neural runs have actual provenance and fixed statistical decision
- [ ] Positive OR negative final result frozen, no training reselect

**Prerequisites:** `phase2s_mechanisms`, `phase2_adaptive_repro`.

### TPM mutual learning and passive adversarial attacks — P1

**Verified:** The original 96-session study was INDEPENDENTLY AUDITED against its real, SHA-checked frozen result JSON on 2026-10-23, not merely synthetic fixtures. [Independent audit run 39973978046](https://github.com/Chatnoir01/ml/actions/runs/39973978046) reproduced all three preregistered paired contrasts from [source run 39971905846](https://github.com/Chatnoir01/ml/actions/runs/39971905846): N8/L2 cooperative 21 versus geometric 28/32 (Holm-adjusted p=0.0390625); N16/L3 10 versus 25/32 (p=0.0001220703125); N32/L4 9 versus 25/32 (p=0.000091552734375). The original frozen ZIP SHA-256 was `b2349d818188f61924edf878044837f422cd5bb5c99b8dd7e08da9869ee5f4bc`. **The historical experiment is scientifically closed at its toy-model scope.**

**Still unproven:** Secure key exchange, behavior under different TPM variants, other attacker families, physical hardware cost equivalence and general production resistance. The original source artifact ID `12510291806` and independent audit artifact ID `12510173703` both expire on 2026-12-22 unless independently archived.

**Next actions:**
- [ ] Export both original ZIPs, their SHA-256, run/job IDs, software dependencies and audit log into durable storage before 2026-12-22.
- [ ] Record dispositions for TPM stacked PRs #143–#151 without changing frozen 96-session data.
- [ ] If desired, preregister a *new* study for alternative attacks/cost-matched setups; it must not rewrite the 96-session historical verdict.

**Exit criteria:**
- [x] Original 96-session output-only audit has passed on the real source artifact.
- [ ] Independent long-term artifact retention beyond GitHub Actions.
- [ ] TPM draft PR disposition agreed; no secure-key-exchange claim.

**Prerequisites:** none within this portfolio.

### RAVEN signed continuity, fork evidence, witness quorums — P1

**Verified:** Signed single-transition state/fork/witness model with conditional n>=3f+1, q=n-f; no real persistent fault-tolerant distributed deployment.

**Still unproven:** Specialized RAVEN workflow result absent from checked PR-head runs, persist vote before signature, crash/restart and recovery, multi-epoch reconfiguration, Byzantine network and sybil/fault roster assumptions.

**Evidence anchors:** research/RAVEN_006_INDEPENDENT_WITNESS_QUORUMS.md (PR #155); PR #155 Phase 0 CI success.

**Next experiments / actions:**
- [ ] Run specialized RAVEN invariant suite on same commit and retain logs.
- [ ] Build stable anti-double-sign state with crash-injection tests.
- [ ] Model multiple epochs, key/roster rotations, network partitions and proof availability.

**Exit criteria:**
- [ ] Specialized tests and crash recovery pass
- [ ] Quorum safety/liveness assumptions explicit across epochs
- [ ] No claims of production consensus or BFT

**Prerequisites:** `cryptowall_envelope`.

### Secure Core Android AVF/Secretkeeper/hardware trust boundary — P0

**Verified:** Latest trust-boundary changes intentionally reject synthetic attestation; regression expectations and/or contract remain inconsistent.

**Still unproven:** Fix five failing tests WITHOUT weakening hardware-proof trust gate, verify real signed attestation on compatible hardware and hostile-host scenarios.

**Evidence anchors:** PR #154 Secure Core CI and Phase 0 failed, 2026-10-25; 5 secure-core test failures in latest checked run; 721 other tests passed.

**Next experiments / actions:**
- [ ] Reconcile each of the five failing synthetic trusted-boundary tests with the new fail-closed guarantee.
- [ ] Re-run Secure Core matrix and full Phase 0 on PR #154 without suppressing tests.
- [ ] Separate simulated software trust from hardware-attested states; test Android AVF/Secretkeeper physical device.

**Exit criteria:**
- [ ] All five regressions fixed with strong trust boundary intact
- [ ] Full CI success on exact commit
- [ ] Hardware-security claim withheld until genuine evidence

**Prerequisites:** none within this portfolio.

### CryptoWall X25519 / HKDF / AES-GCM envelope — P1

**Verified:** Isolated authenticated encryption envelope works in software as a research prototype.

**Still unproven:** Sender authentication, message replay, key life-cycle, nonce domain safety, protocol misuse resistance and cross-implementation verification.

**Evidence anchors:** PR #136 CryptoWall V1 and Phase 0 CI success.

**Next experiments / actions:**
- [ ] Threat model sender/recipient identities and key compromise.
- [ ] Negative-test replay, nonce collision, wrong recipient and downgrade handling.
- [ ] Obtain protocol review before production integration.

**Exit criteria:**
- [ ] Protocol-level authenticated origin and replay decisions documented
- [ ] Negative and interop tests complete
- [ ] No blanket security claim from primitive correctness

**Prerequisites:** none within this portfolio.

### CryptoWall hybrid ML-KEM-768 + X25519 HPKE — P1

**Verified:** Opt-in hybrid KEM/HPKE prototype exercised through library, not an invented post-quantum primitive.

**Still unproven:** Protocol downgrade/version negotiation, key confirmation, KEM failure handling, identity binding and interop/cross-library checks.

**Evidence anchors:** PR #139 Hybrid HPKE and Phase 0 CI success.

**Next experiments / actions:**
- [ ] Document exact dependency versions, hybrid KDF inputs and binding order.
- [ ] Test downgrade, cross-protocol replay, wrong key and decryption-failure states.
- [ ] Independent protocol review before integration with CryptoWall v1.

**Exit criteria:**
- [ ] Hybrid interoperability and negative tests complete
- [ ] Primitive and library provenance reviewed
- [ ] Production security separated from prototype

**Prerequisites:** `cryptowall_envelope`.

### BFV homomorphic encrypted-sum demonstrator — P2

**Verified:** BFV encrypted addition without giving secret decryption key to evaluator demonstrated.

**Still unproven:** Only if expanding beyond original demo: parameter/noise budget analysis, data-privacy threat model, batching and benchmarks.

**Evidence anchors:** PR #140 BFV specialized and Phase 0 CI success.

**Next experiments / actions:**
- [ ] Freeze initial demonstrator and dependency versions.
- [ ] Open distinct new study for parameter/noise and throughput work rather than changing original demo.

**Exit criteria:**
- [ ] Research-only demonstration clearly marked
- [ ] Original result and CI preserved
- [ ] Any scale-up gets its own preregistered study

**Prerequisites:** none within this portfolio.

### BB84 intercept-resend simulator — P2

**Verified:** Idealized BB84 basis sifting, intercept-resend and error rate statistics reproduced in software.

**Still unproven:** Only if extending beyond simulator: finite-key statistics, physical loss, noise and classical authenticated channel assumptions.

**Evidence anchors:** PR #141 specialized quantum simulation and Phase 0 CI success.

**Next experiments / actions:**
- [ ] Freeze simulator and original statistical test scope.
- [ ] Do not imply physical quantum communication; open separate finite-key simulator study if needed.

**Exit criteria:**
- [ ] Simulation results reproducible and marked idealized
- [ ] Physical security claims explicitly excluded

**Prerequisites:** none within this portfolio.

### Neural Alice/Bob/Eve educational obfuscation lab — P1

**Verified:** Smoke paths and bounded neural adversarial training code execute.

**Still unproven:** Full 200-step preregistered Alice/Bob/Eve experiment, fresh attacker controls, multiple seeds, confidence intervals, hard-coded baseline and key/message leakage checks.

**Evidence anchors:** PR #138 neural crypto lab smoke CI and Phase 0 success; research/NEURAL_CRYPTO_LAB_V1_PROTOCOL.md (PR #138).

**Next experiments / actions:**
- [ ] Execute original complete protocol with independent fresh Eves and fixed seeds.
- [ ] Compare Bob reconstruction and strongest held-out Eve; include plaintext/key linear baseline and controls.
- [ ] Record negative result without claiming encryption security.

**Exit criteria:**
- [ ] Full original protocol result archived
- [ ] No test-set tuning or posthoc optimizer changes
- [ ] Explicit NOT encryption product

**Prerequisites:** none within this portfolio.

### Research CI execution, retention and PR dependency hygiene — P1

**Verified:** No general consolidation in main; specialized CI success is not a proof of production security.

**Still unproven:** Review workflow scopes, PR base dependency edges, artifact expiry, merge ordering and reproducible provenance after rebases.

**Evidence anchors:** 38 open draft PRs at 2026-11-02 GitHub snapshot; RAVEN/TPM/Secure Core branches stacked on other research PRs.

**Next experiments / actions:**
- [ ] Archive source artifacts and SHA manifests; preserve original run IDs and time ordering.
- [ ] Identify stacked branch dependencies and classify superseded PRs without deletion.
- [ ] Make research-only CI and proof gates mandatory before merging shared infrastructure.

**Exit criteria:**
- [ ] All 38 current PRs assigned to owner workstreams
- [ ] No duplicate or dropped PR
- [ ] Merge plan shows topological order and non-deployment boundary

**Prerequisites:** none within this portfolio.

## 4. Hard preservation and scientific stop conditions

1. **Do not rewrite frozen outcomes.** The Phase 2G negative and the Phase 2T-v1 source failure are permanent historical results of their exact registered protocols.
2. **No exploratory-to-confirmatory laundering.** Phase 2S was post-hoc on six older S-Boxes. Phase 2U candidates are mathematically selected, but the predicted neural ranking has NOT been timestamped/frozen. All new neural scores must remain unobserved until that rank is sealed and an independently approved neural protocol exists.
3. **No synthetic-to-real evidence laundering.** Phase 2R, TPM receipt auditor, RAVEN and Secure Core may include synthetic fixtures; each must separately meet the actual original artifact/hardware test gate.
4. **No security boundary regression.** The 2026-10-25 PR #154 Secure Core job showed five trust-boundary test failures. Repairs may modify obsolete test expectations only with explicit proof that synthetic pVM evidence still cannot qualify as real hardware attestation.
5. **No cross-product merge.** Do not install Neural Crypto / ToySPN / TPM / RAVEN research constructions inside CryptoWall or production encryption on the basis of research CI alone. Keep libraries and tests isolated.
6. **No artifact loss.** Retain original GitHub Actions ZIPs before expiry, their SHA-256, unique source run/job IDs, Python/package versions, source commit, seeds and reason for every missing output. A hash without independently verified source/time provenance is not an authenticated scientific receipt.
7. **No merging stacked branches out of order.** Prefer squash/cherry-pick with explicit list of commits and files **only after** separate scientific documentation, dependency and CI checks. Avoid dragging unrelated experiments across branch bases.

## 5. Clear transition conditions for later unification

A later unification proposal is permitted only when:
- every listed PR has a reviewed disposition (merge as research-only, keep archive, superseded, or security-blocked);
- all original scientific outputs and negative findings have stable provenance;
- P0 failures are either resolved or independently documented as explicit blockers with no production path;
- tests confirm that moving code does not alter original source/proof bytes or frozen result digests;
- research-only modules stay behind non-production entry points, with explicit contracts and versioned interfaces.

**This registry is a preservation and execution instrument, not a claim that all tracks are finished.**
