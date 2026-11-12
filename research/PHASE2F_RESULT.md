# Phase 2F — Frozen result and execution record

## Final status

**EXECUTED / PREREQUISITES PASSED / VALID NEGATIVE: `phase2f_minimal_band_pressure_not_supported`.**

This is the outcome of the frozen preregistered experiment. It is not a workflow failure or a provenance-inconclusive result. No seed, threshold, band width, arm, budget, or support criterion is changed here. The original protocol remains preserved as the preregistration record; its `PRE-MARKER / NOT EXECUTED` status describes the pre-execution stage and is superseded for current status by this post-execution record.

## Provenance

- Governance: preregistration issue [#115](https://github.com/Chatnoir01/ml/issues/115); execution lock issue [#116](https://github.com/Chatnoir01/ml/issues/116).
- Scientific execution head: `fbfdb0c2fde6835aa85be39e859316378b457850`.
- Authorization marker: [`PHASE2F_EXECUTE.md`](PHASE2F_EXECUTE.md), exact token `AUTHORIZED_PHASE2F_MINIMAL_BAND_EXPERIMENT`.
- Scientific workflow: [Phase 2F Minimal Band Pressure, run 34316686692](https://github.com/Chatnoir01/ml/actions/runs/34316686692), reported conclusion **SUCCESS**.
- Merged implementation/execution PR: [#117](https://github.com/Chatnoir01/ml/pull/117), merged 2026-09-09.
- Final summary artifact SHA-256, as reported by PR #117: `64ded6a8e8418bed72d1382ddecf055aaed3f27ef09a2f6d203f98522f4a8f48` (`sha256:` prefix in PR record).
- Frozen neural budget: **19,008 trainings**.

The PR record reports completion of all 36 arm runs, a freeze over all 36 terminals, 36 held-out Block-X validations, and deterministic aggregation. It says terminal freezing and aggregation were each repeated with byte-identical output. The Phase 2F workflow uploads artifacts with 90-day retention; preserve any still-available original artifact ZIPs and their checksums in durable storage rather than relying on Actions retention alone.

## Frozen verdict and gates

The preregistered verdict is:

`phase2f_minimal_band_pressure_not_supported`

The prerequisites passed. The seven support conditions were not jointly satisfied:

| Preregistered gate | Result |
|---|---|
| Real cross-key mechanism activity on at least 6/9 seeds | PASS — 7/9 |
| B1 beats O0 on at least 8/9 seeds | FAIL — 3/9 |
| One-sided exact paired sign test, `p < 0.05` | FAIL — `p = 0.7734375` |
| Mean `O0 - B1` reduction at least 0.02 | FAIL — `-0.0061987` |
| Classical componentwise non-degradation versus C | PASS |
| B1 beats SB1 on at least 6/9 seeds | FAIL — 5/9 |
| Mean B1 endpoint strictly below mean SB1 endpoint | PASS |

B1 versus O0 outcomes were 3 wins, 4 losses, and 2 ties. Because these are valid prerequisites with failed support gates, the conclusion is a valid negative for this exact minimal-band protocol—not `phase2f_inconclusive_prerequisites`.

## Scope and interpretation

Phase 2F tested one-way, frozen-procedure neural guidance inside a narrow, preregistered classical neighborhood in the educational ToySPN setting. It does not establish that all neural guidance methods fail, nor does it test adaptive bidirectional co-evolution. It provides no claim about AES or other deployed ciphers, operational key recovery, physical side channels, production security, or deployment readiness.

## Protocol / implementation references

- [Frozen protocol](PHASE2F_PROTOCOL.md) — preserve its scientific rules and thresholds unchanged.
- [Authorization marker](PHASE2F_EXECUTE.md).
- Implementation: `src/adversarial_sbox/phase2f_runner.py`, `phase2f_aggregate.py`, `phase2f_terminal_freeze.py`, and related invariant/provenance modules.
- [Scientific workflow](../.github/workflows/phase2f.yml) and [pre-marker qualification workflow](../.github/workflows/phase2f-qualification.yml).
- [PR #117](https://github.com/Chatnoir01/ml/pull/117) records the final run and gate values; [Actions run 34316686692](https://github.com/Chatnoir01/ml/actions/runs/34316686692) is the workflow provenance link.
