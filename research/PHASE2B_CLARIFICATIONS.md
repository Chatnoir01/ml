# Phase 2B — Pre-execution clarifications

Public clarification: issue #102  
Related preregistration: issue #97  
Ex-ante budget amendment: issue #101

## Status

These semantics were frozen **before any Phase-2B scientific neural-pressure execution**. They resolve wording ambiguity only; they do not change the hypothesis, arms, thresholds, evolution seeds, Oracle regime, held-out Block V, or compute budgets.

## Exact paired sign test

For the primary paired Arm-O versus Arm-C Block-V comparison:

- a positive difference `C - O > 0` is an Oracle win;
- a negative difference `C - O < 0` is an Oracle loss;
- an exact zero difference is a tie;
- exact ties are excluded from the binomial sign-test denominator;
- exact ties do not count as wins toward the frozen `8/9` O>C requirement.

The same win semantics apply to the frozen `6/9` O>S specificity requirement: exact O=S ties are not wins.

## Classical non-degradation verdict semantics

Classical non-degradation is a substantive Phase-2B support gate, not a provenance prerequisite.

If provenance, budgets, seed isolation, receipts and execution-lock requirements are valid but Arm O degrades any protected classical component relative to Arm C, the correct result is:

`phase2b_oracle_pressure_not_supported`

The verdict:

`phase2b_inconclusive_prerequisites`

is reserved for invalid or missing provenance, budget violations, seed overlap, held-out leakage, receipt failure, execution-lock violation, or inability to evaluate the required classical gate.
