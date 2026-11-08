"""Pure-Python *classical* simulation of BB84 sifting and intercept/resend.

No qubits, photons, quantum hardware, error correction, privacy amplification
or authenticated public discussion. NEVER emits a production secret key.
"""

from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class BB84Config:
    signals: int = 8192
    eve_intercept_probability: float = 0.0
    channel_flip_probability: float = 0.0
    public_test_fraction: float = 0.25
    demo_qber_alarm_threshold: float = 0.11
    seed: int = 770023

    def validate(self) -> None:
        if type(self.signals) is not int or not 32 <= self.signals <= 1_000_000:
            raise ValueError("signals must be an integer in [32, 1000000]")
        if type(self.seed) is not int or not 0 <= self.seed < 2**32:
            raise ValueError("seed must be uint32")
        for name in ("eve_intercept_probability", "channel_flip_probability"):
            value = getattr(self, name)
            if type(value) not in (int, float) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be a probability in [0,1]")
        if type(self.public_test_fraction) not in (float, int) or not (
            0 < self.public_test_fraction < 1
        ):
            raise ValueError("test fraction must be strictly between 0 and 1")
        if type(self.demo_qber_alarm_threshold) not in (float, int) or not (
            0 <= self.demo_qber_alarm_threshold <= 0.5
        ):
            raise ValueError("demo QBER alarm threshold outside [0,0.5]")


def simulate_bb84(config: BB84Config = BB84Config()) -> dict[str, int | float | bool | str]:
    """Report QBER from randomized basis choices; do not output secret key bits.

    In intercept/resend, Eve measures using a random basis. On a mismatched
    basis, the bit is uniformly random, and so is Bob's readout on a basis
    mismatch. This idealized model yields ~25% QBER among sifted bits under
    complete interception, excluding independent channel noise.
    """
    config.validate()
    rng = random.Random(config.seed)
    sifted: list[tuple[int, int]] = []
    intercepted = 0

    for _ in range(config.signals):
        alice_bit = rng.getrandbits(1)
        alice_basis = rng.getrandbits(1)
        bob_basis = rng.getrandbits(1)

        transmitted_bit = alice_bit
        transmitted_basis = alice_basis
        if rng.random() < config.eve_intercept_probability:
            intercepted += 1
            eve_basis = rng.getrandbits(1)
            transmitted_bit = (
                alice_bit if eve_basis == alice_basis else rng.getrandbits(1)
            )
            transmitted_basis = eve_basis

        bob_bit = (
            transmitted_bit if transmitted_basis == bob_basis else rng.getrandbits(1)
        )
        if rng.random() < config.channel_flip_probability:
            bob_bit ^= 1

        if alice_basis == bob_basis:
            sifted.append((alice_bit, bob_bit))

    if len(sifted) < 2:
        # Zero is not evidence of security; do not silently accept empty test.
        raise ValueError("insufficient sifted bits for testing")
    indices = list(range(len(sifted)))
    rng.shuffle(indices)
    test_count = max(1, min(len(sifted) - 1, round(len(sifted) * config.public_test_fraction)))
    public_set = set(indices[:test_count])
    test_errors = sum(sifted[i][0] != sifted[i][1] for i in public_set)
    all_errors = sum(a != b for a, b in sifted)

    return {
        "schema_version": 1,
        "mode": "idealized_classical_bb84_intercept_resend_simulation",
        "signals": config.signals,
        "intercepted_signals": intercepted,
        "sifted_signals": len(sifted),
        "publicly_compared_signals": test_count,
        "unrevealed_sifted_signals": len(sifted) - test_count,
        "public_sample_qber": test_errors / test_count,
        "all_sifted_qber_research_only": all_errors / len(sifted),
        "demo_qber_alarm": (test_errors / test_count) > config.demo_qber_alarm_threshold,
        "no_secure_key_derived": True,
        "no_physical_quantum_claim": True,
        "authenticated_classical_channel": False,
        "error_correction_implemented": False,
        "privacy_amplification_implemented": False,
    }
