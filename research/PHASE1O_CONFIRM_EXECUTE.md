# Phase 1O blinded confirmation authorization

AUTHORIZED_PHASE1O_CONFIRMATION

The confirmation protocol, Gate-1 transition rule, implementation and workflow were frozen and inspected before any reserved confirmation seed execution.

- Frozen pre-execution confirmation head: `e66a24809afe792aa325b9825d7c57c5827672e5`
- Public confirmation preregistration: issue #55
- Classical Gate 1 transition rule: issue #56
- Confirmation seeds: 2609, 2617, 2621, 2633, 2647, 2657, 2663, 2671, 2683
- Required JOINT seed successes: >=5/9
- Exact classical budget: 340 per arm/seed
- ITO non-inferiority tolerance: +0.02
- Same initial population within seed: required
- deterministic rerun: required
- Neural Oracle: blocked throughout confirmation
- Phase 0 CI on locked head: Python 3.10/3.11/3.12 GREEN
- Historical Phase 1 benchmark on locked head: GREEN
- PR #57 changed-file set before authorization: confirmation workflow, confirmation protocol, confirmation wrapper, confirmation tests only

This commit authorizes only the frozen blinded Phase-1O confirmation run. No parameter or criterion tuning is authorized after results.