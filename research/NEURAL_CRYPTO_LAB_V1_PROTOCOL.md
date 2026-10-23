# Neural Crypto Lab v1 — Alice / Bob / multiple Eves

**Type:** exploratory educational experiment; **not an encryption product**.
Based on the adversarial-learning question in Martín Abadi and David Andersen,
*Learning to Protect Communications with Adversarial Neural Cryptography*
(2016): https://arxiv.org/abs/1610.06918

## Research question

Can three separately initialized neural networks develop **learned obfuscation**
in which Bob, who receives the same secret key as Alice, reconstructs an
8-bit message better than independently trained attacks that see only the
floating-point ciphertext?

This is deliberately **not equivalent to IND-CPA, authenticated encryption,
provable confidentiality, post-quantum security or a usable cipher**. A bounded
collection of unsuccessful trained Eves does not imply security against a
cryptanalyst.

## Experimental architecture (predeclared v1 default)

| Agent | Inputs | Output | Hidden units | Training goal |
| --- | --- | --- | --- | --- |
| Alice | 8 message bits + 8 shared key bits | 8 continuous ciphertext values | 32 | Bob reconstruction loss − 0.5 × Eve reconstruction loss |
| Bob | 8 ciphertext values + 8 shared key bits | 8 estimated message bits | 32 | Minimize message MSE |
| Training Eve | 8 ciphertext values, **no key** | 8 estimated message bits | 24 | Minimize message MSE |
| Fresh challenger #1 | 8 ciphertext values, **no key** | 8 estimated message bits | 16 | Train after Alice is frozen |
| Fresh challenger #2 | 8 ciphertext values, **no key** | 8 estimated message bits | 48 | Train after Alice is frozen |

Every network is a tanh hidden layer with sigmoid output. All training uses
simple explicitly coded NumPy gradients with a 0.01 SGD step and a fixed
gradient clipping rule. The training Eve is updated, then Bob, then Alice
against their **current fixed weights**. Fresh challenger networks are
initialized independently **only after Alice training ends**, with fresh
data and independently chosen fixed seeds.

Default development hypothesis budget: 200 train iterations × 128 independent
uniform message/key samples per iteration. Each fresh challenger gets 120 ×
128 newly generated training samples. Evaluation comprises 1024 previously
unseen message/key pairs. All model and dataset seeds derive from
`DEFAULT_SEED = 621017`; data offset mapping is defined in source and is
constant for this protocol. No model weights or user messages are uploaded.

A separate **smoke mode** uses four iterations, four challenger iterations,
24 samples per mini-batch and 96 evaluation pairs. Smoke results are purely
to verify code execution, not scientific observations.

## Predeclared measurements and controls

- Validation accuracy for Bob and the training Eve, evaluated without
  gradient updates or hyperparameter selection.
- Bob's held-out per-bit reconstruction accuracy.
- Per-bit held-out reconstruction accuracy of both *fresh* Eves and the
  maximum attacker accuracy. Higher Eve accuracy means **more** leakage,
  but an apparently low accuracy is not a guarantee of secrecy.
- Positive leakage control: unencrypted identity data are by definition
  available to a keyless observer (accuracy 1.0).
- Conceptual one-time pad (OTP) control: XOR of an independent uniformly
  random 8-bit key and message; Bob recovers perfectly. The expected
  accuracy of a keyless guess is 0.5 **only if the key is one-time and
  independent**. Key reuse destroys the OTP secrecy guarantee.
- The protocol SHA-256 is recorded in the output; reported outcomes are
  metrics, not generated cryptographic secrets.

**Engineering checkpoints**, not proof criteria: if Bob fails to reconstruct
accurately, there is no useful communication method; if a fresh Eve predicts
well above 50%, there is an observable leak. Any unusual results require
independent seeds, larger data budgets, stronger architectures, chosen
plaintext attacks, classical cryptanalysis and preregistered confidence
intervals before discussion of novelty.

## What is *not* measured yet

No attacker with chosen-plaintext access, no ciphertext-only general-purpose
cryptanalysis, no formal IND indistinguishability game, no partial key
exposure, no key-reuse challenge, no ciphertext discretization/quantization
study, no protocol authentication, no persistent key lifecycle, and no
physical side-channel security. The held-out set is random and is used for
**reporting only**, not model fitting. Training against two more Eves does
not bound the space of possible cryptanalytic attacks.

The floating-point ciphertext is not a bitwise cryptogram. We do not
combine it with AES or CryptoWall, and do not derive application keys
from learned embeddings.

## Run and verification

Use isolated optional neural dependencies:

```bash
python -m pip install -e ".[dev,neural]"
python -m pytest tests/test_neural_crypto_lab.py
python scripts/run_neural_crypto_lab.py --smoke
```

A **separately initiated** exploratory full-budget run is available with:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python scripts/run_neural_crypto_lab.py --full --seed 621017
```

The CI workflow tests **only smoke**, not full scientific training. Later
hypothesis-confirming runs must be preregistered across multiple seeds and
frozen dependencies with independent third-party cryptanalysis before
interpreting a positive result.

## Project separation

- `neural_crypto_lab`: original Alice/Bob/Eve-inspired **research only**.
- `adversarial_sbox`: separate frozen Phase 2G and exploratory Phase 2H/2R
  S-Box security/ML work, unchanged by this PR.
- `cryptowall`: standards-based X25519/HKDF/AES-256-GCM application-layer
  experimental envelope, unchanged by this PR.
- `secure_core_mobile`: hardware/session protection prototype, on hold.

**Acceptance for this PR:** byte-accurate code review, reproducible smoke
outputs, negative controls, data separation, and green Python
3.10/3.11/3.12 workflow. A green CI does not demonstrate secrecy.
