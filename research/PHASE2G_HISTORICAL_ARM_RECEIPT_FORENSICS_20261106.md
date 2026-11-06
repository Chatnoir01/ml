# Phase 2G — historical A/F checkpoint and arm-dependent training-receipt provenance re-audit
**Date: 2026-11-06. Status: source-backed FORENSIC AUDIT; ZERO new neural trainings; original historical verdict frozen.**

## What was investigated

Original frozen Phase 2G scientific [GitHub Actions run 35572084785](https://github.com/Chatnoir01/ml/actions/runs/35572084785), source checkout **`030652489dd489a4705bbf64a12d7e6fa01ca03b`**, comprising 9 evolutionary seeds × 2 arms (adaptive **A**, fixed **F**) × 4 checkpoints (generation 0, 5, 10, 15) × 16 model-state SHA receipts. We independently inspected and rehashed the **18 unchanged original A/F ZIP sources**, their inner scientific payload canonical SHA-256, and the pre-existing preservation archive of **all 39 original Phase 2G source ZIPs** (39/39 ZIP CRC). This work does not recreate original historical input tensors, untrained weights or missing CPU runtime fields.

**Reproduction code:** `phase2g_historical_af_provenance_verifier_20261106.py` saved with the conversation evidence, plus detailed JSON and 36-row CSV. The script reconstructs the exact historical [`_checkpoint_training_receipt()` source](https://github.com/Chatnoir01/ml/blob/030652489dd489a4705bbf64a12d7e6fa01ca03b/src/adversarial_sbox/phase2g_checkpoint_adapter.py#L125-L159), without importing or training any neural model.

## Confirmed factual accounting — DO NOT confuse the denominator

Original records contain **576** paired A/F trained model-state SHA comparisons:

| Historical checkpoints | A/F curriculum as declared | Trained-model SHA result | Scientific interpretation |
|---|---|---|---|
| Generation **0**, 9 seeds ×16 = **144 pairs** | **Identical** curriculum SHA, same declared original population and T/M model/data seeds | **80 same SHA**, **64 different SHA** | **Only these 64** remain a historical reproducibility anomaly under declared equivalent experiment identity |
| Generations **5, 10, 15**, 9 seeds ×3×16 = **432 pairs** | **Different** adaptive/fixed curriculum SHA | **432 different SHA** | A/F training inputs intentionally diverged; these 432 SHA differences cannot independently establish numerical nondeterminism |

At checkpoint 0 the entire 16-replicate block is **all-or-none by evolution seed**. The five evolution seeds **726011, 726023, 726037, 726087, 726099** have **16/16 matching** trained-state SHA; four evolution seeds **726049, 726061, 726073, 726113** have **0/16 matching**, with zero cross-arm SHA overlap. For **all nine** seed pairs, checkpoint-zero declared curriculum fingerprints, curriculum SHA, population-before and population-after fingerprints, dataset seeds and model seeds agree A/F.

The available historical records contain **only the hashes of the final trained model states**, not the historical raw bytes of the final weight arrays, initial weight arrays or exact constructed training datasets. Equal SHA means highly compelling evidence that final bytes were equal (assuming negligible SHA collision); unequal SHA alone cannot quantify weight distance, float32 ULPs or AUC impact.

## NEW provenance clarification: the historical training receipt itself is ARM-DEPENDENT

**Independent reproduction of `training_receipt_sha256` succeeded for ALL 72 of the original arm/checkpoint records (9 seeds × 4 checkpoints × 2 arms).**

The original source's hash payload explicitly includes `"arm": str(arm)`, `"evolution_seed"`, `"checkpoint_generation"`, `"curriculum_digest_sha256"`, and a 16-entry list of model state SHA/seed metadata. The `arm` field is **separate** from the trained-model state-byte SHA.

**Consequences:**
- **0/36 A-vs-F training-receipt SHA pairs are equal**, even when both arms' 16 model state SHA values are all equal. Therefore simply comparing original `training_receipt_sha256` A/F would yield **36 apparently divergent checkpoints** and is *not a valid neural nondeterminism test*.
- To isolate this built-in naming confound, we independently reconstructed a diagnostic **arm-neutral** receipt by replacing both payload `arm` strings with the same diagnostic marker, without changing any original evidence. **5/36** arm-neutral receipts become identical: precisely the five checkpoint-zero seed pairs with 16/16 equal model state SHA; the remaining 31 pairs differ for either the original 64 model-state anomalies (4 checkpoint-zero seeds) or intentional curriculum differences (27 later seed/checkpoint pairs).
- This is not a flaw in the original receipt implementation: an arm-scoped provenance receipt should encode its arm. It becomes misleading only if used as evidence that model parameters themselves differ. We did NOT change historical receipts or their recorded SHA values.

## NEW source-level environment and original job-log check (2026-09-21)

The original frozen [`phase2g.yml` workflow](https://github.com/Chatnoir01/ml/blob/030652489dd489a4705bbf64a12d7e6fa01ca03b/.github/workflows/phase2g.yml#L68-L100) explicitly pins **Ubuntu 24.04** runner LABEL, **Python 3.12** (actual original logs: 3.12.14) and **NumPy 2.5.3**, but **does not specify** `OPENBLAS_CORETYPE`, thread-count caps, numerical CPU dispatch, actual `threadpoolctl` profile or original dataset/initial weight byte snapshots. Original run job logs sampled for 16 A/F cells report the same hosted Ubuntu 24.04 **image release `ubuntu24/20260907.300`** and NumPy wheel family, but no effective BLAS core/CPU SIMD features. **Same image release is NOT proof of same underlying CPU architecture or runtime numerical kernel.**

Original job provisioning timestamp contrasts provide **no simple scheduling explanation**:

| Evolution seed | Historical first job provisioner gap between A and F | Checkpoint 0 trained state SHA outcome |
|---|---:|---|
| 726049 | ~468.0 sec | **0/16 equal** |
| 726061 | ~493.0 sec | **0/16 equal** |
| 726073 | ~1.1 sec | **0/16 equal** |
| 726113 | ~19.8 sec | **0/16 equal** |
| 726037 (control) | ~0.8 sec | **16/16 equal** |
| 726087 (control) | ~1.9 sec | **16/16 equal** |
| 726023 (control) | ~28.3 sec | **16/16 equal** |

These times are GitHub *runner image provisioning log timestamps*, not proof of first numerical instruction time or CPU identity. In particular, divergent **726073** jobs provisioned only ~1 sec apart, while some matching jobs also provisioned close together. **Time gap alone does not separate the two categories.** Job IDs are visible under the [original scientific run](https://github.com/Chatnoir01/ml/actions/runs/35572084785). No causal BLAS/CPU identification is possible from the sampled logs.

## What the recent Phase 2R controls do—and do not—establish

Synthetic same-host OpenBLAS Haswell-vs-Nehalem interventions (PRs #161, #163–#168) did establish that changing BLAS dispatch can alter float32 intermediate values, Adam gradients and up to 32 epochs of model weight SHA bits, **with very small relative model-vector distances** and generally unchanged synthetic held-out AUC. That is a plausible **mechanism**, not forensic proof of original 2026-09 workers' hardware or the cause of the 64 historic SHA differences. Historic model-state **hashes only** cannot be compared to modern synthetic model vector amplitudes or signed AUC deltas.

**Live open questions:** retrieve genuine historical runner CPU/BLAS profiles, exact original NumPy CPU dispatch and thread controls, or authenticated historical input and initialized-weight bytes if they exist outside the archived Phase 2G sources. If they cannot be recovered, the causal root of **64/144** remains **unresolved** from original evidence. Do not substitute a new simulation for missing historical provenance.

## Artifact integrity and retention

- Original 39-archive preservation snapshot, as retrieved from the current workspace: `phase2g_all_39_original_evidence_20261105.zip` (39 nested source ZIP CRC checked) and `phase2g_all_39_manifest_20261105.json`.
- All 18 A/F source ZIP CRC passed, **18/18 original arm scientific payload SHA reconstructed**, and **72/72 original model-training receipt SHA reconstructed exactly**.
- This audit does **not** re-run a model, overwrite any source ZIP, modify Phase 2G's `phase2g_adaptive_coevolution_not_supported` verdict, update the sealed prospective Phase 2U prediction labels or launch any of Phase 2U's 96 neural trainings.
- Actions original-source artifacts are ephemeral (preservation planning previously noted expiration around **2026-12-20**); the conversation has copies, but independent user-owned storage has not been verified.

**Conclusion:** 36/36 A/F checkpoint comparisons are explainable as receipt identity differences, but only **4 checkpoint-zero seed pairs ×16 = 64 trained-model-state SHA mismatches** remain a legitimate numerical-reproducibility question under declared equal curricula. Training-receipt hashes, later-evolution differences, and timing gaps must not be presented as independent evidence of BLAS causation. **Frozen negative Phase 2G scientific verdict unchanged.**
