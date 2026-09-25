"""Evidence gate preventing development harness results from overstating claims."""

from __future__ import annotations

import hashlib
import json

from .claims import ClaimLevel, ClaimRegistry, EvidenceRef


_HOSTILE_EVIDENCE_TOKEN_KEY = object()


class VerifiedHostileHostEvidence:
    """Capability token reserved for a future real hostile-host verifier.

    A self-authored JSON receipt, even with a correct digest and qualifying
    booleans, can never construct this token. No production issuer exists yet.
    """

    __slots__ = (
        "receipt_sha256",
        "boundary_evidence_sha256",
        "campaign_spec_sha256",
        "campaign_results_sha256",
        "provenance",
    )

    def __init__(
        self,
        *,
        _key: object,
        receipt_sha256: str,
        boundary_evidence_sha256: str,
        campaign_spec_sha256: str,
        campaign_results_sha256: str,
        provenance: str,
    ) -> None:
        if _key is not _HOSTILE_EVIDENCE_TOKEN_KEY:
            raise TypeError("hostile-host evidence is verifier-issued only")
        for label, value in (
            ("receipt", receipt_sha256),
            ("boundary evidence", boundary_evidence_sha256),
            ("campaign spec", campaign_spec_sha256),
            ("campaign results", campaign_results_sha256),
        ):
            _require_sha256(value, label=label)
        if not provenance:
            raise ValueError("hostile-host evidence provenance required")

        self.receipt_sha256 = receipt_sha256
        self.boundary_evidence_sha256 = boundary_evidence_sha256
        self.campaign_spec_sha256 = campaign_spec_sha256
        self.campaign_results_sha256 = campaign_results_sha256
        self.provenance = provenance


def _require_sha256(value: str, *, label: str) -> None:
    try:
        if len(value) != 64 or len(bytes.fromhex(value)) != 32:
            raise ValueError
    except ValueError as exc:
        raise ValueError(f"invalid {label} sha256") from exc


def _verify_receipt_sha(receipt: dict) -> str:
    sha = str(receipt.get("sha256", ""))
    _require_sha256(sha, label="experiment receipt")
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
    verified_hostile_evidence: VerifiedHostileHostEvidence | None = None,
) -> None:
    sha = _verify_receipt_sha(experiment_receipt)

    if target >= ClaimLevel.ADVERSARIALLY_TESTED:
        # Qualifying booleans inside caller-created JSON are intentionally not
        # authority. A future real runtime/device verifier must issue the token.
        if not isinstance(
            verified_hostile_evidence,
            VerifiedHostileHostEvidence,
        ):
            raise ValueError(
                "verifier-issued hostile-host evidence required for adversarial promotion"
            )
        if verified_hostile_evidence.receipt_sha256 != sha:
            raise ValueError("hostile-host token does not bind experiment receipt")
        if experiment_receipt.get("scope") != "hostile-host-isolated-boundary":
            raise ValueError("hostile-host isolated-boundary scope required")
        if experiment_receipt.get("campaign_passed") is not True:
            raise ValueError("passing hostile-host campaign required")
        manifest_sha = str(experiment_receipt.get("boundary_evidence_sha256", ""))
        if manifest_sha != verified_hostile_evidence.boundary_evidence_sha256:
            raise ValueError("hostile-host boundary evidence binding mismatch")
        spec_sha = str(experiment_receipt.get("campaign_spec_sha256", ""))
        if spec_sha != verified_hostile_evidence.campaign_spec_sha256:
            raise ValueError("hostile-host campaign spec binding mismatch")
        results_sha = str(experiment_receipt.get("campaign_results_sha256", ""))
        if results_sha != verified_hostile_evidence.campaign_results_sha256:
            raise ValueError("hostile-host campaign results binding mismatch")
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
