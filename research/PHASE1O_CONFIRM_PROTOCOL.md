# Phase 1O — blinded confirmation protocol

## Status

This protocol is frozen after the Phase-1O development PASS and before any reserved Phase-1O confirmation seed is executed. Public preregistration is recorded in issues #55 and #56.

## Frozen base

- development merge on `main`: `5d62d4ef0d6cfcaeb2599d0ad0aa6c31e5a8fc88`
- confirmation branch: `research/phase1o-confirmation`
- development mechanism, budgets, hard thresholds and ITO tolerance are unchanged
- no development seed may be reused
- no confirmation seed may be used for tuning
- Neural Oracle remains blocked throughout confirmation

## Reserved confirmation seeds

Exactly nine seeds are authorized, and only after the confirmation workflow is separately execution-locked:

`2609, 2617, 2621, 2633, 2647, 2657, 2663, 2671, 2683`

## Frozen arms

Arm A: Phase-1O multi-hotspot Walsh plateau proposals, anchored on maximum-DU DDT hotspots, with the frozen staged ITO-aware Pareto/NSGA-II selection policy.

Arm B: frozen Phase-1N single-worst-Walsh proposal mechanism with the identical staged selection policy.

Arm C: historical `feasibility_first` GA comparator, descriptive only.

No scalar fitness weighting is introduced. No candidate-wide hidden prescoring is allowed in proposal generation.

## Exact budget

Each arm receives exactly 340 unique full classical CryptoShield evaluations per confirmation seed. Rejected inspected proposals are charged. Cached reads do not double-charge. ITO evaluations are counted separately.

Frozen geometry remains population 20, shortlist 8, parent count 4, 4 proposals per parent, 16 proposals per generation, 20 generations.

## Frozen JOINT target

A terminal candidate is JOINT-target if all are true:

- differential uniformity <= 8
- nonlinearity >= 100
- maximum absolute linear correlation <= 64
- algebraic degree >= 6

The broader historical hard-admissibility/SAC semantics remain unchanged.

## Confirmation criteria

Every condition below is mandatory:

1. Aggregate terminal JOINT count in Arm A is strictly greater than Arm B.
2. Arm A reaches at least one JOINT terminal candidate on at least 5 of 9 confirmation seeds.
3. DU bridge non-regression: seeds with a terminal DU<=8 candidate in A are at least those in B, and paired best-DU wins are at least paired losses.
4. Median terminal best DU(A) <= median terminal best DU(B).
5. Aggregate protected-classical terminal count (NL>=100, max|LAT|<=64, degree>=6) in A >= B.
6. Median minimum terminal ITO(A) <= median minimum terminal ITO(B) + 0.02.
7. A/B/C each consume exactly 340 unique full classical evaluations on every seed.
8. A/B/C share the same initial population digest within each seed.
9. Fixed-seed canonical scientific payloads are identical on deterministic rerun.
10. Executed seeds match exactly the nine reserved confirmation seeds, and no development seed is reused.
11. Neural Oracle never executes.

Verdict is `phase1o_confirm_pass` only if all eleven checks pass; otherwise `phase1o_confirm_fail`.

## Classical Gate 1 transition

The repository-level rule is preregistered in issue #56. Global Classical Gate 1 becomes GREEN only if the frozen confirmation returns `phase1o_confirm_pass`.

A GREEN Classical Gate 1 means only that the classical search mechanism has confirmatory evidence of reproducibly generating fresh bijective 8x8 candidates satisfying the frozen JOINT target under the matched budget and provenance checks. It moves the Neural Oracle from blocked to **Phase-2 engineering/experimental eligibility**.

It does not establish AES superiority, proof of security, deployment readiness, physical side-channel resistance, validity of ITO as a physical leakage model, neural resistance, or closed-loop GA↔NN success.

If confirmation fails, Gate 1 remains RED, the failure is preserved, the reserved seeds are never tuned against in place, and Neural Oracle scoring/evolution remains blocked.