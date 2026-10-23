# TPM same-runner wall-time: verified retrospective results (2026-10-23)

**Research-only and retrospective; 64 previously observed seeds, not fresh confirmation.**

## Verified GitHub source/run

- Stacked draft [PR #149](https://github.com/Chatnoir01/ml/pull/149).
- Exact original tested head: `1dcaefd0b46f5b3ffd44f325014b72a045bda12f`.
- Specialized GitHub Actions [run 39944832514](https://github.com/Chatnoir01/ml/actions/runs/39944832514) completed **SUCCESS**: Python 3.10, 3.11 and 3.12 engineering smoke; Python 3.11 **all 64 trials** with randomized run order and 2 repetitions.
- Full timing job ID `120384807850` completed **SUCCESS**; raw report artifact ID `12498825840` (`tpm-64-retrospective-wall-time`), archive SHA-256 `fdd8385d1fe0334e121d92fcaebcf40332ced6b7bf2599cb1c33a656b73a3e44`. GitHub retention through ~2026-12-22.
- Dedicated core TPM CI and Phase 0 general CI also completed **SUCCESS** on the exact source head.
- Crucially: all four previously observed exact-state attack-success counts remained unchanged: ensemble9 **30/64**, geometric9 **53/64**, genetic16 **2/64**, geometric16 **58/64**.

## Median per-trial wall times

| Arm | GitHub median over paired trial medians (nanoseconds) | Milliseconds | Exact successes / 64 |
| --- | ---: | ---: | ---: |
| Cooperative ensemble, 9 models | 7,645,428.75 | **7.6454** | 30 |
| Independent geometric, 9 models | 7,432,278.5 | **7.4323** | 53 |
| Genetic-style branching heuristic, 16 candidates | 46,180,684.25 | **46.1807** | 2 |
| Independent geometric, 16 models | 11,587,103.25 | **11.5871** | 58 |

Prespecified *descriptive* paired wall-time ratio (median over 64 trials
of `median(two repeats first) / median(two repeats comparator)`):

- Cooperative9 / geometric9 = **1.018708149665311**.
- Genetic-style16 / geometric16 = **3.9897246789741088**.

**Do not calculate the ratios from the table's marginal medians; the
correct reported ratios are medians of paired per-trial ratios, a different
statistic.** Two repeats per arm, time measurement with
`time.perf_counter_ns()`, Python `gc.collect()` outside each timed
call, and seeded randomized arm ordering.

## Interpretation and limitations

In our implementation, independent geometric replication is more
effective and has slightly lower measured time than majority
cooperation at 9 candidates. Its advantage is much larger against
our *simplified* genetic-style local-field branching heuristic at 16
candidates, where the branching arm constructs far more TPM objects.
This is an engineering and toy-model observation, not a proven
general ranking of neural cryptanalytic algorithms.

Execution timing on hosted runners is noisy (CPU load, virtualization,
interpreter/allocator, warm caches); these numbers are **not portable**.
The measured work includes setting up Alice and Bob inside each arm.
No calibrated equal-time/CPU/energy budget or hardware-independent
instructions metric was enforced. Timings describe already-observed
64 trials, not a new security cohort, independent cryptanalysis, or
probability of confidentiality for real keys.

Do not deploy synchronized TPM weights as real encryption keys and
do not substitute TPM learning for reviewed CryptoWall cryptographic
primitives. Future prospective tests should freeze *new* seeds,
attack selection and performance criteria before seeing any outcomes.
