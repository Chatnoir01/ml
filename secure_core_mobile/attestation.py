"""Fail-closed attestation challenge and verification contracts.

This is protocol infrastructure only. It does not validate Android attestation
certificate chains yet and therefore cannot produce hardware-verified success.
"""

from __future__ import annotations
from dataclasses import dataclass
import hashlib
import secrets
from threading import Lock
from time import time


@dataclass(frozen=True)
class AttestationChallenge:
    challenge_id: str
    nonce: str
    issued_at: int
    expires_at: int


class ChallengeStore:
    def __init__(self) -> None:
        self._issued: dict[str, AttestationChallenge] = {}
        self._consumed: set[str] = set()
        self._lock = Lock()

    def issue(self, *, ttl_seconds: int = 120, now: int | None = None) -> AttestationChallenge:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        current = int(time()) if now is None else int(now)
        challenge = AttestationChallenge(
            challenge_id=secrets.token_hex(16),
            nonce=secrets.token_hex(32),
            issued_at=current,
            expires_at=current + ttl_seconds,
        )
        with self._lock:
            self._issued[challenge.challenge_id] = challenge
        return challenge

    def consume(self, challenge_id: str, *, now: int | None = None) -> AttestationChallenge | None:
        current = int(time()) if now is None else int(now)
        with self._lock:
            challenge = self._issued.get(challenge_id)
            if challenge is None or challenge_id in self._consumed:
                return None
            # Expiry is fail-closed and the expired challenge is burned.
            if current > challenge.expires_at:
                self._consumed.add(challenge_id)
                return None
            self._consumed.add(challenge_id)
            return challenge


@dataclass(frozen=True)
class AttestationEvidence:
    challenge_id: str
    challenge_nonce_sha256: str
    key_handle: str
    certificate_chain_der: tuple[bytes, ...]


@dataclass(frozen=True)
class AttestationVerdict:
    verified: bool
    reason: str


class AttestationVerifier:
    """Baseline verifier. Hardware trust-chain verification is intentionally absent."""

    def verify(
        self,
        *,
        evidence: AttestationEvidence,
        challenge: AttestationChallenge,
        expected_key_handle: str,
    ) -> AttestationVerdict:
        if evidence.challenge_id != challenge.challenge_id:
            return AttestationVerdict(False, "challenge-id-mismatch")
        expected_nonce = hashlib.sha256(challenge.nonce.encode()).hexdigest()
        if evidence.challenge_nonce_sha256 != expected_nonce:
            return AttestationVerdict(False, "challenge-nonce-mismatch")
        if evidence.key_handle != expected_key_handle:
            return AttestationVerdict(False, "key-handle-mismatch")
        if not evidence.certificate_chain_der:
            return AttestationVerdict(False, "certificate-chain-missing")
        return AttestationVerdict(
            False,
            "hardware-trust-chain-verification-not-implemented",
        )
