# Paired TPM attacker comparison — preregistered descriptive pilot

Research only, no production key exchange, no claim of cryptographic security.

All five attacker arms (naive, geometric, random flipping, cooperative
majority, bounded genetic-style branching) use the **same** Alice/Bob
initializations and the same public stimulus for each trial. Every
implementation's independent attacker randomness is separate. The
comparison asserts that the legitimate synchronization time is identical
across arms, otherwise it fails.

Frozen default: 32 trials, master seed 782023, K=3 N=8 L=2,
max 8000 rounds, cooperative ensemble of 9 and branching population of 16.
No post-hoc seed selection. CI executes only a 2-trial smoke.

Report synchronized versus censored trials; for each attacker, number of
trials with an exact weight match at legitimate synchronization, divided
only by synchronized trials. Include descriptive Wilson 95% intervals.
These intervals describe small independent-trial uncertainty and **do not
bound security against untested attackers**. Resource budgets differ
between a single attacker and an ensemble/population: never imply a
controlled equal-compute comparison.

The attacker models are simplified heuristics, **not** independently
validated reproductions of published attacks. Genetic-style scoring uses
only local fields and public parity, not private Alice weights. Exact
private-state equality is accessed by the simulator for evaluation only.
There is no real public key confirmation, no authentication and no
secret-key extraction. No user data.

Run: `python scripts/run_tpm_comparison.py --smoke`
Full opt-in: `python scripts/run_tpm_comparison.py --trials 32`.
