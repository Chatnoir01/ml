# Quantum Lab: idealized BB84 intercept–resend simulation

**Status: classical probability simulation, NOT quantum hardware, QKD
implementation, intrusion guarantee or a secure key distribution product.**

## Scope

Reproduce the basic **statistical signature** of an intercept/resend attacker
under a simplified BB84 model.

- Alice sends an independent uniform random bit in either of two equally
  probable ideal bases.
- Bob independently chooses one of the two bases. Only matching-basis
  positions are retained after public basis sifting.
- Eve intercepts each signal with configured probability and measures in an
  independently random basis. For mismatched bases, the measurement outcome
  is uniform and cannot preserve Alice's original bit with certainty.
- Optional independent channel flips model **bit-error noise only**.
- Publicly compare a fixed fraction (default 25%) of the sifted bit pairs,
  then report sampled and total *research-only* QBER.
- With complete intercept/resend and a noiseless channel, the **expected**
  QBER among sifted bits is approximately 25%. Partial interception may
  remain statistically undetectable from a small sample.
- A chosen threshold of 11% is **only a teaching alarm** in this prototype.
  It is *not* a composable finite-key security bound, a detection guarantee
  or a security proof.

## Explicitly absent

No photons or physical measurement, polarization optics, eavesdropper with
quantum memory, multiphoton attacks, detector blinding, imperfect sources,
photon loss, decoy states, entangled states, authenticated classical
communication, information reconciliation, privacy amplification, finite
statistical confidence intervals or composable end-to-end security.

**Never treat leftover sifted bits as an established secret key.**
The module intentionally returns only aggregate counts and error rates.
An interception may cause no observed sample errors; this does not mean
the channel is secure.

## Verification

The pure standard-library module is tested on Python 3.10, 3.11 and 3.12.
Tests cover clean channel, 100% Eve, partial Eve, independent noise, public
sample accounting, deterministic seed reproducibility and invalid input
rejection.

```bash
python -m pip install -e ".[dev]"
python -m pytest tests/test_quantum_lab_bb84.py
```

Research paths are isolated from real CryptoWall, Neural Crypto Lab and
Secretkeeper. A future real QKD demonstration requires physical equipment,
authenticated channels, full finite-key accounting and independent review.
