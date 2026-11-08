# Neural Crypto Lab V1 — original full exploratory execution (2026-11-08)

**Status: PRE-EXECUTION PROTOCOL ONLY. No novel cipher or security claim.**

This is a continuation of draft PR #138, isolated from CryptoWall and Secure Core.
The original predeclared protocol in research/NEURAL_CRYPTO_LAB_V1_PROTOCOL.md uses:
- Frozen seed 621017.
- Alice/Bob/Eve hidden sizes 32/32/24, challenger widths 16 and 48.
- 200 training iterations, 128 examples per iteration, learning rate 0.01, Eve weight 0.5.
- Two independently initialized fresh Eve challengers: 120 steps and 128 examples per step each.
- 1024 held-out message/key examples.
- Plaintext identity and one-time-XOR reference controls.

The isolated GitHub Actions workflow:
1. Executes the existing targeted unit tests with a real NumPy installation.
2. Runs the original full protocol twice, in independent Python processes, on one Python 3.11 Linux runner with limited BLAS threads.
3. Requires byte-identical JSON results across both independent process executions.
4. Requires finite [0,1] measurements, the correct full-run identity, both challengers, valid controls, and an explicit NOT_EVALUATED_CRYPTOGRAPHICALLY security verdict.
5. Archives two full JSON records, their SHA-256 digest, the exact checked-out commit, Python version and a dependency list with its hash.

**No full scientific conclusion is prespecified from one seed.** A high Bob accuracy or low Eve accuracy is NOT security evidence; a weak Bob or successful Eve is still a valid negative observation. The single-seed study is exploratory and does not validate key reuse, chosen plaintext attackers, or broader seed generalization.

No original frozen outcomes are edited; no models are promoted to CryptoWall or production, and no security properties are inferred. A separate prospective protocol and fresh seeds are required for a confirmatory study. Do not merge automatically.
