# Phase 2V — read-only classical ciphertext-only distinguishers on 144 reconstructed checkpoint-zero ToySPN panels

**Observed 2026-11-06; preregistered before the calculations in [protocol](PHASE2V_CLASSICAL_FALSIFICATION_PROTOCOL_20261106.md), first protocol commit `70858952925366ebaf81a883ed40f802f9bd8924`. NO NEURAL TRAINING, NO Phase 2U outcomes and no modification of frozen Phase 2G scientific results.**

## Research question

Do simple **key-agnostic, ciphertext-only** classical statistics of `C0 XOR C1` detect the class labels in Phase 2G checkpoint-zero historical-format **ToySPN** synthetic data? The purpose is to establish a falsification baseline before interpreting any purported neural cryptanalytic advantage. This does **not** compare matched neural and classical AUC and cannot claim the classical baseline defeats any given neural model without an experiment on identical splits, keys, S-Boxes and training budget.

The original ToySPN is an educational 32-bit four-round substitution-permutation network with **fixed round keys**. It was never intended as a production cipher. Neural differential distinguishers and classical difference-distribution baselines were studied long before this project (e.g., Gohr CRYPTO 2019; see https://eprint.iacr.org/2019/037).

## Exact preregistered source panel, data and metrics

Exactly **144** original checkpoint-0 reconstruction panels: nine evolution seeds × two differences `1, 256` × eight dataset/model seed pairs, with **20 authenticated S-Boxes** per curriculum and split geometry **5600/1200/1200**. All 9 original S-Box curriculum fingerprints match the September 2026 archives; each reconstructed train/validation/test SHA3-256 is checked against the separate reconstruction evidence frozen in PR #169. **Critical provenance limit:** the original September run archived neither raw dataset bytes nor their hashes. These data are deterministic, source-derived *reconstructions*, NOT independent authentication of the original execution's full training dataset.

Every score uses **only the two observed ciphertexts** and original test labels for AUC evaluation; no plaintext or round keys are supplied to any distinguisher. All five score definitions were frozen **before computing** this new result:
1. `0.0` constant-score null AUC;
2. `-bit_count(C0 XOR C1)` fixed-direction 32-bit output Hamming-weight baseline;
3. `sum((byte(C0 XOR C1) == 0) for byte in 4 bytes)` equality-byte count;
4. an elementary four-byte **naive Bayes log-likelihood histogram** estimated from the **5600 original reconstructed TRAIN pairs only** with Laplace alpha=1, evaluated on 1200 original reconstructed TEST pairs;
5. the same histogram after exactly **one precommitted shuffle of TRAIN labels**, with seed `0xD15EA5E XOR evolution_seed XOR T_seed XOR difference`, evaluated on the unmodified test labels. No adaptive search, hyperparameter adjustment or neural model fit.

ROC AUC computed tie-aware with average ranks exactly as in the original `_auc_from_scores`. No selection of direction after outcomes; the neural-style `2*|AUC-0.5|` is not conflated with a signed AUC.

## Verified numerical outcomes

**144/144** panels were generated with source-bound exact train/validation/test SHA3-256; all five AUC statistics are recorded per panel in the accompanying JSON/CSV.

| Predeclared scoring method | Median AUC /144 | Minimum AUC | Maximum AUC | Number of panels with AUC strictly >0.5 |
|---|---:|---:|---:|---:|
| Constant-score null | **0.500000** | 0.500000 | 0.500000 | 0 / 144 |
| Negative output XOR Hamming weight | **0.6415777224** | 0.5979506138 | 0.6781306561 | **144 / 144** |
| Identical output XOR bytes | **0.6838200645** | 0.6580486425 | 0.7097557143 | **144 / 144** |
| Smoothed independent XOR-byte histograms, alpha=1 | **0.6909727154** | 0.6533399321 | 0.7255020255 | **144 / 144** |
| Same histogram after fixed training-label shuffle | **0.5018222462** | 0.4520300334 | 0.5444215795 | 77 / 144 |

**By original input difference:** for `1`, respective median Hamming/zero-byte/histogram/shuffled AUC: **0.641251 / 0.683502 / 0.690973 / 0.502778**; for `256`: **0.642508 / 0.684363 / 0.690881 / 0.500746**. The nine **evolution-seed grouped** median four-byte histogram AUC values range from **0.679863** (726023) to **0.697179** (726061), using within-seed 16-cell medians rather than pretending the 144 panels are independent.

**Within-reconstructed-panel source-integrity control:** **0 / 144 panels** had any exact ciphertext block or ciphertext pair shared between aggregated train and test, even *across different S-Boxes*. This reduces concern about literal train/test ciphertext duplicates in these reconstructions; it does **not** demonstrate absence of statistical dependence, key conditioning or other leakage. As already established, all 20 S-Boxes per panel re-use the same underlying plaintext sample draws and class-label sequence.

## Interpretable mechanism: positive pairs often preserve an equal output byte

In a preselected first-edge panel (evolution seed `726011`, input difference `1`, dataset T seed `776003`), on original-format reconstructed TEST examples:
- **37.8846%** of positive-pair XOR outputs contain **at least one zero byte** (an unchanged byte between ciphertexts);
- **1.9118%** of negative-pair XOR outputs have any zero byte;
- the count-of-zero-bytes distinguisher achieves **AUC `0.6803054298642534`**.

On the last-edge panel (726113, difference 256, T 776097), corresponding positive vs negative fractions are **38.1481%** and **1.2121%**, with zero-byte-count AUC **0.6850953984287318**.

Thus a simple property of the ToySPN output XOR reveals substantial **differential structure** without neural learning, even after four rounds. This is a property of THIS educational construction and synthetic data, **not** a newly discovered vulnerability in a real-world cipher.

## Independent audit and reproducibility

The experiment was performed by a **new, standard-library-only Python script** on the original proven reconstruction archive, not by updating or re-running the 2G historical neural pipeline. Code:
- `phase2v_classical_baseline_audit_20261106.py`, SHA-256 **`bea5597bfa4582853584ee34b25c5d67afb7a81ce6ce0346a63f4b922e1d7774`**;
- results `phase2v_classical_baseline_144_audit_20261106.json` SHA-256 **`2d2654a0a3e52b53651447d401da0a6c423abdfa2ad6ac9ff20feae7e03be641`**, including canonical self-hash and all 144 exact source split hashes;
- 144-row CSV `phase2v_classical_baseline_144_results_20261106.csv` SHA-256 **`19653634c10df672420007414aa0388dfeccb729841919087a5e96783fb47b86`**.

An **additional independently formulated positive-versus-negative pair-count AUC formula** rechecked Hamming, zero-byte, and naive-Bayes AUC on the **first and last prespecified source edge panels**: **6/6** exact matches (apart from ordinary Python binary-float representation tolerance at 5e-16). This is an independent **AUC arithmetic** check, not independent source input capture; the other 142 panel scores were regenerated, SHA-verified and internally tied to a canonical result receipt.

Independent spot-check script and JSON are included with original source evidence. All original archive inputs are untouched and remain independently inspectable. Complete downloadable evidence package `phase2v_classical_falsification_144_verified_evidence_20261106.zip`, **7,155,083 bytes**, outer SHA-256 **`5f4d4c4fb8224fc9501bce2bd14a82a450f61fd483eb161138346034bd71ab5c`**. Contents: *unchanged* 39-artifact Phase 2G preservation+reconstruction ZIP (including original source evidence), classical baseline source, raw per-cell JSON/CSV, independent spot check source/result, README and SHA256SUMS. All contained checksums and ZIP CRC verified. **Not a verified user-owned durable external backup.**

## What this changes and next falsification experiments

**Demonstrated at this synthetic scope:** even trivial classic ciphertext difference statistics produce a consistently measurable distinguisher AUC above the 0.5 null. More elaborate neural models must demonstrate a meaningful **incremental** effect over such baselines on **matched datasets** and ideally after transferring to unseen keys and unseen S-Boxes, otherwise the neural AUC may merely restate obvious ToySPN differential structure.

**NOT demonstrated:** that these classic baselines beat any historical Phase 2G neural model (no exact matched neural train/test comparison performed), that source September dataset bytes are authenticated, that the AUC generalizes to fresh keys, or that the simple histogram is an optimal differential DDT/LAT distinguisher. The 144 panels share S-Boxes/keys/sample seeds and are **not IID replicates**; no p-values, confidence intervals, population generalization or novelty claims are supported.

The appropriate *new, distinct preregistration*, before future neural work, must include (i) same-split weak classical baselines plus a strong DDT-based comparator, (ii) genuinely unseen round-key families, (iii) genuinely unseen S-Box families, (iv) plaintext sample schedules generated independently per S-Box, and (v) non-cherry-picked neural-vs-classic effect sizes with full provenance.

Frozen Phase 2G verdict remains **`phase2g_adaptive_coevolution_not_supported`**, phase2U prospective 96-run sealed panel remains **zero trained**, no merges to main, branch remains DRAFT.
