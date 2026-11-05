# Scientific contributions, priority evidence and open hypotheses — 2026-11-05

**Status: dated research communication register; evidence-bound, NOT a claim of universal novelty, security certification, patent title, or independent peer review.** This document adds a dated communication layer to the unmodified 2026-11-02 portfolio snapshot. It neither overwrites that snapshot nor changes any frozen experiment. The author/contributor attribution for external publications must be reviewed by the project owner.

## 1. Evidence standards

- **Observed**: executed original protocol + original result and identifiable source/experiment provenance.
- **Rechecked**: independently implemented calculation or read-only receipt audit checks original source output (still not necessarily independent hardware replication).
- **Prospective pending**: hypotheses, candidates and/or predictions fixed, but the primary future measurement has NOT occurred.
- **Prototype only**: code and targeted tests exist, without independent proof of the claimed security boundary.
- **Unestablished**: novelty against all relevant prior art, deployment-grade security, universal generalization, causal mechanism, and commercial value unless separately substantiated.

A timestamped repository commit / workflow log can establish that a particular artifact existed at a particular point in a third party's record; a displayed web page date alone is weaker. **None of these demonstrates that no one else discovered the concept earlier.** SHA-256 identifies bytes, not authorship or truth. Store the underlying evidence permanently; hashes without source artifacts are insufficient.

## 2. Contribution ledger (source-bound statements)

### C01 — Phase 2G: neural coevolution versus fixed retraining

**Observed, negative official outcome.** Four arms C/F/A/S, nine preregistered evolution seeds, 2,880 scientific neural trainings (2,304 checkpoint and 576 held-out). The adaptation mechanism was active, but only 6/10 preregistered support checks passed; official verdict remains `phase2g_adaptive_coevolution_not_supported`. Mean held-out neural advantage: A 0.284493866660; F 0.242436934627; S 0.312446887544; C 0.349020522330; smaller is better. A beat F on **0/9** seeds. Classical nondegradation failed on two seeds.

**Sources:** [frozen result](https://github.com/Chatnoir01/ml/blob/research/phase2g-adaptive-coevolution/research/PHASE2G_RESULT.md), [original workflow 35572084785](https://github.com/Chatnoir01/ml/actions/runs/35572084785).

**Allowed claim:** "In our controlled ToySPN experiment, active adaptive coevolution failed the preregistered criterion and fixed-curriculum retraining performed better on all nine held-out seed comparisons."

**NOT proven:** that learning adaptation is generally harmful, why the effect occurs, or resilience of any deployed cipher. The initial A/F checkpoint-0 model hashes differed on four of nine paired seeds; historical cause remains unknown.

### C02 — TPM 96: attack-strategy comparison in a toy model

**Observed and independently receipt-audited.** Paired geometric / cooperative successes across 32 trials per scale:
- N8/L2: geometric 28/32 vs cooperative 21/32; Holm-adjusted p=0.0390625.
- N16/L3: geometric 25/32 vs cooperative 10/32; Holm-adjusted p=0.0001220703125.
- N32/L4: geometric 25/32 vs cooperative 9/32; Holm-adjusted p=0.000091552734375.

**Sources:** [original 96 trials](https://github.com/Chatnoir01/ml/actions/runs/39971905846), [audit of actual original result](https://github.com/Chatnoir01/ml/actions/runs/39973978046), [evidence preservation report](https://github.com/Chatnoir01/ml/blob/research/portfolio-closure-register-20261102/research/RESEARCH_EVIDENCE_RETENTION_20261102.md).

**Allowed claim:** "One predeclared attack strategy outperformed its paired comparator in three toy TPM configurations under the tested model and trial budgets."

**NOT proven:** secure key exchange, real-world attack superiority, novel geometric attacks as a general concept, equivalent wall-clock adversary budgets or independently replicated hardware effects.

### C03 — Phase 2U: sealed prospective classical predictor

**Observed classical source; prospective neural hypothesis pending.** 19 registered source seeds, 12 admitted candidate S-Boxes, seven excluded source seeds, 6,460 classical evaluations. Original source panel SHA-256 `512dd21d01617944047fd4e6f6ec2ae09daa68bc76d808837527a384148914ef`. Pre-neural frozen classical prediction receipt SHA-256 `cd4bfbc9736ced13bdcf95c06f156d4244fbbdde65b05c51fb4e7958a21a30f4`. The ranking was independently recalculated using a separate implementation. **Zero Phase 2U neural outcomes.**

**Sources:** [frozen prediction and all 12 rows](https://github.com/Chatnoir01/ml/blob/research/phase2u-robust-source-20261102/research/PHASE2U_CLASSICAL_PREDICTION_FROZEN_20261102.md), [source-bound original prediction workflow](https://github.com/Chatnoir01/ml/actions/runs/41539098859), [independent clean replay](https://github.com/Chatnoir01/ml/actions/runs/41541767420).

**Allowed claim:** "We preregistered and independently rechecked a classical ranking of twelve source-admitted S-Boxes before collecting new neural labels."

**NOT proven:** positive neural rank correlation, stronger S-Boxes, novel cryptographic property, cipher resistance or out-of-domain generalization. No trial or threshold may be changed after outcome inspection.

### C04 — Phase 2R: checkpoint-zero instrumentation and reproducibility gate

**Engineering tests passed; historic discrepancy still open.** The historical Phase 2G A/F initial model-state hashes agreed on 5/9 paired seeds and disagreed on 4/9; equal declared seeds are not actual byte equivalence. Phase 2R introduced a new synthetic twenty-S-Box fixture, dataset canonical serialization, receipt auditing, actual input-generator preflight and subsequently a read-only initialization/RNG fingerprint helper.

**New audit evidence:** [draft PR #161](https://github.com/Chatnoir01/ml/pull/161), [observation-only 7-test Python 3.10/3.11/3.12 CI](https://github.com/Chatnoir01/ml/actions/runs/41897769126), [Phase 0 CI](https://github.com/Chatnoir01/ml/actions/runs/41897769183), [Phase 1 benchmark](https://github.com/Chatnoir01/ml/actions/runs/41897769500).

**Allowed claim:** "The independent synthetic tests confirm that the new hash-observation helper records initialized weight/RNG identity without consuming the sampled training permutation under the tested setup."

**NOT proven:** actual full neural-run reproducibility, a cause of the historic 4/9 mismatches, cross-CPU bitwise equality or prior-art novelty. PR #161 is **not** integrated into the trainer and is not a science execution authorization.

### C05 — Research security prototypes (separate from validated encryption)

**Prototype only.** RAVEN signed-state continuity and crash-only journal controls; CryptoWall X25519/HKDF/AES-GCM envelope and experimental hybrid ML-KEM-768/X25519; educational homomorphic BFV and BB84 simulators; educational neural Alice/Bob/Eve lab.

**Sources:** [RAVEN PR #160](https://github.com/Chatnoir01/ml/pull/160), [specialized RAVEN job](https://github.com/Chatnoir01/ml/actions/runs/41540243153), [CryptoWall PR #136](https://github.com/Chatnoir01/ml/pull/136), [hybrid PR #139](https://github.com/Chatnoir01/ml/pull/139), [BFV PR #140](https://github.com/Chatnoir01/ml/pull/140), [BB84 PR #141](https://github.com/Chatnoir01/ml/pull/141), [Alice/Bob/Eve PR #138](https://github.com/Chatnoir01/ml/pull/138).

**NOT proven:** deployment security, formal protocol proofs, real hardware attestation, production-grade distributed fault tolerance, physical quantum communication. [Secure Core PR #154](https://github.com/Chatnoir01/ml/pull/154) retained five hardware trust-boundary test failures in the last documented run; do not convert simulated attestation into a security claim.

## 3. Prior-art boundaries: comparison required before any novelty claim

The following established themes precede this project:
- Neural synchronization / tree parity machines and an adversarial learner: Rosen-Zvi et al., Phys. Rev. E (2002), DOI [10.1103/PhysRevE.66.066135](https://doi.org/10.1103/PhysRevE.66.066135).
- Evolutionary or stochastic S-Box design: Clark, Jacob & Stepney (2004), [institutional record](https://eprints.whiterose.ac.uk/id/eprint/7103/).
- Neural differential cryptanalysis and methodological risks: Gerault et al., survey [IACR-associated research record](https://ouci.dntb.gov.ua/en/works/lxLPxKmN/). The full current literature must be searched and checked by a specialist.
- More recent neural distinguisher architecture search also exists: [Applied Soft Computing, October 2026](https://www.sciencedirect.com/science/article/pii/S1568494626012809).

**Candidate contributions to investigate (NOT declared original):**
1. Generalization of classical single-bit differentials into blinded neural distinguishability across matched classical S-Box metrics, fresh architectures and data/keys (Phase 2U).
2. Measured explanation of why near-total evolving-curriculum replacement underperforms fixed retraining, followed by targeted intervention and independent replication (2G/2H/2R/2I/2J).
3. Under clearly matched budgets, the effect of passive adversary strategy across TPM parameter scales, with comparisons against strong prior attacks, outside toy-only conclusions.
4. Security properties of signed distributed state continuity under explicit crash/rollback/Byzantine threat models, only if novel relative to authenticated logs and existing distributed protocols.

Do not describe the *general ideas* of neural cryptanalysis, geometric TPM attacks, adaptive surrogate models or S-Box evolution as invented here.

## 4. Ranked prospective research gates (new data only after precommit)

| Rank | Gate | Strict next evidence | Stop condition |
|---|---|---|---|
| P0 | Evidence survival | Preserve complete original source artifacts in independently verified, durable storage; include original SHA and chronological links | Missing source or archive integrity fails |
| P0 | Phase 2R comparability | Freeze model-initialization serializer, actual environment/BLAS provenance, all 16 input cells across processes; separately authorize 4-run A1/A2/F1/F2 comparison | Any missing data/init/state hashes or runtime mismatch |
| P0 | Phase 2U prediction | Preregister independent neural architecture, 12 candidate identities, seed schedule, Spearman rank primary endpoint, effect threshold, correction/failure policy before labels | Any precommit mismatch, leakage or incomplete provenance |
| P0 | Secure Core boundary | Demonstrate failure of synthetic/fabricated hardware evidence using genuine hardware-boundary tests | Any trust-boundary regression |
| P1 | Mechanism/replication | Test targeted stable-vs-adaptive curriculum intervention on **new** seeds, then independent environment/hardware | Frozen 2G reused for post-hoc significance |
| P1 | TPM extension | New paired trials against credible alternative attackers under fair measured budgets | Uncontrolled comparisons or post-hoc seed selection |
| P1 | CryptoWall/RAVEN | Independent threat-model review, interop and adversarial/restart tests | Only friendly-path or synthetic proof |

Scientific work should follow these gates; passing one does not authorize the next without a separately frozen study.

## 5. Public site and CV publication readiness

A public site may **accurately** describe the above verified results with links to original workflow runs and frozen report commits. Each presented result should have: date of the *externally verifiable* artifact (not a manually editable label), author/contributor disclosure, precise method, sample count, baselines, observed result, uncertainty, limitations, underlying inputs, and code version.

**Priority is narrow**: a timestamp establishes existence of particular recorded content, not universal originality or exclusive intellectual property. Before publishing any currently non-public enabling technical invention, assess IP strategy first. No such invention is newly disclosed in this ledger; statements consolidate publicly visible material.

A defensible résumé formulation: "Independent, AI-assisted defensive cryptography research laboratory: 2,880 preregistered neural-training runs in a controlled coevolution study; independently audited 96-trial toy TPM strategy comparison; source-hashed prospective 12-S-Box prediction; reproducibility engineering in Python and GitHub Actions." Attribution should accurately describe the author's own work and AI assistance.

## 6. Retention and immutability warnings

Original Phase 2G workflow artifacts were advertised to expire **2026-12-20**; original TPM 96 artifacts **2026-12-22**. The external 66-ZIP bundle documented in the existing portfolio report is **NOT proven independently preserved**. The separate preexisting 2026-11-02 manifest remains immutable and is not updated by this new 2026-11-05 document.

**No training, score generation, promotion, refactoring of frozen science, PR merges or deployments are triggered by this file.**
