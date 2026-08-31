# Adversarial S-Box Research

Research framework for evaluating whether learned neural distinguishers can serve as fitness oracles during evolutionary S-Box design, while keeping classical cryptographic constraints explicit and independently testable.

## Research question

Given S-Boxes with comparable classical metrics (nonlinearity, differential uniformity, LAT, SAC, algebraic degree and related side-channel metrics), can an evolutionary search reduce signal exploitable by held-out neural distinguishers without degrading those classical properties?

## Method

The project is intentionally staged:

1. **Phase 0 — foundations:** verified S-Box metrics, AES reference vectors, toy SPN, deterministic dataset plumbing and tests.
2. **Phase 1 — classical evolution:** permutation-preserving GA and baselines, with no neural oracle.
3. **Phase 2 — neural validation:** reproduce a reduced, published distinguisher-style benchmark and establish positive/negative controls.
4. **Phase 3 — closed loop:** use a learned oracle only after classical admissibility gates.
5. **Phase 4 — blind validation:** freeze candidates and test unseen architectures, seeds, keys and datasets.

## Scientific guardrails

- AES S-Box reference checks must pass before optimization work begins.
- Classical security metrics are hard constraints, not quantities a neural score may compensate for.
- Test data never enters evolutionary fitness.
- Oracle networks and held-out challenger networks are separated.
- Results are reported across multiple seeds with uncertainty, not from a single lucky run.
- Negative results are retained.

## Status

Repository initialized. Active implementation work starts on a dedicated `research/phase0-cryptoshield` branch.

## Scope

This repository is for defensive cryptographic research and reproducible experimentation. The initial implementation uses a small educational SPN to study measurement and optimization behavior; it is not intended as a production cipher.
