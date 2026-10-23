# TPM reserved-seed confirmation — candidate-count-matched attacker comparison

**Protocol frozen before any held-out results were inspected or executed.**
This is a numerical experiment in classical, finite-size TPM attacks. It is
**not secure key agreement, cryptographic validation, or production CryptoWall**.

## Prior development and held-out isolation

- Development pilot [PR #146](https://github.com/Chatnoir01/ml/pull/146):
  master seed `782023`, 32 paired TPM trials with a **single geometric Eve**
  versus 9-Eve collective and 16-candidate genetic-style attack. Results and
  all retrospective exploratory contrasts are already visible; those cannot
  be treated as independent confirmation.
- **Confirmation set here:** 64 entirely NEW trial roots, master seed
  `971023`, trial roots `seed + trial_index * 100003`. These roots are
  disjoint from the previous run. No pilot results or holdout outcomes
  enter model selection, hyperparameter tuning or opponent development.
- Fixed legitimate model `K=3, N=8, L=2`, Hebbian integer saturation, max
  8000 rounds per trial; same Alice, Bob and public input stream for
  **every attack arm within each trial**. A mismatched synchronization time
  across arms raises an error rather than fabricating paired observations.
- Public stimulus/outputs only to attackers. Privileged private-weight
  equality is used **only for simulation scoring** and to identify first
  Alice/Bob synchronization. No secret-weight export or key derivation.

## Candidate-matched experimental arms (registered now)

| Prespecified contrast | First attacker | Baseline with same candidate count |
| --- | --- | --- |
| C1 | 9-Eve cooperative majority heuristic | 9 independent geometric Eves |
| C2 | 16-candidate genetic-style branching heuristic | 16 independent geometric Eves |

Replicated geometric models have independently fixed initial seeds and
observe exactly the same public input and public Alice/Bob parity. Their
per-candidate update is the identical minimum-field geometric rule used in
the original TPM lab. A group succeeds if **at least one** candidate's
complete integer-weight state matches Alice at the first legitimate sync.

These are **candidate-count-matched**, NOT equal-CPU, equal-neural-update,
equal-memory, equal-information or representative of optimal attack
populations. Genetic-style candidate branching can be more expensive per
step than independently updated geometric models. Neither implementation
is an independently validated reproduction of a published attack.

## Frozen preregistration hashes

- Holdout plan SHA-256:
  `0872aa224297a9a9630cd7f58448b5254ff12064f651fcfd787424be5bb2ba06`.
- TPM protocol SHA-256:
  `dfb640df5159f38db9cc05706e0d2583273ffdb49d608f324c05d233891e9452`.
- Main source: `src/tpm_lab/heldout.py`.
- Exact operation: `python scripts/run_tpm_holdout.py --confirm`, producing
  JSON output. Dedicated GitHub workflow must verify both SHA-256s,
  exact 64 records, bounded success counts and absence of raw private
  weights; store original JSON in a downloadable CI artifact. CI may also
  run `--smoke` for deterministic engineering tests, **not pilot science**.

## Frozen endpoints and statistical analysis

1. Legitimate Alice/Bob synchronization count, censored count and median
   synchronization round conditional on successful synchronization.
2. For each arm: at-least-one-candidate exact-match count / **legitimate
   synchronized** trials. Censored trials are not attacker failures.
   Report descriptive Wilson 95% intervals.
3. For C1/C2: paired successes (both, neither, first-only, second-only).
   The paired success-rate difference is (first-only - second-only) divided
   by the number of synchronized trials.
4. The two-sided exact McNemar binomial test on discordant pairs, then
   **Holm adjustment across BOTH prespecified contrasts**. Threshold
   adjusted p < 0.05 may indicate a statistical difference for this
   simulation and these conditions; it does not imply cryptographic
   advantage or strong security. Report effects with the counts even if
   p >= 0.05. No post-hoc trial exclusions and no stopping early based on
   outcomes.
5. If fewer than 64 legitimate synchronizations occur, report censored
   outcomes and do not silently replace those seeds or count them as
   successful defensive resistance.

This still cannot establish real-world TPM key security, even with
statistically different simulated attack-success rates. The small TPM's
weight entropy is limited, Python's Mersenne Twister is not a CSPRNG,
the channel is not authenticated, public detection of synchronization
does not exist, and no active/chosen-input/side-channel/key derivation
analysis or independent attack review has occurred.

**One confirmatory seed set only.** Any changes to the 64 seed roots,
contrasts, attack algorithms or outcome criterion require a *new*
protocol version with a separately reserved seed set, not silent
rewriting of the current experimental result.
