# Prospective TPM three-scale replication — frozen protocol v1

**Frozen before the 96 reserved sessions were executed or inspected.**
This is research into weak finite tree-parity-machine implementations,
**not** an endorsed key exchange or encryption protocol.

## Why this is new, not reused

Earlier public results: development pilot 32 seeds (master 782023),
held-out 64 seeds (master 971023), plus the follow-up retrospective
workload and wall-time audit on those exact 64 sessions. Those outcomes
show high success of 9 independent geometric attackers versus our
cooperative heuristic at K=3,N=8,L=2.

This protocol reserves **96 new sessions** over three model sizes,
with no overlapping public random-state roots with the earlier two
cohorts. No changes to the evaluated attack implementations, chosen
outcome, candidate counts or registered scale set are allowed after
viewing any scale result.

## Registered scales (all 32 independent trials)

| Scale ID | Hidden units K | Inputs N | Weight depth L | New master seed | Trials | Hard step cap |
|---|---:|---:|---:|---:|---:|---:|
| small_N8_L2 | 3 | 8 | 2 | 25102311 | 32 | 12000 |
| medium_N16_L3 | 3 | 16 | 3 | 25102319 | 32 | 12000 |
| large_N32_L4 | 3 | 32 | 4 | 25102331 | 32 | 12000 |

Each trial's public/party RNG root is `master_seed + index*100003`,
as in the original implementation. Each scale independently initializes
Alice and Bob identically across attack arms. There is **no** adaptive
stopping or selection after inspecting any per-trial result.

Frozen plan SHA-256:
`6d282d9130f03e41204607af690c50501afec816d5820639c2eeba2178d69569`.

## Attack resource controls

Exactly two immutable attacker implementations are compared in each
trial:

- **9 independent geometric Eves**, each using her own local field to
  determine the minimum-absolute-field hidden flip upon disagreement.
- **9 cooperating majority-flipping Eves** using the heuristic from
  the existing frozen ensemble PR #144.

Both see **only the common public stimulus and public parity**.
Instrument the actual `TPM.evaluate()` invocation for each model,
not estimated counts. The experiment **fails closed** if attack
candidate constructions are unequal or the total attacker forward
evaluations differ *within a paired trial*. Synchronization must
occur at the exact same step for both attack arms. Record actual
updates and attempted coordinate writes as secondary work counters.

**This aligns 9 candidates and observed forward evaluations, not the
complete CPU work**: cooperative majority computations, branch logic,
memory allocation, or future optimizations may differ. Therefore
the experiment is called *forward-evaluation-matched*, not *equal-cost*.

## Registered endpoints and analysis

For every scale and all 32 seeds, record:

1. Number of legitimate synchronizations; censored cases if the parties
   do not synchronize before the 12000-step cap; median legitimate
   synchronization step only across successfully synchronized trials.
2. For each arm, number of trials with **any exact attack weight match
   at the first legitimate sync**, divided by synchronized trials only.
   A censored session is not a success or failure for either attacker.
   Descriptive Wilson 95% intervals are reported.
3. Paired contingency: both succeed, neither succeed, cooperative only,
   geometric only. Report cooperative minus geometric paired success-rate.
4. **Two-sided exact McNemar test separately for each of the THREE scales**,
   with **Holm correction across all three scales** fixed in advance,
   including p=1 for a completely censored scale so the multiplicity
   family cannot shrink opportunistically.
5. Adjusted p < 0.05 is only evidence of a simulator-level difference
   for these specific models, not evidence of TPM security, cryptographic
   indistinguishability, or superiority against all attacker families.
   Even if all p values are non-significant, the work must report
   observed attack successes and censored fractions.
6. No late addition of strong/missing attackers to retroactively change
   the confirmatory claim. Independent attack families (genetic,
   active chosen-input, optimized solvers) require new frozen protocols.

The private model states are **simulation-only scoring instruments**,
never visible to Eves. The software neither derives nor releases any
secret key or raw private weight tensor. It does not authenticate public
messages, provide legitimate public synchronization confirmation, use
a CSPRNG, or claim formal security. The relevant CryptoWall construction
continues to use independent, vetted cryptographic libraries, **not TPM**.

## Exact execution

```bash
python -m pip install -e ".[dev]"
python -m pytest -q tests/test_tpm_multiscale.py
python scripts/run_tpm_multiscale.py --smoke
python scripts/run_tpm_multiscale.py --confirm
```

A dedicated GitHub Actions workflow must execute the 96-trial
confirmation **on the actual PR source tree**, verify the frozen plan
hash, each trial index, all resource and outcome accounting, and
upload the unedited JSON artifact. No complete outcome data or claims
shall be entered here until that source-run finishes and reports.
