"""Machine-readable security claim registry with fail-closed promotion."""

from __future__ import annotations
from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Iterable


class ClaimLevel(IntEnum):
    CLAIMED = 0
    IMPLEMENTED = 1
    TESTED = 2
    ADVERSARIALLY_TESTED = 3
    EXTERNALLY_VALIDATED = 4


@dataclass(frozen=True)
class EvidenceRef:
    evidence_id: str
    kind: str
    artifact_sha256: str


@dataclass(frozen=True)
class SecurityClaim:
    claim_id: str
    statement: str
    level: ClaimLevel = ClaimLevel.CLAIMED
    evidence: tuple[EvidenceRef, ...] = ()


class ClaimRegistry:
    def __init__(self, claims: Iterable[SecurityClaim]):
        items = tuple(claims)
        self._claims = {claim.claim_id: claim for claim in items}
        if len(self._claims) != len(items):
            raise ValueError("duplicate claim id")

    def get(self, claim_id: str) -> SecurityClaim:
        try:
            return self._claims[claim_id]
        except KeyError as exc:
            raise ValueError("unknown claim id") from exc

    def promote(
        self,
        claim_id: str,
        *,
        target: ClaimLevel,
        evidence: tuple[EvidenceRef, ...],
    ) -> SecurityClaim:
        current = self.get(claim_id)
        if target != ClaimLevel(current.level + 1):
            raise ValueError("claim promotion must advance exactly one level")
        if not evidence:
            raise ValueError("claim promotion requires evidence")
        for item in evidence:
            if not item.evidence_id or not item.kind or len(item.artifact_sha256) != 64:
                raise ValueError("malformed claim evidence")
        required_kind = {
            ClaimLevel.IMPLEMENTED: "implementation",
            ClaimLevel.TESTED: "test",
            ClaimLevel.ADVERSARIALLY_TESTED: "hostile-host-test",
            ClaimLevel.EXTERNALLY_VALIDATED: "external-validation",
        }[target]
        if not any(item.kind == required_kind for item in evidence):
            raise ValueError(f"promotion to {target.name} requires {required_kind} evidence")
        updated = replace(
            current,
            level=target,
            evidence=current.evidence + tuple(evidence),
        )
        self._claims[claim_id] = updated
        return updated


def baseline_claims() -> tuple[SecurityClaim, ...]:
    return (
        SecurityClaim("SCM-I1", "Unknown security-relevant state is denied by default."),
        SecurityClaim("SCM-I2", "Application authorization uses opaque key handles."),
        SecurityClaim("SCM-I3", "Policy/state authorization precedes provider operation."),
        SecurityClaim("SCM-I4", "Authorization evidence binds the exact protected request."),
        SecurityClaim("SCM-I5", "Consumed, stale, or replayed freshness evidence is rejected."),
        SecurityClaim("SCM-I6", "Security-relevant rollback is prevented or detected."),
        SecurityClaim("SCM-I7", "Software fallback cannot satisfy hardware-backed requirements."),
        SecurityClaim("SCM-I8", "Integrity receipts exclude secret key material."),
        SecurityClaim("SCM-I9", "Implementation status cannot silently promote security claims."),
        SecurityClaim("SCM-I10", "Central hostile-host resistance requires hostile-host evidence."),
    )
