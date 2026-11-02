# Urgent evidence retention — 2026-11-02

**Preservation does not mean scientific validation, cryptographic originality, or production security.** This research artifact inventory was prepared BEFORE the planned cross-branch consolidation. It is a separate dated snapshot, not a change to any frozen historical result.

## Artifacts recovered into one external conversation ZIP

A consolidated ZIP file was created from **66 original GitHub Actions artifact ZIP files** downloaded through the GitHub connector. Every source ZIP passed the ZIP CRC test; the bundle contains an individual SHA-256 entry for each original ZIP in `manifest.json` and `SHA256SUMS.txt`.

- Bundle filename: `crypto_research_evidence_bundle_20261102.zip`
- Bundle total size: **7,035,916 bytes**
- Bundle SHA-256: **`1e8ab6d13e8766240228ca9e6b546b1d10462a8ac9dff6ccfc27d4f0a9e1407f`**
- Bundle content: **39 Phase 2G source ZIPs**, **2 TPM source/audit ZIPs**, **4 Phase 2T-v1 blocked-source ZIPs**, **19 Phase 2U source ZIPs**, **2 Phase 2U admission/replay ZIPs**.

**IMPORTANT:** The archive is available as a downloadable file in the conversation where it was generated. It has **NOT** been uploaded to this repository or another permanent external store. Whoever maintains the project must preserve an independent copy and check the archive SHA-256 before using it as evidence.

## Critical expiry deadlines verified from GitHub Actions

| Branch / source | Workflow run | Critical artifact IDs | Last advertised expiry (UTC) | Required preservation |
|---|---:|---|---|---|
| Phase 2G frozen adaptive GA↔NN (36 arm ZIPs + summary / heldout / freeze) | [35572084785](https://github.com/Chatnoir01/ml/actions/runs/35572084785) | **39 artifacts**; example summary `10627326790`, heldout `10626982348`, terminal freeze `10626482818` | **2026-12-20 07:15:10** | Retain all 39 raw ZIPs and arm seeds; do not relabel negative result |
| TPM prospective 96 sessions | [39971905846](https://github.com/Chatnoir01/ml/actions/runs/39971905846) | `12510291806` | **2026-12-22 14:52:27** | Retain raw 96-trial report; original audit checked ZIP SHA `b2349d818188f61924edf878044837f422cd5bb5c99b8dd7e08da9869ee5f4bc` |
| TPM real output-only independent audit | [39973978046](https://github.com/Chatnoir01/ml/actions/runs/39973978046) | `12510173703` | **2026-12-22 15:07:01** | Retain original independent audit JSON: checked all 96 trials and three scale contrasts |
| Phase 2U admitted 12-candidate source panel | [41460802079](https://github.com/Chatnoir01/ml/actions/runs/41460802079) | `13149717470` | **2027-01-31 14:19:12** | Retain full 19-seed admission receipt before any Phase 2U neural labels |
| Phase 2U seed-41003 full independent source replay | [41460158043](https://github.com/Chatnoir01/ml/actions/runs/41460158043) | `13149417447` | **2027-01-01 14:32:00** | Retain independently regenerated 340-evaluation source receipt |

Original Phase 2T-v1 source artifacts retained in this bundle: `13109089315`, `13109483030`, `13109542695`, `13110002017`. The missing seed `31013` has **NO successful source receipt** because the versioned generator crashed; preserve that fact rather than inventing an archive.

Original Phase 2U source-run artifacts retained in this bundle: `13113599556`, `13136426780`, `13134649849`, `13136142649`, `13136730329`, `13135489405`, `13137865391`, `13137606727`, `13137216809`, `13140663528`, `13140843593`, `13140713382`, `13140388590`, `13142727617`, `13141899471`, `13142147789`, `13141968078`, `13147734812`, `13149120287`. The twelfth success was at seed `41143`; source selection stops there.

## Verified TPM result status

The original [96-session independent audit](https://github.com/Chatnoir01/ml/actions/runs/39973978046) **already passed on the actual original frozen 96-trial JSON**, contrary to an earlier tentative statement that only synthetic controls had run. Adjusted p-values and exact successful attacks reproduced:
- N8/L2 cooperative 21/32 vs geometric 28/32, adjusted p=0.0390625.
- N16/L3 cooperative 10/32 vs geometric 25/32, adjusted p=0.0001220703125.
- N32/L4 cooperative 9/32 vs geometric 25/32, adjusted p=0.000091552734375.

The 96-trial experiment is scientifically closed *at its original toy-model scope*. Any further attacks must be a new preregistered study; no claim of secure neural key exchange.

## Before deletion, merges or archival migration

1. Independently store **all original ZIPs and their SHA-256** beyond GitHub Actions retention; verify SHA after copy.
2. Record a canonical mapping of source run ID / job ID / source SHA / artifact ID / source seed / version / Python dependencies.
3. Preserve raw negative findings and source failures with the same priority as positive outcomes.
4. Include original README/protocol source at its frozen commit, not only a current mutable branch name.
5. Never interpret mere successful CI or a SHA checksum as proof of experimental independence.
6. Do not delete original drafts or close workstreams based on this inventory alone.

This is an evidence preservation snapshot, NOT a release or a merge plan authorizing actions.
