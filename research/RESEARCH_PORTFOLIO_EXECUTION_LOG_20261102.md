# Research closure execution log — 2026-11-02

This log records **real actions performed**, not future work promises. It is part of draft PR #159 (research governance), and does not modify any frozen science or production crypto.

## Completed during the inventory

1. **All 38 previously open draft PRs enumerated** and assigned exactly once to 15 tracks in `RESEARCH_PORTFOLIO_CLOSURE_MANIFEST_20261102.json`. The newly created registry PR #159 is subsequent to this historical baseline and is therefore **not** one of those 38.
2. **Evidence + exit conditions registered** per track and a dependency graph created. A standard-library validator and 18 synthetic tests were written; CI run on the new branch is **NOT YET CONFIRMED**. A passing status must not be asserted until GitHub reports it.
3. **TPM 96 real output audit located and independently cross-checked**. Run [39973978046](https://github.com/Chatnoir01/ml/actions/runs/39973978046) successfully read the original frozen ZIP, verified SHA-256 `b2349d818188f61924edf878044837f422cd5bb5c99b8dd7e08da9869ee5f4bc` and independently recomputed all 96 paired outcomes and three Holm-corrected contrast p-values. The original 96-session study is COMPLETE at toy TPM scope; new attack settings need a **different** study.
4. **66 original GitHub Actions artifact ZIPs retrieved and CRC-checked**, including all 39 Phase 2G artifacts, 2 TPM source/audit ZIPs, 4 incomplete-v1 Phase 2T receipts, 19 Phase 2U source receipts and 2 Phase 2U official panel/replay ZIPs.
5. A downloadable `crypto_research_evidence_bundle_20261102.zip` was created. Its SHA-256 is `1e8ab6d13e8766240228ca9e6b546b1d10462a8ac9dff6ccfc27d4f0a9e1407f`. The bundle contains `manifest.json` and `SHA256SUMS.txt` with individual ZIP fingerprints. It is available in the generating ChatGPT conversation **ONLY**; it was NOT uploaded to GitHub or persistent third-party storage. User must preserve an independent copy.
6. **Three real frozen artifacts rechecked directly** from the downloaded ZIPs:
   - Phase 2G: aggregate verdict `phase2g_adaptive_coevolution_not_supported`, 2880 trainings, aggregate SHA256 `1df1812bc58e088c6a639d7ccbb94e1f3a02feb0ebd9f8b04e4ac81b1ea983d2`.
   - TPM: independent auditor validated original 96 trials; exact adjusted p-values 0.0390625 / 0.0001220703125 / 0.000091552734375.
   - Phase 2U: officially admitted 19-source/12-candidate panel, original SHA256 `512dd21d01617944047fd4e6f6ec2ae09daa68bc76d808837527a384148914ef`, SHA3 fingerprints on all 12 S-Boxes match, and `new_neural_trainings=0`.
7. **Specialized RAVEN state-model test workflow explicitly activated** through a safe test-only change to `.github/workflows/raven-research.yml` in [PR #155](https://github.com/Chatnoir01/ml/pull/155). [GitHub run 41483812755](https://github.com/Chatnoir01/ml/actions/runs/41483812755) accepted and was QUEUED when last checked. This is not a PASS yet.

## Confirmed blockers (do NOT merge past these)

- **Phase 2U:** no sealed source-bound prediction receipt and no neural outcomes. Freeze source-bound classical ranking before independent neural labels; resolve Phase 2R input/model-state anomaly first.
- **Phase 2R:** synthetic input preflight passed, but actual A/F checkpoint-zero provenance mismatch origin remains unknown on 4/9 reported seeds; no new claim of adaptive superiority.
- **Secure Core:** five trust-boundary tests failed in latest checked [PR #154](https://github.com/Chatnoir01/ml/pull/154) CI. Neither tests nor code may be weakened to treat fabricated software pVM claims as authenticated hardware proof.
- **RAVEN:** Python specialized suite is queued, not yet validated; crash-durable witnesses and multi-epoch quorum safety do not exist in production form.
- **Artifacts:** long-term external copy of the 66-artifact bundle is still an **action required**. Old Phase 2G ZIPs expire 2026-12-20 UTC; original TPM source/audit ZIPs expire 2026-12-22 UTC.

## Immediate continuation order

1. Confirm RAVEN specialized CI run 41483812755 and registry PR #159 CI; fix genuine test defects without changing frozen research claims.
2. Ensure evidence bundle has been independently stored, SHA verified, and its provenance reviewed.
3. Lock Phase 2U prediction receipt before any neural training.
4. Resolve Phase 2R reproducibility with a prospective actual model-state replay.
5. Correct Secure Core's five trust-boundary regressions safely.
6. Close remaining protocol demonstrations and negative result drafts administratively; only then plan a dependency-respecting integration.

**No unrelated research PRs were merged, closed, deleted or rebased by this log.**

## Addendum — later actions on 2026-11-02 (after the 38-PR baseline snapshot)

8. **RAVEN-002–006 specialized CI confirmed:** run [41483812755](https://github.com/Chatnoir01/ml/actions/runs/41483812755) completed SUCCESS on PR #155 head `462676c80e5ced1cbf8a2c53bd1c99b6c9f46226`; Phase 0 [41483812585](https://github.com/Chatnoir01/ml/actions/runs/41483812585) passed across Python 3.10/3.11/3.12. This validates the current single-transition model only; durability and epochs remain unproven.
9. **Phase 2U classical prediction precommit completed:** run [41539098859](https://github.com/Chatnoir01/ml/actions/runs/41539098859) SUCCESS; source panel SHA `512dd21d01617944047fd4e6f6ec2ae09daa68bc76d808837527a384148914ef`, classical prediction SHA `cd4bfbc9736ced13bdcf95c06f156d4244fbbdde65b05c51fb4e7958a21a30f4`, artifact #13185193738 ZIP SHA `5084090f27fd225af5ae763055f022c4a83582a951fff1c73a4bb9d042551cd1`. Original JSON canonical digest and ranking independently checked from downloaded bytes. ZERO neural outcomes; research report committed on PR #158.
10. **RAVEN-007 new post-snapshot draft [PR #160](https://github.com/Chatnoir01/ml/pull/160):** separate crash-only fsync-before-sign journal with injected crash/restart tests and an explicit malicious snapshot rollback negative control. Initial RAVEN-007 CI queued at log creation; **NOT YET VALIDATED**. This new draft is not part of the original fixed 38-PR snapshot and must be included in the next dated inventory version.
11. Registry PR #159's manifest and human-readable guide updated to mark the Phase 2U precommit complete without falsely claiming neural generalization. The 38-PR historical baseline count remains immutable; new PRs #159/#160 need future dated snapshot.

**No Phase 2U neural training occurred during these actions. No research PR was merged into main.**
