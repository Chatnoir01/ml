# TPM post-confirmation attacker workload audit — research only

**Retrospective methodology; the 64-seed holdout has already been observed.**
This project measures actual algorithmic work in our five-arm TPM
implementation; it is **NOT a fresh held-out confirmation, a cryptographic
security argument or an equal-CPU contest**.

## Why this is necessary

The [registered 64-trial confirmation PR #147](https://github.com/Chatnoir01/ml/pull/147)
found:
- 9-candidate cooperative: 30 exact matches out of 64;
- 9 independent geometric attackers: **53/64**;
- 16-branch genetic-style heuristic: 2/64;
- 16 independent geometric attackers: **58/64**.

These only match the number of simultaneous candidate models. A branching
heuristic can construct and score many more candidate objects and need more
updates per step than independent geometric attacks. Performance equality
was never claimed in the original confirmation.

## Strict instrumentation contract

`src/tpm_lab/cost_audit.py` wraps the real `TPM.__init__`,
`TPM.evaluate` and `TPM.update` **during a single synchronous simulation
call only**. It labels the **first two** constructed TPMs as Alice and Bob,
and every later construction as an attacker candidate, including branches
and clones. The original implementations perform all actual work.
All result records are checked against their uninstrumented implementations
in deterministic tests before analyzing costs.

For each arm and trial, measure:

- Number of actual attacker TPM constructions (includes repeated clone
  construction in the branching genetic-style heuristic).
- Number of actual attacker `TPM.evaluate` forward invocations.
- Number of actual attacker `TPM.update` weight-update invocations.
- Number of attempted attacker coordinate writes
  (`inputs_per_unit × number_of_hidden_units_selected_for_update`);
  these are algorithmic edit attempts, **not** distinct changed
  coordinates, CPU instructions or memory writes.
- Separate corresponding honest Alice/Bob counts (sanity gate).
- The exact-match outcome and first legitimate synchronization step
  to ensure instrumentation has not modified any scientific result.

These are code-level *proxies* for work, not equivalent CPU cycles,
optimized operations, clock time, electrical energy, or runtime on
an adversary's actual attack hardware. Patching is deliberately
single-threaded and isolated; no concurrent use is supported.
The constructor ordering is a contract of this particular TPM code.
A future refactor that changes the ordering needs audit changes.

## Dataset / reporting

Use the **original already-seen confirmation seeds**, master seed 971023,
first N = 64 for the full retrospective cost audit. No fresh held-out
inference is possible from them. Python 3.10/3.11/3.12 CI smoke runs
**only 2 trials**. A separate Python 3.11 full audit executes all 64,
asserts agreement with previously published exact-match counts, and
uploads the raw cost JSON.

We report each arm's median and total model method-call costs together
with the method's success count. Do **not** rank the "best attack"
solely by success percentage. A legitimate next prospective experiment
would first freeze an equal-operation/equal-time budget policy, an
actual compute platform, stronger published attack baselines, and a
new independent seed allocation. That new study must not reuse the
64 confirmation seeds as a confirmatory cohort.

## Reproduce

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_tpm_cost_audit.py
python scripts/run_tpm_cost_audit.py --smoke
python scripts/run_tpm_cost_audit.py --full
```

No actual encryption keys, live messages, medical records, private TPM
weights, or secure key-exchange credentials are exported. The toy TPM
has no authentication or independent cryptanalysis and is not connected
to CryptoWall.
