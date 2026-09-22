"""Evidence gate preventing development harness results from overstating claims."""

from __future__ import annotations
import hashlib
import json

from .claims import ClaimLevel, ClaimRegistry, EvidenceRef


def _verify_receipt_sha(receipt: dict) -> str:
    sha = str(receipt.get("sha256", ""))
    try:
        if len(sha) != 64 or len(bytes.fromhex(sha)) != 32:
            raise ValueError
    except ValueError as exc:
        raise ValueError("invalid experiment receipt sha256") from exc
    body = {k: v for k, v in receipt.items() if k != "sha256"}
    canonical = json.dumps(body, sort_keys=True, separators=(",", ":")).encode()
    actual = hashlib.sha256(canonical).hexdigest()
    if actual != sha:
        raise ValueError("experiment receipt digest mismatch")
    return sha


def promote_from_experiment(
    registry: ClaimRegistry,
    claim_id: str,
    *,
    target: ClaimLevel,
    experiment_receipt: dict,
) -> None:
    sha = _verify_receipt_sha(experiment_receipt)

    if target >= ClaimLevel.ADVERSARIALLY_TESTED:
        qualifies = (
            experiment_receipt.get("qualifies_as_hostile_host_evidence") is True
            or (
                experiment_receipt.get("scope") == "hostile-host-isolated-boundary"
                and experiment_receipt.get("qualifies_as_pkvm_evidence") is True
            )
        )
        if not qualifies:
            raise ValueError("development-host evidence cannot authorize adversarial claim promotion")
        if experiment_receipt.get("campaign_passed") is False:
            raise ValueError("failed hostile-host campaign cannot promote claim")
        kind = "hostile-host-test"
    elif target is ClaimLevel.TESTED:
        # The central hostile-host claim SCM-I10 may never be promoted from a
        # generic development receipt.
        if claim_id == "SCM-I10":
            raise ValueError("SCM-I10 requires adversarial isolated-boundary evidence")
        kind = "test"
    elif target is ClaimLevel.IMPLEMENTED:
        kind = "implementation"
    else:
        raise ValueError("experiment receipt cannot authorize external validation")

    registry.promote(
        claim_id,
        target=target,
        evidence=(EvidenceRef(f"experiment:{sha[:16]}", kind, sha),),
    )
