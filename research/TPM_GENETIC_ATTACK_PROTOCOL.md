# TPM branching population attacker — research protocol

This PR is stacked on TPM #144, which is stacked on #143. It adds a
**bounded genetic-style branching heuristic**, not a faithful reproduction
or validated security evaluation of the published genetic attack.

At each public parity agreement between Alice and Bob, the attacker
branches each independently seeded candidate TPM into parity-compatible
hidden configurations. Each child updates only from public stimuli and
the observed public parity. Population is capped at 2–128. Children are
ranked by a heuristic derived from their own local field magnitudes,
with seeded random tie breaking. This heuristic may be weak or biased.

Default pilot: K=3, N=8, L=2, 8 trials, 16 candidates, at most 8000
steps. Tests use 2 trials and 8 candidates to stay inexpensive.
The only comparison against Alice's private weights occurs at
**simulation scoring time**, never in attacker branching or ranking.

Report legitimate synchronization count, censored count, and
number of trials in which any candidate exactly matches Alice at
the first legitimate synchronization. Never interpret censored
runs as attacker failures, and do not compare population success
with a single attacker without noting different resource budgets.

The code does not derive or export secret keys. It does not implement
an authenticated transcript, genetic selection over validated fitness,
majority-flipping literature benchmarks, chosen-input attacks, key
confirmation or formal security analysis. No production CryptoWall
integration or claims of post-quantum resistance are allowed.
