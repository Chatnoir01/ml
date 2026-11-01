"""RAVEN-005: bounded, deterministic signed-checkpoint gossip simulation.

Research ONLY. Requires authenticated issuer key and pinned root checkpoint.
There is no consensus, live networking, durability, availability guarantee,
key transparency or actual security against arbitrary Byzantine behavior.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Iterable

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from research.raven_fork_evidence import (
    CheckpointReceipt, prove_conflicting_receipts, verify_receipt,
)


class WitnessRejected(ValueError):
    """Invalid, untrusted or resource-exceeding witness input."""


@dataclass(frozen=True)
class Delivery:
    sent: int
    bytes_sent: int
    blocked: bool = False


def _digest(receipt: CheckpointReceipt) -> str:
    # Length prefixes avoid concatenation ambiguity in transcript framing.
    body, sig = receipt.message(), receipt.signature
    return sha256(b"RAVEN-005/receipt-id/v1\0" + len(body).to_bytes(4, "big")
                  + body + len(sig).to_bytes(2, "big") + sig).hexdigest()


def _is_sha256_hex(value: str) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(ch in "0123456789abcdef" for ch in value))


class Witness:
    """One independently operated, gossip-capable verifier.

    Receipts are stored even when their parent is not rooted (orphans), but
    fork evidence is reported ONLY for pairs rooted at a pinned genesis.
    """

    def __init__(self, *, name: str, issuer: str, namespace: str,
                 compartment: str, genesis_commitment: str,
                 issuer_key: Ed25519PublicKey, max_receipts: int = 4096) -> None:
        if not name or not issuer or not namespace or not compartment:
            raise ValueError("witness identity and scope must be nonempty")
        if not _is_sha256_hex(genesis_commitment):
            raise ValueError("root must be a SHA-256-formatted commitment")
        if type(max_receipts) is not int or not 1 <= max_receipts <= 100000:
            raise ValueError("invalid capacity")
        self.name = name
        self.issuer = issuer
        self.namespace = namespace
        self.compartment = compartment
        self.genesis_commitment = genesis_commitment
        self.issuer_key = issuer_key
        self.max_receipts = max_receipts
        self._records: dict[str, CheckpointReceipt] = {}
        self._connected: frozenset[str] = frozenset()
        self._orphans: frozenset[str] = frozenset()
        self._evidence: tuple[tuple[CheckpointReceipt, CheckpointReceipt], ...] = ()

    def _recompute(self) -> None:
        # An independent pinned root is essential. A signature alone does NOT
        # establish that the parent exists in a trusted checkpoint history.
        reachable = {(0, self.genesis_commitment)}
        connected: set[str] = set()
        groups: dict[tuple[int, str], list[CheckpointReceipt]] = {}
        items = sorted(self._records.items(), key=lambda kv: (
            kv[1].parent_epoch, kv[0]))
        # Receipts increment epoch exactly once, so one ascending pass suffices.
        for identifier, receipt in items:
            parent = (receipt.parent_epoch, receipt.parent_commitment)
            if parent not in reachable:
                continue
            connected.add(identifier)
            reachable.add((receipt.child_epoch, receipt.child_commitment))
            groups.setdefault(parent, []).append(receipt)
        proofs = []
        for origin in sorted(groups):
            # Keep one contradictory pair per parent rather than O(N²) pairs.
            # The full set of signed receipts remains available to reproduce it.
            candidates = groups[origin]
            first = candidates[0]
            first_child = (first.child_commitment, first.child_policy_digest)
            for other in candidates[1:]:
                if (other.child_commitment, other.child_policy_digest) != first_child:
                    proofs.append(prove_conflicting_receipts(first, other, self.issuer_key))
                    break
        self._connected = frozenset(connected)
        self._orphans = frozenset(self._records) - self._connected
        self._evidence = tuple(proofs)

    def observe(self, receipt: CheckpointReceipt) -> bool:
        """Verify an issuer-signed claim, then retain it, even if out of order."""
        if len(receipt.message()) > 4096 or len(receipt.signature) != 64:
            raise WitnessRejected("oversized receipt or invalid signature length")
        verify_receipt(receipt, self.issuer_key)
        if (receipt.issuer, receipt.namespace, receipt.compartment) != (
            self.issuer, self.namespace, self.compartment
        ):
            raise WitnessRejected("receipt outside pinned witness scope")
        if not all(_is_sha256_hex(x) for x in (
            receipt.parent_commitment, receipt.child_commitment,
            receipt.child_policy_digest,
        )):
            raise WitnessRejected("malformed commitment digest")
        if receipt.child_commitment == receipt.parent_commitment:
            raise WitnessRejected("self-commitment transition")
        identity = _digest(receipt)
        if identity in self._records:
            return False
        if len(self._records) >= self.max_receipts:
            raise WitnessRejected("receipt capacity exceeded; fail closed")
        self._records[identity] = receipt
        self._recompute()
        return True

    def compatible(self, peer: Witness) -> bool:
        return (
            self.issuer == peer.issuer
            and self.namespace == peer.namespace
            and self.compartment == peer.compartment
            and self.genesis_commitment == peer.genesis_commitment
            and self.issuer_key.public_bytes_raw() == peer.issuer_key.public_bytes_raw()
        )

    @property
    def evidence(self) -> tuple[tuple[CheckpointReceipt, CheckpointReceipt], ...]:
        return self._evidence

    @property
    def connected_count(self) -> int:
        return len(self._connected)

    @property
    def orphan_count(self) -> int:
        return len(self._orphans)

    @property
    def receipt_count(self) -> int:
        return len(self._records)

    def send_to(self, other: Witness, *, limit: int | None = None) -> Delivery:
        """Deterministically send missing signed claims; no actual network.

        A signed receipt alone is not an endorsement by the sending witness.
        Receivers always verify the checkpoint issuer key themselves.
        """
        if not self.compatible(other):
            raise WitnessRejected("different pinned trust roots or domains")
        if limit is not None and (type(limit) is not int or limit < 0):
            raise ValueError("invalid transmission limit")
        count, size = 0, 0
        for identity, receipt in sorted(self._records.items()):
            if limit is not None and count >= limit:
                break
            if identity in other._records:
                continue
            other.observe(receipt)
            count += 1
            size += len(receipt.message()) + len(receipt.signature)
        return Delivery(count, size)


class Network:
    """Directed simulation of network partitions and gossip rounds.

    All delivery is synchronous and reliable on unblocked edges. This is NOT
    an approximation of real asynchronous Byzantine network guarantees.
    """

    def __init__(self, witnesses: Iterable[Witness]) -> None:
        peers = list(witnesses)
        self.witnesses = {w.name: w for w in peers}
        if len(self.witnesses) != len(peers):
            raise ValueError("duplicate witness names")
        self.blocked: set[tuple[str, str]] = set()
        self.round = 0
        self.bytes_sent = 0
        self.deliveries = 0
        self.first_evidence_round: dict[str, int] = {}

    def step(self, edges: Iterable[tuple[str, str]]) -> tuple[Delivery, ...]:
        self.round += 1
        results = []
        for source_name, target_name in edges:
            if source_name == target_name:
                raise ValueError("self-gossip not supported")
            source, target = self.witnesses[source_name], self.witnesses[target_name]
            if (source_name, target_name) in self.blocked:
                results.append(Delivery(0, 0, blocked=True))
                continue
            delivered = source.send_to(target)
            results.append(delivered)
            self.deliveries += delivered.sent
            self.bytes_sent += delivered.bytes_sent
        for name, witness in self.witnesses.items():
            if witness.evidence and name not in self.first_evidence_round:
                self.first_evidence_round[name] = self.round
        return tuple(results)
