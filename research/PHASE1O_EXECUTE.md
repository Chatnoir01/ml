# Phase 1O scientific execution authorization

AUTHORIZED_PHASE1O_SCIENTIFIC_RUN

Engineering/preregistration lock inspected before execution.

- Frozen pre-execution head: `f29149ada450becb9b15285546581128a5ad183c`
- Phase 0 CI on locked head: Python 3.10/3.11/3.12 GREEN
- Historical Phase 1 benchmark on locked head: GREEN
- PR #54 changed-file set inspected: workflow, protocol, seed registry, Phase-1O engine, Phase-1O tests only
- Preregistration issues: #49-#53
- Development seeds: 2503, 2521, 2531, 2539, 2543
- Reserved confirmation seeds remain quarantined
- Exact classical budget: 340 evaluations per arm/seed
- Neural Oracle remains blocked

This commit authorizes only the frozen Phase-1O development run. No parameter tuning is authorized after results.