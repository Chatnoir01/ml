# TPM majority-flipping ensemble — independent exploratory attacker

This experiment extends TPM Lab PR #143 and must **not** be merged before
that branch. It is research-only, not a key exchange, and has no connection
to CryptoWall application secrets.

An odd number of independently initialized passive Eves receive the same
public stimuli and public parity exchange. Each proposes a local hidden
configuration (flipping the minimum-absolute-field unit when parity
disagrees). A majority configuration, if consistent with Alice's public
parity, guides their updates. This is a **simplified heuristic**, not a
verified reproduction of any published cooperative attack.

The predeclared engineering fixture uses TPM K=3,N=8,L=2, 3 trials in
regression tests and 5 attackers; the default exploratory run may use 8
trials and 9 attackers. Report the number of legitimate synchronized
trials separately from the number of exact attacker matches. Censored
trials do not count as security successes. The simulation uses privileged
weight comparison **only to score outcomes**.

No private weights are exported; no secret key is derived; no authenticated
public transcript, information-theoretic guarantee or formal cryptographic
security exists. These tests are regression checks, not independent
cryptanalysis. Additional genetic and active attackers remain future work.
