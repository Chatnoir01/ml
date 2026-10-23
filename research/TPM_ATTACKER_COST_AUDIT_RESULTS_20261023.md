# TPM 64-trial attacker-cost audit — verified source-run receipt (2026-10-23)

**Research only. Retrospective, already-observed hold-out seeds.**
This report was added **after the original protocol and result were frozen**;
it cannot be used as a second independent confirmation of success rates,
a cryptographic attack standard, or any secure-key assurance.

## GitHub provenance

- Stacked draft [PR #148](https://github.com/Chatnoir01/ml/pull/148).
- Verified source SHA: `7a9a682a45b8ef2ec5819b1c68b12e08bb117882`.
- Exact [workflow 39936890271](https://github.com/Chatnoir01/ml/actions/runs/39936890271): **SUCCESS**, including independent 64-seed cost audit and smoke tests on Python **3.10, 3.11, 3.12**.
- `cost-audit-64-retrospective` job ID `120358511172`: **SUCCESS**.
- Raw cost report artifact `tpm-64-retrospective-attacker-costs` ID `12494757690`; archive SHA-256 `85be3ae4551ebe734dcc6049859debb88c35b7aba8d333c33f25a65e274ab6ca`. Artifact retained by GitHub until approximately **2026-12-22**.
- Generic Phase 0 CI also **SUCCESS** on exact source SHA (run `39936890121`); TPM core suite likewise **SUCCESS** (run `39936890205`).
- These are direct job-log receipts; the source of exact row-level data is the GitHub artifact.

## Verified source outcomes (unchanged)

The instrumentation verified **exactly the original held-out 64-trial success counts**:
cooperative majority 9 = **30/64**, independent geometric 9 = **53/64**,
genetic-style 16 = **2/64**, independent geometric 16 = **58/64**.
The preserved attack outcomes show the instrumentation itself did not
change the protocol state transitions in the tested code.

### Real algorithmic workload from GitHub logs

| Arm | At-least-one exact-weight match / 64 | Total attacker TPM evaluations, 64 trials | Median attacker TPM object constructions / trial | Median attacker TPM updates / trial | Median attempted attacker coordinate writes / trial |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cooperative majority, 9 | 30 | 31,140 | 9 | 445.5 | 5,400 |
| Independent geometric, 9 | **53** | 31,140 | 9 | 445.5 | 5,544 |
| Genetic-style branching, 16 | 2 | 55,360 | **1,601** | **1,585** | **18,664** |
| Independent geometric, 16 | **58** | 55,360 | 16 | 792 | 9,984 |

**Key distinctions:**

- For each candidate-count-matched contrast, forward `TPM.evaluate()`
  invocation totals were **identical**: 31,140 for both 9-candidate arms
  and 55,360 for both 16-candidate arms. This is a meaningful **equal
  counted forward passes** comparison in this *specific* code.
- The genetic-style branch nevertheless constructed **1,601** objects
  per median trial, whereas geometric 16 constructed **16**.
  Candidate cloning/selection overhead and update invocations differ;
  **forward-pass equality is NOT equal CPU/memory/energy**.
- Cooperative and geometric arms also execute different Python majority/
  sorting/control logic that the TPM invocation counters do not measure.
  A direct wall-clock or optimized equal-hardware benchmark is still absent.
- Counts are medians over trials except the column explicitly labeled
  total, and are **real instrumented function call counts**, not assumed
  theoretical asymptotics.
- The 16-candidate genetic heuristic is a deliberately simplified
  *local-field* beam, not a reviewed reproduction of the strongest
  published genetic attack. Its low success is specific to this
  implementation and tested finite-size TPM.
- Exact private state matches at the legitimate first-synchronization
  instant are assessed with a **privileged simulation-only equality oracle**.
  Real remote parties cannot rely on that oracle or derive assured secret
  keys from the model.
- Post-hoc cost inspection cannot transform the 64-seed cohort into
  a new hold-out. Further claims require a **new reserved independent
  seed set** and full cost contract preregistration.

## Security decision

**Do not enable TPM key exchange in CryptoWall.** The studied toy TPM
was vulnerable at high rates to independent geometric attackers, and
the work proxy does not establish protection against stronger active,
genetic, quantum, side-channel or offline attacks. Do not use Python's
noncryptographic RNG or experimental weights for user encryption. Keep
standards-based HPKE/AEAD research separate.
