# Phase 1E — spectral/DDT-guided frontier continuation result

Status: **development did not establish advancement; confirmation not executed; global Gate 1 remains RED**.

## Scope

Phase 1E was a warm-start operator-mechanism experiment, not global Gate-1 evidence.
It asked whether hotspot-guided permutation moves could escape the historically
reproduced `NL=98 / DU=8 / max-correlation=60` plateau while retaining the
structural frontier.

The development protocol was preregistered before execution in
`research/PHASE1E_DEV_PROTOCOL.md`.

## Frozen experimental receipt

- GitHub Actions run: `33464306187`
- frozen experimental HEAD: `6b4294a03bfc11b97e354f31384b03bbae662178`
- Python: `3.12`
- development seeds: `907, 911, 919, 929, 937`
- per completed configuration and seed: `480` guided full classical evaluations
  and `480` matched unguided adaptive evaluations
- workflow timeout: `45` minutes per matrix job
- reserved confirmation seeds: `1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051`

The run reproduced the same historical Phase-1B warm start through the existing
Phase-1D receipt gate before performing development comparisons.

## Completed configuration results

Four of the five preregistered configurations completed successfully.

| configuration | guided target `NL>=100 & DU<=8` | guided admissible | guided / unguided / ties | median guided `NL / DU / max-corr` | artifact receipt |
|---|---:|---:|---:|---:|---|
| `spectral32_s1` | `0/5` | `0/5` | `0 / 0 / 5` | `98 / 8 / 60` | ID `9784446617`, `sha256:2e5deb0d8dd6b02e2b4bca7609c54b852963da6542fb0cf4c060c0dfc1e0aec2` |
| `spectral96_s1` | `0/5` | `0/5` | `0 / 0 / 5` | `98 / 8 / 60` | ID `9784458406`, `sha256:677d61b46b01e00fa38a811bbc705b5f88a1533b0ffd61d079288a0b82fdc384` |
| `hybrid64_s1` | `0/5` | `0/5` | `0 / 0 / 5` | `98 / 8 / 60` | ID `9784452502`, `sha256:5bd640dd95b359b152906b9b9f1a3957447f1a2cfd6b447aa8e3b41b88264bdc` |
| `hybrid64_s2` | `0/5` | `0/5` | `0 / 1 / 4` | `98 / 8 / 60` | ID `9784452990`, `sha256:a838b87d07438b42ef19e579c74d61c80bdd8c6f38adec00b1cf18e51c5d6a35` |

For all four completed configurations, the matched unguided comparator also had
`0/5` target successes and `0/5` hard-admissible runs. Increasing spectral
proposal count from 32 to 96 did not change the observed endpoint medians, and
adding a second hybrid swap did not improve the target outcome.

## `ddt64_s1` is censored, not scored as zero

The fifth preregistered configuration, `ddt64_s1`, did **not** complete. Its job
started the frozen command with the same five development seeds and 480-evaluation
budget, but GitHub Actions cancelled the running process at the workflow's
predeclared `timeout-minutes: 45` limit.

- job ID: `99720865343`
- computation started: `2026-09-01T02:55:09Z`
- cancellation recorded: `2026-09-01T03:40:15Z`
- conclusion: `cancelled`
- no result JSON was written
- artifact upload failed because `phase1e-ddt64_s1.json` did not exist

Therefore `ddt64_s1` is treated as **right-censored by the frozen runtime limit**.
It is not assigned `0/5`, and no claim is made about what its final metric outcome
would have been if given additional runtime.

The job is deliberately **not rerun** after observing the other development
results. A rerun could consume additional candidate evaluations after observation
and would weaken the preregistered matched-budget interpretation.

## Decision under the preregistered protocol

The protocol allowed confirmation only after development established at least one
guided configuration producing `NL>=100` with `DU<=8` on a development seed.

That positive prerequisite was **not established**:

- the four completed guided configurations produced zero such successes across
  20 completed guided seed-runs;
- the fifth configuration is censored and provides no completed positive result;
- no completed guided configuration produced a hard-admissible candidate.

Accordingly:

- **Phase 1E confirmation is not executed**;
- confirmation seeds `1009, 1013, 1019, 1021, 1031, 1033, 1039, 1049, 1051`
  remain **UNUSED**;
- no confirmation acceptance rule or confirmation workflow is created;
- global **Gate 1 remains RED**;
- the neural-oracle phase remains **BLOCKED**.

This is intentionally more conservative than claiming the literal stop-rule
antecedent ("no guided configuration succeeds") was fully observed for all five
configurations: `ddt64_s1` is censored, so the scientifically accurate statement
is that Phase 1E **did not establish the positive prerequisite required to
advance**.

## Engineering validation after the frozen run

A compatibility regression in `experiment_seeds.py` was found after the frozen
experimental run: an older test still imported the historical symbol
`USED_BEFORE_V2`. The alias was restored without changing Phase-1E search logic,
configuration, seeds, or frozen evidence.

At commit `5840cf6bb911e4cb8d15ce06d1b7bcf5f9fb5f61`, Phase 0 CI passed on Python
`3.10`, `3.11`, and `3.12`.

The experimental evidence remains tied to the earlier frozen HEAD
`6b4294a03bfc11b97e354f31384b03bbae662178`.

## Scientific interpretation

The completed spectral and hybrid arms reinforce the Phase-1D observation that
the verified `DU=8` warm-start frontier is easy to preserve but the `NL=98`
plateau is difficult to cross with local output-permutation moves. Explicitly
targeting the currently worst Walsh component, increasing spectral proposal
oversampling, and combining Walsh/DDT guidance did not improve the completed
endpoint medians.

The DDT-only arm also exposed a practical limitation: recomputing and exploiting
DDT hotspots at this granularity is substantially more expensive and failed to
complete within the frozen 45-minute execution envelope. That runtime outcome is
useful negative engineering evidence, but it is not a cryptographic metric
failure.

A future classical phase should therefore use a genuinely different search
representation or move family rather than merely extending Phase-1E runtime,
increasing pair-proposal count, or retuning swap counts after observing these
results. Fresh development and confirmation seeds must again be registered before
execution. Any future claim relevant to global Gate 1 must also return to a
fresh-population, equal-budget validation arm rather than relying only on the
historical warm start.
