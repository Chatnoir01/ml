# Phase 2V-T1 — ciphertext-only classic distinguisher transfers to held-out S-Boxes and a fixed alternate key
**Source-backed synthetic read-only research result, 2026-11-06. Protocol preregistered BEFORE computation at commit `fc6c8941cf287e269c3775035ed00530608b9bce`. No neural model training or phase2U unblinding.**

## Question and preregistered scope

Prior [Phase 2V classical baseline experiment](PHASE2V_CLASSICAL_FALSIFICATION_RESULT_20261106.md) found median AUC about 0.691 for a four-position, Laplace-1, train-only ciphertext-XOR-byte naive Bayes baseline over 144 historical-source-**reconstructed** four-round ToySPN checkpoint-zero cells. Does this signal persist without fitting again when the test data contain **new S-Box identities** and ciphertexts encrypted under **another independently fixed public key schedule**?

[Phase 2V-T1 prespecified protocol](PHASE2V_T1_KEY_SBOX_TRANSFER_PROTOCOL_20261106.md): all **nine original evolution curricula** (9×20 authentic checkpoint-zero S-Boxes), **both original input differences 1 and 256**, and **two T seeds selected by original index** 776003 and 776097. Total **36 cells**, each with 15 fingerprint-sorted S-Boxes used to train its elementary count table (**4,200 original-key training pairs**) and five **entirely unseen by the histogram** S-Boxes. Four prespecified test arms per cell: 15 known S-Boxes at original keys (**900 pairs**), five unseen S-Boxes at original keys (**300**), 15 known S-Boxes at alternate keys (**900**), five unseen S-Boxes at alternate keys (**300**).

The one alternate public five-word 32-bit key schedule was generated **before outcome** from `SHA256("phase2v-t1-key-schedule-20261106-v1|" || decimal_index)[:4]` for indices 0–4, producing **`7687fafa,e8f31286,f7bf81fd,88905423,f2f2b1ea`**. The original source keys are `243f6a88,85a308d3,13198a2e,03707344,a4093822`. There was no key search, no model tuning and no additional cohort selected after observing results.

Each counterfactual alternate-key pair uses the **same original plaintext pair draw and label order as its source-key counterpart**, so this is a paired controlled key change, **NOT independent new plaintext sampling or a multi-key population test**. All 20 original checkpoint-zero S-Boxes in a cell also share the same original T-seed plaintext draws and label schedules, a previously identified dependence.

## Numerical outcomes — all 144 registered evaluation arms

Exact tie-aware held-out AUC values from ciphertext inputs alone; the counts estimator was fitted **once per cell on original-key 15-S-Box train samples**, then evaluated unchanged in all four test conditions. No neural training.

| Predeclared test domain | Number of cells | Hamming weight AUC median | Zero output-XOR-byte AUC median | Trained-once byte-histogram AUC median | Byte-histogram min–max | Cells histogram AUC > 0.5 |
|---|---:|---:|---:|---:|---:|---:|
| Seen S-Boxes + original keys | 36 | **0.637363** | **0.682061** | **0.686716** | 0.648326–0.713472 | **36/36** |
| **Unseen S-Boxes** + original keys | 36 | **0.640001** | **0.683588** | **0.689214** | 0.626991–0.739820 | **36/36** |
| Seen S-Boxes + **alternate keys** | 36 | **0.638502** | **0.679596** | **0.682709** | 0.657015–0.727843 | **36/36** |
| **Unseen S-Boxes + alternate keys** | 36 | **0.645249** | **0.685354** | **0.686217** | 0.606599–0.750362 | **36/36** |

The constant-score null yields **exact AUC 0.5 in every one of 144 panels**. The unfitted Hamming and zero-byte scores also exceed 0.5 in all 144 panels. This is not a report of 144 independent successes: labels/plaintext draws, curricula, key schedules and model training tables are shared.

**Prespecified paired histogram AUC differences**, each calculated *within* one of the 36 original cells relative to seen/original-key AUC:

| Target transfer | Median signed AUC change | Per-cell min–max signed change | Number showing positive vs negative difference |
|---|---:|---:|---:|
| Unseen S-Boxes / original keys | **+0.0101036** | −0.05490 to +0.06181 | 23 positive / 13 negative |
| Seen S-Boxes / alternate keys | **−0.0027514** | −0.03792 to +0.07952 | 16 positive / 20 negative |
| Unseen S-Boxes / alternate keys | **+0.0009777** | −0.09262 to +0.10204 | 18 positive / 18 negative |

Thus the histogram remains meaningfully above *chance* under both registered shifts but has **no consistently positive or negative shift from the original test setting**. The relative transfer effect varies substantially by cell. The difference of the medians is not equal to the paired median difference and must not be conflated.

## Source integrity and reproducibility

The study was run using standard-library-only Python, importing the original pure-Python Phase2G source reconstruction and the Phase2V ROC AUC/Hamming/histogram helpers. It **does not** import or train a neural model. **All 36 original-source reconstructed cells** passed:

1. Original 20-S-Box curriculum canonical SHA3-256 fingerprints and archived 2026-09 A/F reconstructed SHA identity validated before any scores;
2. Exact reconstructed full 20-S-Box source-key ordered train/validation/test SHA3 receipts equal to the independently preserved Phase2G checkpoint-zero reconstruction (5,600/1,200/1,200);
3. Alternate and original key encryptions use the SAME deterministic source plaintext pair/label stream. The alternate-key source stream was checked against an independent original-key `generate_pair_splits` implementation **for every one of 720 S-Box-by-cell calls** (36 cells ×20 S-Boxes);
4. Fixed training/test geometry and both binary labels present; **zero exact source training ciphertext blocks OR full ciphertext pairs** appear in any of the **144** evaluated test panels;
5. One canonical JSON `receipt_sha256` self-hash validated. All 144 row keys unique and each of four arms has exactly 36 rows;
6. The **first and last prespecified source cells** were independently reconstructed and their four score AUCs recomputed by *direct positive-negative pair enumeration*, **32/32 comparisons matched** the original rank-based implementation (absolute float tolerance `5e-15` for arithmetic only; no relaxation of SHA checks);
7. The complete downloaded evidence ZIP was extracted into a separate clean directory and **both the full JSON and full 144-row CSV reproduced with exactly the same SHA-256 bytes**, without neural training or dependence on the original paths. AUC spot checks passed again there.

### Integrity manifest

- Prespecified GitHub research protocol commit **`fc6c8941cf287e269c3775035ed00530608b9bce`** (created before computation).
- Original prior Phase2G reconstruction source ZIP **`phase2g_checkpoint0_forensics_reconstruction_verified_20261106.zip`**, unchanged outer SHA-256 **`6f6b6fbe68a123ad8bf302b4ba3a80f069e9d8ab64188121c28e631a66444845`**, contains 39 original Phase2G scientific ZIP artifacts and authenticated S-Box curricula.
- Full baseline script **`phase2v_t1_classical_transfer_20261106.py`**: SHA-256 **`e5aeee5224b21bb7f6bdff953b0d8c0bc752845c4f5a7b39083ca60935aa876d`**.
- Detailed 144-row JSON `phase2v_t1_key_sbox_transfer_audit_20261106.json`: file SHA-256 **`274c811bf738c0b793a4f525aecb799e3d1dbb582f7ee25036e02316b46de430`**, canonical internal receipt SHA256 `a9794cbbbfc5f292a9fd3f0c9c3612f2fda2fdfd8081a93b8cc70d40d030feaa`.
- Original 144-row CSV `phase2v_t1_key_sbox_transfer_results_20261106.csv`: SHA-256 **`0d16236ab5c95858a1a130e67e3269c18e0fe0dbdcb4ebb262f3944a3b55f273`**.
- Complete internally verified conversation evidence ZIP **`phase2v_t1_key_sbox_transfer_verified_evidence_20261106.zip`**, **7,147,329 bytes**, SHA256 **`49a6c053feb96e9ae94ac9aece36d8ea8dd0c5e63a9a31f769a469f2438deb20`**; contains unchanged original source ZIP, original reconstruction helper and baseline helper scripts, new transfer script, full source JSON/CSV, independent pair-enumeration spot-check code and machine JSON, README, full SHA256SUMS. ZIP CRC and all member hashes pass. **No independently user-owned durable archival copy is verified**.

## What we have established and not established

**Established in this fixed educational synthetic setting**: a weak classical, ciphertext-only XOR-difference histogram trained on 15 original S-Boxes remains above AUC 0.5 when tested on five different S-Box identities, and after a prechosen public key schedule change, without any refitting. The toy cipher's distinguishability cannot be attributed solely to memorizing the 15 training S-Boxes or one exact key-byte sequence. It is **consistent with a differential feature caused by the ToySPN round structure**. This is not surprising for a simple educational cipher but is a stringent essential comparison.

**Not established:** a new cryptanalytic property in a real-world cipher; superiority or inferiority of any historical neural model (not matched at these exact splits), independence from the reused plaintext samples/label structure, a general theorem for all possible keys, broad unseen-key generalization or the historical Phase2G 64/144 trained-weight hash root cause. The test uses **only one** alternate key family and five held-out original-pool S-Boxes per cell. This is **36 correlated panels × 4 arms, not 144 IID replicates**; no statistical p-values or confidence intervals are claimed.

**Next scientifically decisive falsification:** in a separately preregistered experiment compare this baseline against (a) a random-permutation oracle with matched input draws and block size, (b) independently re-sampled plaintext schedules per S-Box and key, and (c) genuine matched neural baseline; the previous sealed Phase 2U neural panel remains unexecuted until its independent authorization and prerequisites. Original Phase 2G negative verdict `phase2g_adaptive_coevolution_not_supported` unchanged, no new model training, no merge to `main`, DRAFT only.
