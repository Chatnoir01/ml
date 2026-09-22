"""Evidence gate preventing development harness results from overstating claims."""

from __future__ import annotations

from .claims import ClaimLevel, ClaimRegistry, EvidenceRef


def promote_from_experiment(
    registry: ClaimRegistry,
    claim_id: str,
    *,
    target: ClaimLevel,
    experiment_receipt: dict,
) -> None:
    sha = str(experiment_receipt.get("sha256", ""))
    scope = experiment_receipt.get("scope")
    pkvm = experiment_receipt.get("qualifies_as_pkvm_evidence") is True

    if target >= ClaimLevel.ADVERSARIALLY_TESTED:
        if scope != "hostile-host-isolated-boundary" or not pkvm:
            raise ValueError("development-host evidence cannot authorize adversarial claim promotion")
        kind = "hostile-host-test"
    elif target is ClaimLevel.TESTED:
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
