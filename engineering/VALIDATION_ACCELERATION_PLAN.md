# Validation acceleration — Secure Core Mobile + cryptographic research

**Status:** Engineering workflow proposal, not a claim of cryptographic assurance.
**Scope:** `Chatnoir01/ml`; no alteration of preregistered Phase 2G experiments,
frozen receipts, held-out evaluations, or their workflow authorisation gates.

## The measured bottleneck

Observed GitHub Actions activity on 2026-10-23 included many Phase 0 CI runs
created within seconds for successive commits on the Phase 2R branch. Full
Phase 0 jobs were still in progress well after individual Secure Core CI jobs
completed. Multiple redundant Python 3.10/3.11/3.12 matrices were consuming
capacity. These observations do **not** by themselves establish the actual
wall-clock reduction obtained from any optimisation.

## Changes included in this PR

1. The generic **Phase 0 CI** now applies GitHub Actions concurrency to the
   current workflow + trigger type + pull request number (or push ref).
   Superseded runs are cancelled after a newer commit on the same PR/ref.
   This **does not cancel a separate PR, a different push ref, or any of the
   preregistered scientific experiments**. The most recent code still has to
   pass the complete Python 3.10, 3.11 and 3.12 test matrix.
2. **Phase 1 development benchmark** receives the same latest-commit-only
   policy, while retaining its matched-budget seeds and artifact upload.
3. Cache pip package downloads using `setup-python` + `pyproject.toml`
   as the dependency cache key. Cache reuse is a speed optimisation, **not
   dependency locking, trust evidence, or scientific reproducibility**.
4. Stop upgrading `pip` unconditionally inside Phase 0 CI. Package versions
   remain resolved from the project's existing dependency constraints.
   Exact reproducibility will require an independently pinned lockfile.

No test was removed, no Python version was dropped, and no permission was
expanded. The specialised Secure Core, 2H and 2R workflows are unchanged.

## Target test lanes (follow-up implementation, not in this PR)

| Lane | Trigger | Required evidence | Release authority |
| --- | --- | --- | --- |
| Fast feedback | each code change | syntax/import, target unit and negative tests, no network credentials | blocks PR review on failure |
| Integration | latest PR commit + before merge | full Python 3.10/3.11/3.12, fuzz/property and platform-neutral boundary checks | required pre-merge |
| Frozen research | preregistered experiment, explicit execution marker | hashes, fixed seed/dataset registry, blind evaluation, full deterministic receipts | **scientific gate only** |
| Native Android | pinned Android API/ABI + supported device | Keystore/StrongBox status, attestation chain, AuthGraph/Secretkeeper session, negative controls | device- and build-specific gate |
| Hostile-host | separately approved attack campaign on supported pVM | compromised host cannot trigger forbidden key operation under specified adversary | only lane allowed to promote hardware isolation claim |

### Secure Core test priorities

**P0 — Fail-closed security invariants:** AES-GCM per-key IV reuse, request
and response key separation, authenticated sequence and replay, rollback,
malformed CBOR/COSE, unauthorized signing and plaintext/key exfiltration.
A failing negative test blocks all higher-security assertions.

**P1 — Native integration:** pin target AOSP revision and HAL/AVF/Secretkeeper
capability matrix; maintain a device ledger with OS build, AVF/pKVM support,
auth-chain trust profile, test results and hardware artefact hashes.
`UNSUPPORTED` must never be converted into `PASS`.

**P2 — Real-device hostile-host trials:** require actual threat-model evidence,
hardware-specific provenance and independent replay. A green Python job
alone cannot promote SCM-I10 or prove protection against root compromise.

### S-Box / model research priorities

**R0 — Freeze integrity:** repository source commit, exact fixture bytes,
hashes, T/M seeds, independent panel registry and immutable experimental
protocols must remain verifiable.

**R1 — Phase 2R reproducibility:** investigate the 4/9 checkpoint-0 mismatch
only through a separate approved experiment with exact dataset,
initialisation and model-state bytes plus pinned CPU/BLAS/thread settings.
Do not replay missing model weights after seeing an outcome.

**R2 — Neural training budgets:** keep preregistered compute/seed counts
separate from CI. Do not rerun costly GA/NN experiments on every code push.
Report negative results; never lower support thresholds post-hoc.

## Next measurable objectives

Record **per workflow and job**, over an initial baseline and after the
change: queue delay (created to started), execution duration, number of runs
cancelled as superseded, runs per merged PR, successful latest-head checks,
and number of safety regressions escaping fast feedback.

Evaluate time/cost only after collecting paired, comparable data. Do not
promise an arbitrary 2× or 10× improvement from concurrency/caching alone.

## Merge acceptance

- The workflow YAML is valid and preserves all existing branch filters,
  Python versions, test commands, benchmark seeds and artifact uploads.
- A PR update generates a fresh full check while superseding only the
  older check for that same PR/ref/event.
- A separate PR and all frozen experiment workflows run independently.
- No policy that deletes old scientific artifacts or makes simulated
  evidence look hardware-backed is introduced.
