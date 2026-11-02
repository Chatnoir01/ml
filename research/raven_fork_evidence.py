"""RAVEN-004: verifiable *signed-claim* fork evidence, research-only.

Two valid checkpoint receipts with a common parent and differing children
provide evidence of conflicting claims by the same receipt-signing authority.
Issuance checks the simulated live anchor, but does NOT prove durable finality
or identify a canonical branch. A witness must actually receive both receipts.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey, Ed25519PublicKey,
)

from research.raven_signed_model import (
    InMemoryAnchor, Rejected, SignedTransition, State, canonical, verify_transition,
)
from research.raven_recovery_model import resulting_state

RECEIPT_DOMAIN = "RAVEN-004/checkpoint-receipt/v1"


@dataclass(frozen=True)
class CheckpointReceipt:
    issuer: str
    namespace: str
    compartment: str
    parent_epoch: int
    parent_commitment: str
    child_epoch: int
    child_commitment: str
    child_policy_digest: str
    signature: bytes

    def body(self) -> dict:
        return {
            "domain": RECEIPT_DOMAIN, "issuer": self.issuer,
            "namespace": self.namespace, "compartment": self.compartment,
            "parent_epoch": self.parent_epoch,
            "parent_commitment": self.parent_commitment,
            "child_epoch": self.child_epoch,
            "child_commitment": self.child_commitment,
            "child_policy_digest": self.child_policy_digest,
        }

    def message(self) -> bytes:
        return canonical(self.body())


def issue_receipt(
    *, anchor: InMemoryAnchor, previous: State, change: SignedTransition,
    transition_authority: Ed25519PublicKey,
    issuer: str, checkpoint_signer: Ed25519PrivateKey,
) -> CheckpointReceipt:
    """Only model-side issuance: verify signed transition and new anchor state.

    Does not prove anchor durability or that the old parent was itself committed.
    """
    if not issuer:
        raise Rejected("missing checkpoint issuer")
    verify_transition(previous, change, transition_authority)
    after = resulting_state(previous, change)
    anchor.checkpoint(after)
    receipt = CheckpointReceipt(
        issuer=issuer, namespace=previous.namespace,
        compartment=previous.compartment,
        parent_epoch=previous.epoch, parent_commitment=previous.commitment,
        child_epoch=after.epoch, child_commitment=after.commitment,
        child_policy_digest=after.policy.digest(), signature=b"",
    )
    return replace(receipt, signature=checkpoint_signer.sign(receipt.message()))


def verify_receipt(receipt: CheckpointReceipt, public_key: Ed25519PublicKey) -> None:
    if not receipt.issuer or not receipt.namespace or not receipt.compartment:
        raise Rejected("empty receipt identity")
    if receipt.parent_epoch < 0 or receipt.child_epoch != receipt.parent_epoch + 1:
        raise Rejected("invalid receipt epoch")
    try:
        public_key.verify(receipt.signature, receipt.message())
    except (InvalidSignature, TypeError, ValueError) as exc:
        raise Rejected("invalid checkpoint receipt signature") from exc


def prove_conflicting_receipts(
    left: CheckpointReceipt, right: CheckpointReceipt,
    checkpoint_public_key: Ed25519PublicKey,
) -> tuple[CheckpointReceipt, CheckpointReceipt]:
    """Return portable pair of validated conflicting signed claims.

    No proof of gossip delivery, finality, maliciousness or canonical choice.
    """
    verify_receipt(left, checkpoint_public_key)
    verify_receipt(right, checkpoint_public_key)
    origin = lambda x: (
        x.issuer, x.namespace, x.compartment,
        x.parent_epoch, x.parent_commitment, x.child_epoch,
    )
    if origin(left) != origin(right):
        raise Rejected("not the same signed origin")
    if (left.child_commitment, left.child_policy_digest) == (
        right.child_commitment, right.child_policy_digest
    ):
        raise Rejected("no conflicting child commitments")
    return left, right
