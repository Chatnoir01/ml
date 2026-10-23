# TPM same-runner wall-time audit — retrospective design (2026-10-23)

**Research only; no production TPM key agreement. No new confirmation seeds.**
The 64 public experiment outcomes were already observed in PR #147.
This is a **retrospective performance audit** stacked on #148
(algorithmic operation counts).

## Evidence motivating this benchmark

The exact [GitHub run 39936890271](https://github.com/Chatnoir01/ml/actions/runs/39936890271)
confirmed identical held-out attacker exact-state results
`ensemble9=30/64`, `geometric9=53/64`,
`genetic16=2/64`, `geometric16=58/64`.
The model forward evaluation counts were exactly matched *within each
candidate-count contrast*: 31,140 across 9-candidate arms, and 55,360
across 16-candidate arms, but genetic branching constructed
~1,601 TPM objects in a typical trial versus 16 for geometric.

## Single-machine timing protocol

- Replay only the frozen 64 already-observed trial seeds
  (master seed 971023, K=3,N=8,L=2), exactly once per repetition.
- Run **two repetitions per trial and attacker arm**. Each trial
  contains 4 attack arms; all share identical Alice/Bob initial states,
  public input stream and observed synchronized state. Repeat outcomes
  and synchronization clocks must agree across arms.
- Run attacker arms sequentially, in a seeded **shuffled order**
  per trial/repetition rather than always geometric first. This reduces,
  but does not eliminate, ordering bias, CPU throttling or background
  runner scheduling effects.
- Call `gc.collect()` before each timing. Record actual
  `time.perf_counter_ns()` elapsed around each original attack function
  (including its own Alice/Bob setup). Report the median over two
  repetitions per trial, then the median over trials for each arm.
- For each of the two preregistered **descriptive** contrasts,
  report median across trials of (median-arm-time / median-geometric-time)
  on the **same paired session**. These are not cryptographic
  odds ratios, p-values or a new security test.
- No human-selected trial exclusions. No threshold on absolute speed,
  success, ratio direction or claimed algorithmic superiority in CI.
- Keep timings as **nanoseconds with runner/version metadata**.
  They are noisy and not portable to GPUs, other languages, hardware,
  memory allocators, CPUs under different load, or optimized attacks.
  Python object allocation, garbage collection and sorting matter.
- CI must run the original attack functions, verify the *same*
  previously source-confirmed 30/53/2/58 success receipts and assert
  all time observations are positive and well-formed. Save entire raw
  trial timing report artifact; print only the aggregate workload summary.

This design is not equal-runtime/candidate/operation budget enforcement.
It only **observes** performance on one CI host. Candidate counts are
9 vs 9 and 16 vs 16; the workloads are not algorithmically equivalent.
No inference of key secrecy, use of private weights by attackers, crypto
proof or integration with CryptoWall is permitted.

## Commands

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_tpm_runtime_audit.py
python scripts/run_tpm_runtime_audit.py --smoke
python scripts/run_tpm_runtime_audit.py --full
```

**A new attack-strength comparison with a real equal-compute budget**
would require reserving yet another never-used seed cohort, predefining
the absolute resource cutoff, cryptographic adversary implementations,
and a hardware/software environment before looking at outcomes. The
64 recorded results here are not a fresh held-out security evaluation.
