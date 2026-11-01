"""RAVEN-006: independently signed witness attestations, research-only.

The *single pinned-genesis transition* experiment explores quorum intersection,
not BFT consensus or durable finality. Honest keys and their one-vote records
exist only in process memory: restart/rollback/compromise invalidate assumptions.
A quorum certificate proves signatures by members of a pinned roster, not that
a proposal was committed, honest witnesses were online, or ciphertext is safe.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)

from research.raven_fork_evidence import CheckpointReceipt, verify_receipt
from research.raven_signed_model import Rejected, canonical
from research.raven_witness_model import Witness, _digest as receipt_id

DOMAIN = "RAVEN-006/witness-endorsement/v1"


def _hex_digest(value: str) -> bool:
    return (isinstance(value, str) and len(value) == 64
            and all(c in "0123456789abcdef" for c in value))


@dataclass(frozen=True)
class Roster:
    issuer: str
    namespace: str
    compartment: str
    genesis_commitment: str
    issuer_key: Ed25519PublicKey
    witnesses: Mapping[str, Ed25519PublicKey]
    max_byzantine: int

    def __post_init__(self) -> None:
        if not self.issuer or not self.namespace or not self.compartment:
            raise ValueError("missing pinned scope")
        if not _hex_digest(self.genesis_commitment):
            raise ValueError("invalid pinned genesis")
        if not isinstance(self.issuer_key, Ed25519PublicKey):
            raise ValueError("invalid checkpoint-issuer key")
        roster = dict(self.witnesses)
        if not roster or any(not x or not isinstance(k, Ed25519PublicKey)
                             for x, k in roster.items()):
            raise ValueError("invalid witness roster")
        if len({x.public_bytes_raw() for x in roster.values()}) != len(roster):
            raise ValueError("witness keys must be independently distinct")
        f = self.max_byzantine
        n = len(roster)
        if type(f) is not int or f < 0 or n < 3 * f + 1:
            raise ValueError("need n >= 3f+1 with f >= 0")
        object.__setattr__(self, "witnesses", MappingProxyType(roster))

    @property
    def quorum(self) -> int:
        return len(self.witnesses) - self.max_byzantine

    @property
    def intersection_lower_bound(self) -> int:
        return 2 * self.quorum - len(self.witnesses)


@dataclass(frozen=True)
class Attestation:
    witness: str
    issuer: str
    namespace: str
    compartment: str
    genesis_commitment: str
    parent_epoch: int
    parent_commitment: str
    child_epoch: int
    receipt_hash: str
    signature: bytes

    def body(self) -> dict:
        return {
            "domain": DOMAIN, "witness": self.witness,
            "issuer": self.issuer, "namespace": self.namespace,
            "compartment": self.compartment,
            "genesis_commitment": self.genesis_commitment,
            "parent_epoch": self.parent_epoch,
            "parent_commitment": self.parent_commitment,
            "child_epoch": self.child_epoch,
            "receipt_hash": self.receipt_hash,
        }

    def message(self) -> bytes:
        return canonical(self.body())


def _check_root_receipt(receipt: CheckpointReceipt, roster: Roster) -> None:
    """Deliberate RAVEN-006 restriction: only the first child of pinned genesis."""
    verify_receipt(receipt, roster.issuer_key)
    if (receipt.issuer, receipt.namespace, receipt.compartment) != (
        roster.issuer, roster.namespace, roster.compartment
    ):
        raise Rejected("receipt outside pinned scope")
    if (receipt.parent_epoch != 0 or receipt.child_epoch != 1
            or receipt.parent_commitment != roster.genesis_commitment):
        raise Rejected("only pinned-genesis transitions are modeled")
    if (not _hex_digest(receipt.child_commitment)
            or not _hex_digest(receipt.child_policy_digest)):
        raise Rejected("malformed signed digest")
    if receipt.child_commitment == receipt.parent_commitment:
        raise Rejected("self transition")


def sign_witness_claim(key: Ed25519PrivateKey, roster: Roster,
                       witness: str, receipt: CheckpointReceipt) -> Attestation:
    """Low-level test helper: a keyholder can sign arbitrarily, including Byzantine forks.

    This signature alone is not a valid certificate. The HonestWitness wrapper
    enforces one-vote-per-parent; only the threat model makes that honest rule
    meaningful.
    """
    if witness not in roster.witnesses:
        raise Rejected("witness not in pinned roster")
    if key.public_key().public_bytes_raw() != roster.witnesses[witness].public_bytes_raw():
        raise Rejected("wrong witness signing key")
    _check_root_receipt(receipt, roster)
    unsigned = Attestation(
        witness=witness, issuer=receipt.issuer,
        namespace=receipt.namespace, compartment=receipt.compartment,
        genesis_commitment=roster.genesis_commitment,
        parent_epoch=receipt.parent_epoch,
        parent_commitment=receipt.parent_commitment,
        child_epoch=receipt.child_epoch,
        receipt_hash=receipt_id(receipt),
        signature=b"",
    )
    return Attestation(**{**unsigned.__dict__,
                          "signature": key.sign(unsigned.message())})


def verify_attestation(att: Attestation, receipt: CheckpointReceipt,
                       roster: Roster) -> None:
    _check_root_receipt(receipt, roster)
    pub = roster.witnesses.get(att.witness)
    if pub is None:
        raise Rejected("unregistered witness")
    expected = (
        receipt.issuer, receipt.namespace, receipt.compartment,
        roster.genesis_commitment, receipt.parent_epoch,
        receipt.parent_commitment, receipt.child_epoch, receipt_id(receipt),
    )
    actual = (
        att.issuer, att.namespace, att.compartment,
        att.genesis_commitment, att.parent_epoch, att.parent_commitment,
        att.child_epoch, att.receipt_hash,
    )
    if actual != expected:
        raise Rejected("attestation and checkpoint mismatch")
    if len(att.signature) != 64:
        raise Rejected("invalid witness signature length")
    try:
        pub.verify(att.signature, att.message())
    except (InvalidSignature, ValueError, TypeError) as exc:
        raise Rejected("invalid witness signature") from exc


class HonestWitness:
    """Witness with volatile one-vote guard. NOT rollback-proof witness custody."""

    def __init__(self, witness_id: str, private_key: Ed25519PrivateKey,
                 roster: Roster):
        if witness_id not in roster.witnesses:
            raise ValueError("unknown witness")
        if (private_key.public_key().public_bytes_raw() !=
                roster.witnesses[witness_id].public_bytes_raw()):
            raise ValueError("wrong private key")
        self.witness_id, self.private_key, self.roster = witness_id, private_key, roster
        self.history = Witness(
            name=witness_id, issuer=roster.issuer,
            namespace=roster.namespace, compartment=roster.compartment,
            genesis_commitment=roster.genesis_commitment,
            issuer_key=roster.issuer_key,
        )
        self._votes: dict[tuple[int, str], Attestation] = {}

    def endorse(self, receipt: CheckpointReceipt) -> Attestation:
        _check_root_receipt(receipt, self.roster)
        self.history.observe(receipt)
        if not self.history.is_rooted(receipt):
            raise Rejected("unrooted proposal")
        parent = (receipt.parent_epoch, receipt.parent_commitment)
        existing = self._votes.get(parent)
        if existing is not None:
            if existing.receipt_hash != receipt_id(receipt):
                raise Rejected("honest witness refuses double vote")
            return existing
        att = sign_witness_claim(
            self.private_key, self.roster, self.witness_id, receipt,
        )
        self._votes[parent] = att
        return att


@dataclass(frozen=True)
class QuorumCertificate:
    receipt: CheckpointReceipt
    attestations: tuple[Attestation, ...]


def verify_quorum_certificate(qc: QuorumCertificate, roster: Roster) -> None:
    _check_root_receipt(qc.receipt, roster)
    if len(qc.attestations) < roster.quorum or len(qc.attestations) > len(roster.witnesses):
        raise Rejected("insufficient or excessive witness signatures")
    seen: set[str] = set()
    for att in qc.attestations:
        if att.witness in seen:
            raise Rejected("duplicate witness identity")
        seen.add(att.witness)
        verify_attestation(att, qc.receipt, roster)


def prove_witness_double_vote(
    a: Attestation, a_receipt: CheckpointReceipt,
    b: Attestation, b_receipt: CheckpointReceipt,
    roster: Roster,
) -> tuple[Attestation, Attestation]:
    """A publicly verifiable conflicting-signature pair from one roster member."""
    verify_attestation(a, a_receipt, roster)
    verify_attestation(b, b_receipt, roster)
    if a.witness != b.witness:
        raise Rejected("not the same witness")
    if (a.parent_epoch, a.parent_commitment, a.child_epoch) != (
        b.parent_epoch, b.parent_commitment, b.child_epoch
    ):
        raise Rejected("different transition origins")
    if a.receipt_hash == b.receipt_hash:
        raise Rejected("not conflicting endorsements")
    return a, b
