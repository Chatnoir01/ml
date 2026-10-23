"""Tree parity machine synchronization and passive attacker experiments.

Educational, deterministic, finite-size *classical simulation*. This is NOT
secure key agreement: public transcript is unauthenticated, algorithms/seed
are public, tested attackers are bounded, and no secret is exported.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import random
import statistics
from typing import Any


@dataclass(frozen=True)
class TPMProtocol:
    hidden_units: int = 3
    inputs_per_unit: int = 8
    synaptic_depth: int = 2
    max_steps: int = 8000
    trials: int = 8
    master_seed: int = 782023
    learning_rule: str = "hebbian"

    def validate(self) -> None:
        if (type(self.hidden_units) is not int or self.hidden_units != 3
                or type(self.inputs_per_unit) is not int or not 2 <= self.inputs_per_unit <= 128
                or type(self.synaptic_depth) is not int or not 1 <= self.synaptic_depth <= 16
                or type(self.max_steps) is not int or not 1 <= self.max_steps <= 100000
                or type(self.trials) is not int or not 1 <= self.trials <= 100
                or type(self.master_seed) is not int or not 0 <= self.master_seed < 2**32
                or self.learning_rule != "hebbian"):
            raise ValueError("invalid or nonregistered TPM protocol parameters")

    def sha256(self) -> str:
        self.validate()
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class TPM:
    def __init__(self, *, k: int, n: int, l: int, rng: random.Random):
        self.k, self.n, self.l = k, n, l
        self.weights = [[rng.randint(-l, l) for _ in range(n)] for _ in range(k)]

    def evaluate(self, signal: tuple[tuple[int, ...], ...]) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
        if len(signal) != self.k or any(len(row) != self.n or any(x not in (-1, 1) for x in row) for row in signal):
            raise ValueError("invalid public TPM stimulus")
        fields = tuple(sum(w * x for w, x in zip(weights, inputs)) for weights, inputs in zip(self.weights, signal))
        hidden = tuple(1 if h >= 0 else -1 for h in fields)
        parity = 1
        for sigma in hidden:
            parity *= sigma
        return parity, hidden, fields

    def update(self, signal: tuple[tuple[int, ...], ...], public_tau: int, hidden: tuple[int, ...]) -> None:
        """Hebbian, fixed integer saturation. Update only matching hidden outputs."""
        if public_tau not in (-1, 1) or len(hidden) != self.k or any(s not in (-1, 1) for s in hidden):
            raise ValueError("invalid teacher parity or hidden outputs")
        for i, (row, sigma) in enumerate(zip(signal, hidden)):
            if sigma == public_tau:
                for j, x in enumerate(row):
                    self.weights[i][j] = max(-self.l, min(self.l, self.weights[i][j] + public_tau * x))


def _signal(rng: random.Random, k: int, n: int) -> tuple[tuple[int, ...], ...]:
    return tuple(tuple(1 if rng.getrandbits(1) else -1 for _ in range(n)) for _ in range(k))


def trial(protocol: TPMProtocol, *, trial_index: int) -> dict[str, Any]:
    protocol.validate()
    if type(trial_index) is not int or not 0 <= trial_index < protocol.trials:
        raise ValueError("invalid trial index")
    # Independent state and public input streams. No post-hoc seed selection.
    root = protocol.master_seed + trial_index * 100_003
    public = random.Random(root + 1)
    alice = TPM(k=protocol.hidden_units, n=protocol.inputs_per_unit, l=protocol.synaptic_depth, rng=random.Random(root + 10))
    bob = TPM(k=protocol.hidden_units, n=protocol.inputs_per_unit, l=protocol.synaptic_depth, rng=random.Random(root + 20))
    naive = TPM(k=protocol.hidden_units, n=protocol.inputs_per_unit, l=protocol.synaptic_depth, rng=random.Random(root + 30))
    geometric = TPM(k=protocol.hidden_units, n=protocol.inputs_per_unit, l=protocol.synaptic_depth, rng=random.Random(root + 40))
    random_flip = TPM(k=protocol.hidden_units, n=protocol.inputs_per_unit, l=protocol.synaptic_depth, rng=random.Random(root + 50))
    attack_rng = random.Random(root + 60)
    accepted = 0
    synced_at: int | None = None
    attacker_matches_at_sync: dict[str, bool] | None = None

    for step in range(1, protocol.max_steps + 1):
        stimulus = _signal(public, protocol.hidden_units, protocol.inputs_per_unit)
        tau_a, hidden_a, _ = alice.evaluate(stimulus)
        tau_b, hidden_b, _ = bob.evaluate(stimulus)
        if tau_a == tau_b:
            accepted += 1
            # Eve sees only public input and the public exchange parities.
            states = {
                "naive": (naive, naive.evaluate(stimulus)),
                "geometric": (geometric, geometric.evaluate(stimulus)),
                "random_flip": (random_flip, random_flip.evaluate(stimulus)),
            }
            alice.update(stimulus, tau_a, hidden_a)
            bob.update(stimulus, tau_b, hidden_b)
            for strategy, (eve, (tau_e, sig_e, field_e)) in states.items():
                if strategy == "naive" and tau_e != tau_a:
                    continue
                new_sig = list(sig_e)
                if tau_e != tau_a:
                    if strategy == "geometric":
                        layer = min(range(protocol.hidden_units), key=lambda i: (abs(field_e[i]), i))
                    else:
                        layer = attack_rng.randrange(protocol.hidden_units)
                    new_sig[layer] *= -1
                eve.update(stimulus, tau_a, tuple(new_sig))
        # Comparing PRIVATE weights is simulation-only evidence and cannot be
        # used by real peers as a public synchronization oracle.
        if alice.weights == bob.weights:
            synced_at = step
            attacker_matches_at_sync = {
                "naive": naive.weights == alice.weights,
                "geometric": geometric.weights == alice.weights,
                "random_flip": random_flip.weights == alice.weights,
            }
            break

    return {
        "trial_index": trial_index,
        "synchronized": synced_at is not None,
        "steps_to_sync": synced_at,
        "observed_steps": synced_at if synced_at is not None else protocol.max_steps,
        "public_accepted_steps": accepted,
        "attacker_exact_match_at_sync": attacker_matches_at_sync,
        "no_secret_weights_exported": True,
    }


def run_study(protocol: TPMProtocol = TPMProtocol()) -> dict[str, Any]:
    protocol.validate()
    records = [trial(protocol, trial_index=i) for i in range(protocol.trials)]
    synced = [r for r in records if r["synchronized"]]
    attack_success = {
        name: sum(int(r["attacker_exact_match_at_sync"][name]) for r in synced)
        for name in ("naive", "geometric", "random_flip")
    }
    return {
        "schema_version": 1,
        "kind": "experimental_tree_parity_machine_sync_not_cryptography",
        "protocol_sha256": protocol.sha256(),
        "protocol": asdict(protocol),
        "trials": records,
        "synchronized_trials": len(synced),
        "unsynchronized_trials": protocol.trials - len(synced),
        "median_steps_conditional_on_sync": (
            statistics.median(r["steps_to_sync"] for r in synced) if synced else None
        ),
        "attacker_exact_matches_at_sync": attack_success,
        "attacker_comparison_denominator": len(synced),
        "attacker_success_not_measured_when_no_sync": True,
        "authentication_not_implemented": True,
        "does_not_generate_a_secure_key": True,
        "no_production_crypto_integration": True,
    }
