"""Single-use attestation service; challenge freshness precedes verification."""

from __future__ import annotations
from dataclasses import dataclass

from .attestation import (
    AttestationEvidence,
    AttestationVerifier,
    AttestationVerdict,
    ChallengeStore,
)


@dataclass
class AttestationService:
    challenges: ChallengeStore
    verifier: AttestationVerifier

    def verify_once(
        self,
        *,
        evidence: AttestationEvidence,
        expected_key_handle: str,
        now: int | None = None,
    ) -> AttestationVerdict:
        challenge = self.challenges.consume(evidence.challenge_id, now=now)
        if challenge is None:
            return AttestationVerdict(False, "unknown-expired-or-replayed-challenge")
        return self.verifier.verify(
            evidence=evidence,
            challenge=challenge,
            expected_key_handle=expected_key_handle,
        )
