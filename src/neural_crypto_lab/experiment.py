"""Alice/Bob/Eve educational neural cryptography experiment.

This studies learnability against bounded adversaries, NEVER cryptographic
security. Soft floating-point ciphertext is not a deployable cipher.
No production CryptoWall or Secure Core imports and no held-out test tuning.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

import numpy as np

MESSAGE_BITS = 8
KEY_BITS = 8
DEFAULT_SEED = 621017
TRAIN_DATA_SEED_OFFSET = 101
VALIDATION_SEED_OFFSET = 202
TEST_SEED_OFFSET = 303
CHALLENGER_DATA_SEED_OFFSET = 404
STEPS = 200
BATCH = 128
EVE_WEIGHT = 0.5
LEARNING_RATE = 0.01


@dataclass(frozen=True)
class Protocol:
    version: int = 1
    message_bits: int = MESSAGE_BITS
    key_bits: int = KEY_BITS
    ciphertext_units: int = 8
    hidden_alice: int = 32
    hidden_bob: int = 32
    hidden_eve: int = 24
    hidden_challengers: tuple[int, int] = (16, 48)
    train_steps: int = STEPS
    batch_size: int = BATCH
    learning_rate: float = LEARNING_RATE
    eve_weight: float = EVE_WEIGHT
    challenger_steps: int = 120
    eval_samples: int = 1024

    def validate(self) -> None:
        if self.version != 1 or self.message_bits != 8 or self.key_bits != 8:
            raise ValueError("only preregistered 8-bit v1 demonstration supported")
        if self.ciphertext_units != 8 or self.hidden_challengers != (16, 48):
            raise ValueError("ciphertext/challenger v1 architecture is frozen")
        if any(v < 1 or v > 4096 for v in (
            self.hidden_alice, self.hidden_bob, self.hidden_eve,
            self.batch_size, self.train_steps, self.challenger_steps,
            self.eval_samples,
        )):
            raise ValueError("protocol has invalid bounded compute dimensions")
        if not (0 < self.learning_rate <= 0.05 and 0 <= self.eve_weight <= 2):
            raise ValueError("invalid optimizer or adversarial weight")

    def digest(self) -> str:
        return hashlib.sha256(
            json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


class MLP:
    """Simple tanh-sigmoid MLP with explicit input gradient for Alice updates."""

    def __init__(self, inputs: int, hidden: int, outputs: int, seed: int):
        if min(inputs, hidden, outputs) < 1:
            raise ValueError("MLP dimensions must be positive")
        rng = np.random.default_rng(seed)
        self.w1 = rng.normal(0, 1 / np.sqrt(inputs), (inputs, hidden))
        self.b1 = np.zeros(hidden)
        self.w2 = rng.normal(0, 1 / np.sqrt(hidden), (hidden, outputs))
        self.b2 = np.zeros(outputs)

    def forward(self, x: np.ndarray) -> tuple[np.ndarray, tuple]:
        h = np.tanh(x @ self.w1 + self.b1)
        z = h @ self.w2 + self.b2
        y = 1 / (1 + np.exp(-np.clip(z, -30, 30)))
        return y, (x, h, y)

    def backward(self, cache: tuple, dy: np.ndarray) -> tuple[np.ndarray, tuple]:
        x, h, y = cache
        dz = dy * y * (1.0 - y)
        dw2 = h.T @ dz
        db2 = dz.sum(axis=0)
        dh = (dz @ self.w2.T) * (1 - h * h)
        dw1 = x.T @ dh
        db1 = dh.sum(axis=0)
        dx = dh @ self.w1.T
        return dx, (dw1, db1, dw2, db2)

    def update(self, grads: tuple, learning_rate: float) -> None:
        for param, grad in zip((self.w1, self.b1, self.w2, self.b2), grads):
            np.clip(grad, -5, 5, out=grad)
            param -= learning_rate * grad

    def predict(self, x: np.ndarray) -> np.ndarray:
        return self.forward(x)[0]


def _loss(prediction: np.ndarray, actual: np.ndarray) -> tuple[float, np.ndarray]:
    if prediction.shape != actual.shape:
        raise ValueError("mismatched prediction and message shapes")
    error = prediction - actual
    # Mean-squared error over batch and bits; gradient matches scalar loss.
    return float(np.mean(error**2)), 2.0 * error / error.size


def _bits(seed: int, count: int) -> tuple[np.ndarray, np.ndarray]:
    if count < 1:
        raise ValueError("nonempty samples required")
    rng = np.random.default_rng(seed)
    messages = rng.integers(0, 2, (count, MESSAGE_BITS)).astype(np.float64)
    keys = rng.integers(0, 2, (count, KEY_BITS)).astype(np.float64)
    return messages, keys


def _bit_accuracy(predictions: np.ndarray, messages: np.ndarray) -> float:
    return float(np.mean((predictions >= 0.5) == (messages >= 0.5)))


def _retrain_attacker(
    frozen_alice: MLP, *, hidden: int, seed: int, data_seed: int,
    steps: int, batch_size: int, learning_rate: float,
) -> MLP:
    """New attacker sees *only* ciphertext; Alice cannot receive gradients."""
    attacker = MLP(8, hidden, 8, seed)
    rng = np.random.default_rng(data_seed)
    for _ in range(steps):
        m = rng.integers(0, 2, (batch_size, 8)).astype(np.float64)
        k = rng.integers(0, 2, (batch_size, 8)).astype(np.float64)
        cipher = frozen_alice.predict(np.concatenate((m, k), axis=1))
        out, cache = attacker.forward(cipher)
        _, grad = _loss(out, m)
        _, weight_grad = attacker.backward(cache, grad)
        attacker.update(weight_grad, learning_rate)
    return attacker


def run_experiment(
    *, seed: int = DEFAULT_SEED, protocol: Protocol | None = None,
) -> dict[str, Any]:
    """Run opt-in *toy* adversarial training; not an audited cipher experiment."""
    p = Protocol() if protocol is None else protocol
    p.validate()
    if type(seed) is not int or not 0 <= seed < (1 << 32):
        raise ValueError("seed must be a uint32")

    alice = MLP(16, p.hidden_alice, 8, seed + 1)
    bob = MLP(16, p.hidden_bob, 8, seed + 2)
    eve = MLP(8, p.hidden_eve, 8, seed + 3)
    rng = np.random.default_rng(seed + TRAIN_DATA_SEED_OFFSET)

    for _ in range(p.train_steps):
        m = rng.integers(0, 2, (p.batch_size, 8)).astype(np.float64)
        k = rng.integers(0, 2, (p.batch_size, 8)).astype(np.float64)

        # Train Eve on the current Alice output, with no gradient back to Alice.
        c = alice.predict(np.concatenate((m, k), axis=1))
        e, ec = eve.forward(c)
        _, de = _loss(e, m)
        _, grads = eve.backward(ec, de)
        eve.update(grads, p.learning_rate)

        # Update Bob to reconstruct the message given ciphertext and secret key.
        b, bc = bob.forward(np.concatenate((c, k), axis=1))
        _, db = _loss(b, m)
        _, grads = bob.backward(bc, db)
        bob.update(grads, p.learning_rate)

        # Alice minimizes Bob's loss and *maximizes* this Eve's loss.
        # Derivatives are evaluated against the newly updated fixed opponents.
        ac_input = np.concatenate((m, k), axis=1)
        c, ac = alice.forward(ac_input)
        b, bc = bob.forward(np.concatenate((c, k), axis=1))
        e, ec = eve.forward(c)
        _, db = _loss(b, m)
        _, de = _loss(e, m)
        dx_b, _ = bob.backward(bc, db)
        dx_e, _ = eve.backward(ec, de)
        _, grads = alice.backward(ac, dx_b[:, :8] - p.eve_weight * dx_e)
        alice.update(grads, p.learning_rate)

    # Validation is for observing learning curves, never for tuning held-out.
    v_m, v_k = _bits(seed + VALIDATION_SEED_OFFSET, p.eval_samples)
    v_c = alice.predict(np.concatenate((v_m, v_k), axis=1))
    val_bob = _bit_accuracy(bob.predict(np.concatenate((v_c, v_k), axis=1)), v_m)
    val_eve = _bit_accuracy(eve.predict(v_c), v_m)

    challengers = [
        _retrain_attacker(
            alice, hidden=h, seed=seed + 2000 + i,
            data_seed=seed + CHALLENGER_DATA_SEED_OFFSET + i * 10_000,
            steps=p.challenger_steps, batch_size=p.batch_size,
            learning_rate=p.learning_rate,
        )
        for i, h in enumerate(p.hidden_challengers)
    ]
    t_m, t_k = _bits(seed + TEST_SEED_OFFSET, p.eval_samples)
    t_c = alice.predict(np.concatenate((t_m, t_k), axis=1))
    bob_acc = _bit_accuracy(bob.predict(np.concatenate((t_c, t_k), axis=1)), t_m)
    attacker_acc = [_bit_accuracy(a.predict(t_c), t_m) for a in challengers]

    # Explicit, independent baselines on the SAME held-out message/key pairs.
    # Identity intentionally leaks 100% (positive attacker control).
    # Fresh uniform XOR mask with one-time keys leaks no message information
    # to a keyless adversary, but only when the key is NEVER reused.
    xor_cipher = np.logical_xor(t_m.astype(bool), t_k.astype(bool)).astype(float)
    xor_bob = np.logical_xor(xor_cipher.astype(bool), t_k.astype(bool))
    return {
        "schema_version": 1,
        "kind": "educational_neural_cryptography_not_a_cipher",
        "seed": seed,
        "protocol_sha256": p.digest(),
        "architecture": {
            "alice": [16, p.hidden_alice, 8],
            "bob": [16, p.hidden_bob, 8],
            "eve": [8, p.hidden_eve, 8],
            "fresh_eve_hidden": list(p.hidden_challengers),
        },
        "train_steps": p.train_steps,
        "val_bob_bit_accuracy": val_bob,
        "val_trained_eve_bit_accuracy": val_eve,
        "heldout_bob_bit_accuracy": bob_acc,
        "heldout_fresh_eve_bit_accuracies": attacker_acc,
        "heldout_fresh_eve_max_bit_accuracy": max(attacker_acc),
        "controls": {
            "identity_eve_accuracy": _bit_accuracy(t_m, t_m),
            "fresh_xor_bob_accuracy": _bit_accuracy(xor_bob.astype(float), t_m),
            "fresh_xor_keyless_guess_expected_accuracy": 0.5,
        },
        "no_security_claim": True,
        "holdout_not_used_for_training": True,
        "no_crypto_wall_integration": True,
    }
